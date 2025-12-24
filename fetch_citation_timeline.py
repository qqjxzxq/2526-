# fetch_citation_timeline.py — Real-time wide CSV building (Fixed Year Range)
import os
import time
import json
import csv
import re
import requests
import pandas as pd
from tqdm import tqdm

INPUT_FILE = "output_cleaned/vispub_final.csv"

# 输出路径
OUTPUT_DIR = "citation_timeline"
RAW_JSONL = os.path.join(OUTPUT_DIR, "citation_timeline_raw.jsonl")
FAILED_FILE = os.path.join(OUTPUT_DIR, "failed_records.csv")
WIDE_CSV = os.path.join(OUTPUT_DIR, "citation_timeline_wide.csv")

# 固定年份范围
YEAR_MIN = 1986
YEAR_MAX = 2025
YEAR_RANGE = list(range(YEAR_MIN, YEAR_MAX + 1))

SLEEP_BETWEEN_REQUESTS = 0.25
MAX_RETRIES = 3
TIMEOUT = 12
HEADERS = {"User-Agent": "YourName/1.0 (mailto:xzxq1027@gmail.com)"}

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------- load cleaned data ----------
df = pd.read_csv(INPUT_FILE)
# 倒序扫描，先扫描旧年份的引用记录
df = df.iloc[::-1].reset_index(drop=True)

if "oa_openalex_id" not in df.columns:
    raise KeyError("CSV 中找不到列 oa_openalex_id")
if "year" not in df.columns:
    raise KeyError("CSV 缺少出版年份列 'year'")

# normalize wid
def normalize_to_wid(raw):
    if pd.isna(raw):
        return None
    m = re.search(r"W\d+", str(raw))
    return m.group(0) if m else None

df["oa_wid"] = df["oa_openalex_id"].apply(normalize_to_wid)
all_wids = list(df["oa_wid"].dropna().unique())

print(f"📌 Total works = {len(all_wids)}")

# ID -> Pub Year 映射
pub_year_map = {
    row["oa_wid"]: int(row["year"]) if not pd.isna(row["year"]) else None
    for idx, row in df.iterrows()
}

# ---------- Load existing wide CSV ----------
if os.path.exists(WIDE_CSV):
    wide_df = pd.read_csv(WIDE_CSV)
    existing_ids = set(wide_df["openalex_id"])
else:
    # 创建初始宽表
    columns = ["openalex_id"] + [str(y) for y in YEAR_RANGE]
    wide_df = pd.DataFrame(columns=columns)
    existing_ids = set()

print(f"🔄 Already completed = {len(existing_ids)}")

# ---------- Load failed list ----------
failed_ids = set()
if os.path.exists(FAILED_FILE):
    fdf = pd.read_csv(FAILED_FILE)
    failed_ids = set(fdf["openalex_id"])
print(f"⚠ historical failed = {len(failed_ids)}")


# ---------- Save wide CSV ----------
def save_wide(df):
    df.sort_values("openalex_id", inplace=True)
    df.to_csv(WIDE_CSV, index=False)


# ---------- Retry fetch ----------
def fetch_with_retries(url):
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            if r.status_code == 200:
                return ("ok", r.json())
            last_err = ("http_error", r.status_code)
            if r.status_code == 429:
                time.sleep(10)
        except Exception as e:
            last_err = ("network_error", str(e))
        time.sleep(1.5 * (attempt + 1))
    return ("fail", last_err)


# ---------- Parse JSON timeline ----------
def parse_timeline(obj, wid, pub_year):
    rows = {}

    # counts_by_year
    if isinstance(obj, dict) and "counts_by_year" in obj:
        for g in obj["counts_by_year"]:
            year = g.get("year")
            cnt = g.get("cited_by_count") or g.get("count") or 0
            try:
                year = int(year)
                cnt = int(cnt)
            except:
                continue

            # ★ 忽略早于出版年份的引用
            if pub_year and year < pub_year:
                continue

            # ★ 忽略超出 1986–2025 范围
            if year < YEAR_MIN or year > YEAR_MAX:
                continue

            rows[year] = cnt

    # group_by
    elif isinstance(obj, dict) and "group_by" in obj:
        for g in obj["group_by"]:
            year = g.get("key") or g.get("year")
            cnt = g.get("cited_by_count") or g.get("count") or 0
            try:
                year = int(year)
                cnt = int(cnt)
            except:
                continue

            if pub_year and year < pub_year:
                continue
            if year < YEAR_MIN or year > YEAR_MAX:
                continue

            rows[year] = cnt

    # 返回 dict: {year: cnt}
    return rows


# ---------- Main loop ----------
for wid in tqdm(all_wids):

    if wid in existing_ids:
        continue
    if wid in failed_ids:
        continue

    pub_year = pub_year_map.get(wid, None)

    endpoints = [
        f"https://api.openalex.org/works/{wid}/citations?group_by=year",
        f"https://api.openalex.org/works/{wid}/citation-timeline",
        f"https://api.openalex.org/works/{wid}"
    ]

    payload = None
    reason = None

    for url in endpoints:
        status, res = fetch_with_retries(url)
        if status == "ok":
            payload = res
            break
        else:
            reason = res

    if payload is None:
        with open(FAILED_FILE, "a", newline='', encoding="utf-8") as f:
            csv.writer(f).writerow([wid, str(reason)])
        failed_ids.add(wid)
        print(f"❌ Failed {wid}, reason={reason}")
        continue

    # save raw
    with open(RAW_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

    # parse timeline
    rows = parse_timeline(payload, wid, pub_year)

    # build row
    row = {"openalex_id": wid}
    for y in YEAR_RANGE:
        row[str(y)] = rows.get(y, 0)

    # append
    wide_df = pd.concat([wide_df, pd.DataFrame([row])], ignore_index=True)
    existing_ids.add(wid)

    save_wide(wide_df)

    print(f"✔ {wid}: years={len(rows)}, total={sum(rows.values())}")

    time.sleep(SLEEP_BETWEEN_REQUESTS)

print("\n🎉 Finished.")
print(f"👉 Wide CSV: {WIDE_CSV}")
print(f"👉 Raw JSON: {RAW_JSONL}")
print(f"👉 Failed:   {FAILED_FILE}")

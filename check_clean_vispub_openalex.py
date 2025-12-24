# check_clean_vispub_openalex.py
import os
import json
import ast
import re
import pandas as pd
from difflib import SequenceMatcher

# ---------- 配置 ----------
VISPUB_CSV = "vispubs.csv"
OA_CSV = "vispub_with_openalex.csv"
OUTPUT_DIR = "output_cleaned"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- 读取 CSV ----------
vispub = pd.read_csv(VISPUB_CSV)
oa = pd.read_csv(OA_CSV)

# ---------- 给 OpenAlex 所有列加前缀 ----------
oa = oa.add_prefix("oa_")
df = pd.concat([vispub.reset_index(drop=True), oa.reset_index(drop=True)], axis=1)

# ---------- 辅助函数 ----------
def compute_similarity(a, b):
    try:
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()
    except:
        return 0.0

def valid_doi(x):
    if pd.isna(x):
        return False
    s = str(x).strip()
    if s.startswith("http://") or s.startswith("https://"):
        return "doi.org" in s
    return bool(re.match(r'^10\.\d{2,9}\/\S+', s))

def valid_openalex_id(x):
    """
    OpenAlex ID 正确格式示例：
        https://openalex.org/W1234567890 或 W1234567890
    """
    if pd.isna(x):
        return False
    x = str(x).strip()
    x = x.replace("https://openalex.org/", "").replace("http://openalex.org/", "")
    return bool(re.match(r'^[A-Z][A-Za-z0-9]{5,15}$', x))

def parse_referenced_works(x):
    if pd.isna(x): return []
    if isinstance(x, list): return x
    if isinstance(x, str):
        x = x.strip()
        if x == "" or x == "[]": return []
        try:
            parsed = ast.literal_eval(x)
            if isinstance(parsed, list): return parsed
        except: pass
        try:
            parsed = json.loads(x)
            if isinstance(parsed, list): return parsed
        except: pass
        return [p.strip() for p in re.split(r'[,\s]+', x) if p.strip()]
    return []

def extract_oa_authors(x):
    if pd.isna(x): return []
    if isinstance(x, list):
        names = []
        for item in x:
            if isinstance(item, dict):
                if "author" in item and isinstance(item["author"], dict):
                    names.append(item["author"].get("display_name", "").strip())
                elif "author_display_name" in item:
                    names.append(item["author_display_name"].strip())
            elif isinstance(item, str):
                names.append(item.strip())
        return [n for n in names if n]
    if isinstance(x, str):
        try:
            parsed = json.loads(x)
            if isinstance(parsed, list):
                return [item.get("author", {}).get("display_name", "") if isinstance(item, dict) else "" for item in parsed]
        except: pass
        parts = re.split(r'[;,\|]+', x)
        return [p.strip() for p in parts if p.strip()]
    return []

def author_overlap(vis_authors_str, oa_authorships_field):
    if pd.isna(vis_authors_str): vis_list = []
    else: vis_list = [p.strip().lower() for p in re.split(r'[;,\|]+', str(vis_authors_str)) if p.strip()]
    oa_list = [p.strip().lower() for p in extract_oa_authors(oa_authorships_field)]
    if not vis_list or not oa_list: return 0.0
    inter = set(vis_list).intersection(set(oa_list))
    union = set(vis_list).union(set(oa_list))
    return len(inter) / len(union)

# ---------- 清洗 OpenAlex ID 和 DOI ----------

# OpenAlex ID 清洗
oa_id_column = None
for c in ["oa_openalex_id", "oa_id"]:
    if c in df.columns:
        oa_id_column = c
        break

def valid_openalex_id(x):
    if pd.isna(x):
        return False
    s = str(x).strip()
    # OpenAlex ID 一般为 https://openalex.org/W123456 或 shortID Wxxxxx
    return s.startswith("https://openalex.org/") or re.match(r"^[WVAR]\d+", s) is not None

if oa_id_column is None:
    print("⚠ 未找到 OpenAlex ID 列（oa_openalex_id / oa_id），跳过 ID 清洗")
    df["oa_id_valid"] = False
    openalex_invalid_count = len(df)
else:
    df["oa_id_valid"] = df[oa_id_column].apply(valid_openalex_id)
    df.loc[~df["oa_id_valid"], oa_id_column] = ""  # 清洗掉无效值
    openalex_invalid_count = int((~df["oa_id_valid"]).sum())

# DOI 清洗 —— OpenAlex 和 VisPub 二者都检查
df["oa_doi_valid"] = df["oa_doi"].apply(valid_doi)
df.loc[~df["oa_doi_valid"], "oa_doi"] = ""

df["doi_valid"] = df["oa_doi"].apply(valid_doi) | df["doi"].apply(valid_doi)
doi_invalid_after_clean = int((~df["doi_valid"]).sum())


# ---------- 继续之前的逻辑 ----------
df["title_similarity"] = df.apply(lambda r: compute_similarity(r.get("title", ""), r.get("oa_title", "")), axis=1)
df["oa_referenced_works_parsed"] = df["oa_referenced_works"].apply(parse_referenced_works) if "oa_referenced_works" in df else [[]]*len(df)
df["ref_count"] = df["oa_referenced_works_parsed"].apply(len)

df["year_consistent"] = df.apply(
    lambda r: abs(int(r["year"]) - int(r["oa_publication_year"])) <= 1 
        if not (pd.isna(r["year"]) or pd.isna(r["oa_publication_year"])) else False, axis=1)

df["author_overlap"] = df.apply(lambda r: author_overlap(r.get("authorNamesDeduped", ""), r.get("oa_authorships", "")), axis=1)

df["valid_score"] = (
    (df["title_similarity"] > 0.75).astype(int) +
    ((df["doi_valid"]) | (df["ref_count"] > 0)).astype(int) +
    ((df["year_consistent"]) | (df["author_overlap"] > 0.4)).astype(int)
)
df["valid_record"] = df["valid_score"] >= 2

# ---------- 输出摘要 ----------
print("\n===== 数据检查结果 =====")
print("总论文数:", len(df))
print("有效记录:", int(df["valid_record"].sum()))
print("无引用记录:", int((df["ref_count"] == 0).sum()))
print("疑似标题匹配错误 (sim <= 0.75):", int((df["title_similarity"] <= 0.75).sum()))
print("OpenAlex ID 无效或缺失:", openalex_invalid_count)
print("DOI 无效或缺失:", doi_invalid_after_clean)
print("年份不一致:", int((~df["year_consistent"]).sum()))
print("作者重合度低 (<=0.4):", int((df["author_overlap"] <= 0.4).sum()))

# ---------- 保存 ----------
df.to_csv(os.path.join(OUTPUT_DIR, "vispub_cleaned.csv"), index=False)
df[df["valid_record"] == False].to_csv(os.path.join(OUTPUT_DIR, "vispub_errors.csv"), index=False)
df[df["valid_record"] == True].to_csv(os.path.join(OUTPUT_DIR, "vispub_valid_only.csv"), index=False)

print(f" 已生成文件：{OUTPUT_DIR}/vispub_cleaned.csv, vispub_errors.csv, vispub_valid_only.csv")
print("Done.")

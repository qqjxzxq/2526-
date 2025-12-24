import requests
import pandas as pd
import urllib.parse
import time
import json
import os

# -----------------------------
# 搜索函数（与你原来的基本一致）
# -----------------------------
def search_openalex_by_title(title):
    query = urllib.parse.quote(title)
    url = f"https://api.openalex.org/works?filter=title.search:{query}"

    try:
        r = requests.get(url, timeout=10).json()
    except Exception as e:
        print("  ⚠ 网络错误:", e)
        return None

    if "results" in r and len(r["results"]) > 0:
        work = r["results"][0]
        return {
            "title": title,
            "openalex_id": work.get("id"),
            "doi": work.get("doi"),
            "cited_by_count": work.get("cited_by_count"),
            "publication_year": work.get("publication_year"),
            "referenced_works": work.get("referenced_works"),
        }
    return None


# -----------------------------
# 加载进度文件 progress.json
# -----------------------------
progress_file = "progress.json"

if os.path.exists(progress_file):
    with open(progress_file, "r") as f:
        progress = json.load(f)
else:
    progress = {"index": 0}  # 默认从 0 开始

# -----------------------------
# 读取 CSV 输入文件
# -----------------------------
df = pd.read_csv("vispubs.csv")
total = len(df)

# -----------------------------
# 输出文件（自动追加模式）
# -----------------------------
output_file = "vispub_with_openalex.csv"

# 如果文件不存在 → 创建并写入表头
if not os.path.exists(output_file):
    out_df = pd.DataFrame(columns=[
        "title", "openalex_id", "doi", "cited_by_count",
        "publication_year", "referenced_works"
    ])
    out_df.to_csv(output_file, index=False)


print(f"从进度 {progress['index']}/{total} 继续爬取...\n")


# -----------------------------
# 主循环（支持断点续传）
# -----------------------------
for i in range(progress["index"], total):

    title = df.loc[i, "title"]
    print(f"[{i+1}/{total}] Searching OpenAlex: {title}")

    data = search_openalex_by_title(title)

    if data is None:
        print("  ❌ Not found")
        data = {
            "title": title,
            "openalex_id": None,
            "doi": None,
            "cited_by_count": None,
            "publication_year": None,
            "referenced_works": None
        }
    else:
        print(f"  ✔ Found: {data['openalex_id']}, DOI={data['doi']}")

    # 每条数据立即写入 CSV（避免中断丢数据）
    pd.DataFrame([data]).to_csv(output_file, mode="a", header=False, index=False)

    # 保存进度
    progress["index"] = i + 1
    with open(progress_file, "w") as f:
        json.dump(progress, f)

    # 限速
    time.sleep(0.5)

print("\n全部完成！数据已写入 vispub_with_openalex.csv")

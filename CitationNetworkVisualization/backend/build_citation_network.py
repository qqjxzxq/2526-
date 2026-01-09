# build_citation_network.py
import pandas as pd
import ast
import re
import os

INPUT_FILE = "../../output_cleaned/vispub_final.csv"
OUTPUT_DIR = "citation_network"

EDGE_FILE = os.path.join(OUTPUT_DIR, "citation_edges.csv")
NODE_FILE = os.path.join(OUTPUT_DIR, "citation_nodes.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------- helpers ----------
def normalize_wid(x):
    if pd.isna(x):
        return None
    m = re.search(r"W\d+", str(x))
    return m.group(0) if m else None


def parse_refs(x):
    if pd.isna(x):
        return []
    try:
        return [normalize_wid(r) for r in ast.literal_eval(x)]
    except:
        return []


# ---------- load data ----------
df = pd.read_csv(INPUT_FILE)

required_cols = [
    "oa_openalex_id",
    "year",
    "oa_referenced_works_parsed"
]
for c in required_cols:
    if c not in df.columns:
        raise KeyError(f"Missing column: {c}")

df["wid"] = df["oa_openalex_id"].apply(normalize_wid)
df["pub_year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["refs"] = df["oa_referenced_works_parsed"].apply(parse_refs)

df = df.dropna(subset=["wid"])


# ---------- build edges ----------
edges = []

for _, row in df.iterrows():
    src = row["wid"]
    src_year = row["pub_year"]

    if not row["refs"]:
        continue

    for tgt in row["refs"]:
        if tgt:
            edges.append({
                "source": src,
                "target": tgt,
                "source_year": src_year
            })

edges_df = pd.DataFrame(edges)

edges_df.to_csv(EDGE_FILE, index=False)
print(f"✅ Edge list saved: {EDGE_FILE}  ({len(edges_df)} edges)")


# ---------- build nodes ----------
# 可选：结合你之前算的 citation timeline
timeline_file = "../../citation_timeline/citation_timeline_wide.csv"

if os.path.exists(timeline_file):
    wide = pd.read_csv(timeline_file)
    year_cols = [c for c in wide.columns if c.isdigit()]
    wide["total_citations"] = wide[year_cols].sum(axis=1)
    citation_map = dict(
        zip(wide["openalex_id"], wide["total_citations"])
    )
else:
    citation_map = {}

nodes = []
for _, row in df.iterrows():
    wid = row["wid"]
    nodes.append({
        "id": wid,
        "year": row["pub_year"],
        "total_citations": citation_map.get(wid, 0)
    })

nodes_df = pd.DataFrame(nodes).drop_duplicates("id")
nodes_df.to_csv(NODE_FILE, index=False)

print(f"✅ Node list saved: {NODE_FILE}  ({len(nodes_df)} nodes)")

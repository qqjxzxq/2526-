import pandas as pd
import os

# =========================
# 输入文件
# =========================
EDGES_FILE = "citation_network/citation_edges.csv"
NODES_FILE = "citation_network/nodes_with_citations.csv"

# =========================
# 输出目录
# =========================
OUTPUT_DIR = "yearly_networks"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# 读取数据
# =========================
edges = pd.read_csv(EDGES_FILE)
nodes = pd.read_csv(NODES_FILE)

# 基本校验（防止悄悄出错）
required_edge_cols = {"source", "target", "source_year"}
required_node_cols = {"id"}

if not required_edge_cols.issubset(edges.columns):
    raise ValueError(f"edges 缺少必要列: {required_edge_cols - set(edges.columns)}")

if not required_node_cols.issubset(nodes.columns):
    raise ValueError(f"nodes 缺少必要列: {required_node_cols - set(nodes.columns)}")

# =========================
# 按年拆分
# =========================
years = sorted(edges["source_year"].dropna().unique())

print(f"📆 共检测到 {len(years)} 个年份: {years[0]} → {years[-1]}")

for year in years:
    year = int(year)

    # ---- 年内边 ----
    edges_year = edges[edges["source_year"] == year]

    if edges_year.empty:
        continue

    # ---- 年内节点：只保留在该年出现过的论文 ----
    node_ids = set(edges_year["source"]) | set(edges_year["target"])
    nodes_year = nodes[nodes["id"].isin(node_ids)]

    # ---- 输出 ----
    edge_out = os.path.join(OUTPUT_DIR, f"edges_{year}.csv")
    node_out = os.path.join(OUTPUT_DIR, f"nodes_{year}.csv")

    edges_year.to_csv(edge_out, index=False)
    nodes_year.to_csv(node_out, index=False)

    print(
        f"✔ {year}: "
        f"edges={len(edges_year)}, "
        f"nodes={len(nodes_year)}"
    )

print("✅ 所有年度子网络已生成完毕")

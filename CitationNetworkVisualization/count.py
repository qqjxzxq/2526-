import pandas as pd

edges = pd.read_csv("./citation_network/citation_edges.csv")
nodes = pd.read_csv("./citation_network/citation_nodes.csv")

# 如果 nodes 里已经有 total_citations，先删掉
if "total_citations" in nodes.columns:
    nodes = nodes.drop(columns=["total_citations"])

# 统计被引用次数
citation_counts = (
    edges.groupby("target")
         .size()
         .reset_index(name="total_citations")
)

# 合并
nodes = nodes.merge(
    citation_counts,
    how="left",
    left_on="id",
    right_on="target"
)

nodes["total_citations"] = nodes["total_citations"].fillna(0).astype(int)
nodes.drop(columns=["target"], inplace=True)

nodes.to_csv("./citation_network/nodes_with_citations.csv", index=False)

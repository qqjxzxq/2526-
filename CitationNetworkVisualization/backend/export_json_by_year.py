import pandas as pd
import os
import json

YEARLY_DIR = "yearly_networks"
OUTPUT_DIR = "../web/data"


os.makedirs(OUTPUT_DIR, exist_ok=True)

for year in range(1986, 2026):
    nodes_file = f"{YEARLY_DIR}/nodes_{year}.csv"
    edges_file = f"{YEARLY_DIR}/edges_{year}.csv"

    if not os.path.exists(nodes_file) or not os.path.exists(edges_file):
        continue

    nodes = pd.read_csv(nodes_file)
    edges = pd.read_csv(edges_file)

    node_ids = set(nodes["id"])

    # ------ 🔥 补齐缺失节点 ------
    missing = set(edges["source"]).union(set(edges["target"])) - node_ids

    if missing:
        print(f"{year}: repairing {len(missing)} missing nodes")

    for mid in missing:
        nodes = pd.concat([
            nodes,
            pd.DataFrame([{
                "id": mid,
                "year": year,
                "total_citations": 0
            }])
        ], ignore_index=True)

    graph = {
        "nodes": [{"id": r["id"], "citations": int(r["total_citations"])} 
                   for _, r in nodes.iterrows()],
        "links": [{"source": s, "target": t} 
                  for s, t in zip(edges["source"], edges["target"])]
    }

    json.dump(
        graph,
        open(f"{OUTPUT_DIR}/{year}.json", "w"),
        indent=2
    )

import pandas as pd
import networkx as nx
from node2vec import Node2Vec
import numpy as np
import os

# --- 配置 ---
NETWORK_DIR = "./yearly_networks/"  # 你现有的数据目录
OUTPUT_DIR = "tsne_data/high_data/" # 准备生成的目录
START_YEAR = 1990 # (去掉1986、1987吧)
END_YEAR = 2025 # 根据你的实际年份调整

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate():
    for year in range(START_YEAR, END_YEAR + 1):
        i = year - START_YEAR
        node_file = f"{NETWORK_DIR}nodes_{year}.csv"
        edge_file = f"{NETWORK_DIR}edges_{year}.csv"
        
        if not (os.path.exists(node_file) and os.path.exists(edge_file)):
            print(f"跳过 {year}年：文件不存在")
            continue

        print(f"正在处理 {year}年 (high{i}.txt)...")

        # 1. 加载数据
        nodes_df = pd.read_csv(node_file)
        edges_df = pd.read_csv(edge_file)

        # 2. 构建图 (使用 NetworkX)
        G = nx.from_pandas_edgelist(edges_df, source='source', target='target')
        
        # 确保 nodes_df 中的所有节点都在图中，防止 Node2Vec 报错
        G.add_nodes_from(nodes_df['id'].tolist())

        # 3. 运行 Node2Vec 生成特征
        # dimensions=64 是指生成的 high{i}.txt 每行有64列特征
        node2vec = Node2Vec(G, dimensions=64, walk_length=20, num_walks=100, workers=4)
        model = node2vec.fit(window=10, min_count=1, batch_words=4)

        # 4. 关键步骤：按 nodes_{year}.csv 的行顺序提取向量
        # t-SNE 算法依赖于顺序的一致性
        embeddings = []
        for node_id in nodes_df['id']:
            vector = model.wv[str(node_id)]
            embeddings.append(vector)
        
        # 5. 保存为 txt
        np.savetxt(f"{OUTPUT_DIR}high{i}.txt", np.array(embeddings))
        print(f"完成 {year}年，保存为 high{i}.txt")

if __name__ == "__main__":
    
    generate()
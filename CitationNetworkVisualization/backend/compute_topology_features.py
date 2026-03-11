import networkx as nx
import pandas as pd
import os
from sklearn.preprocessing import StandardScaler
from umap import UMAP

# 1. 自动聚合所有年份的边数据
input_dir = './yearly_networks'
all_edges = []

print("正在读取历年边数据...")
for file in os.listdir(input_dir):
    if file.startswith('edges_') and file.endswith('.csv'):
        df = pd.read_csv(os.path.join(input_dir, file))
        all_edges.append(df)

all_edges_df = pd.concat(all_edges).drop_duplicates()

# 2. 构建全局有向图
print("构建全局引用网络...")
G = nx.from_pandas_edgelist(all_edges_df, 'source', 'target', create_using=nx.DiGraph())

# 3. 计算 5 大拓扑特征
print("开始计算拓扑特征（这可能需要一点时间）...")
features = {
    'degree': dict(G.degree()),
    'eigenvector': nx.eigenvector_centrality_numpy(G),
    'betweenness': nx.betweenness_centrality(G, k=1000), # 采样计算以提速
    'clustering': nx.clustering(G.to_undirected()),
    'pagerank': nx.pagerank(G)
}

# 4. 特征标准化与 UMAP 投影
print("执行动态投影降维...")
df_feat = pd.DataFrame(features)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_feat)

# 执行 UMAP 降维得到 X, Y 坐标
reducer = UMAP(
    n_components=2, 
    init='random',           # 直接跳过失败的“谱初始化”，使用随机初始化
    n_jobs=-1,               # 利用所有 CPU 核心并行计算，极大提升速度
    low_memory=True,         # 如果你的论文节点超过几万个，建议开启
    verbose=True             # 开启进度打印，让你知道它运行到哪了，不会觉得卡死
)
embedding = reducer.fit_transform(X_scaled)

df_feat['x_proj'] = embedding[:, 0]
df_feat['y_proj'] = embedding[:, 1]
df_feat['node_id'] = df_feat.index

# 5. 保存结果供后续导出 JSON 使用
output_dir = 'features'
output_path = os.path.join(output_dir, 'node_features_and_projection.csv')
df_feat.to_csv(output_path, index=False)
print(f"✨ 特征工程完成！结果已保存至: {output_path}")
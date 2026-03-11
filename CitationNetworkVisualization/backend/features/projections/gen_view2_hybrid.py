import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from umap import UMAP

HERE = os.path.dirname(__file__)
FEATURE_PATH = os.path.normpath(os.path.join(HERE, '..', 'node_features_and_projection.csv'))
NODES_PATH = os.path.normpath(os.path.join(HERE, '..', '..', 'citation_network', 'nodes_with_citations.csv'))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, 'outputs'))
OUT_PATH = os.path.join(OUTPUT_DIR, 'coords_view2_hybrid.csv')

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    df_feat = pd.read_csv(FEATURE_PATH)
    df_nodes = pd.read_csv(NODES_PATH)

    # --- 强力对齐 ID 列名 ---
    # 检查 df_feat
    if 'id' in df_feat.columns:
        df_feat = df_feat.rename(columns={'id': 'id'})
    elif 'id' not in df_feat.columns:
        # 如果既没有 id 也没有 id，可能是第一列，我们手动命名它
        df_feat = df_feat.rename(columns={df_feat.columns[-1]: 'id'})

    df = pd.merge(df_feat, df_nodes[['id', 'year']], on='id')

    features = ['degree', 'eigenvector', 'betweenness', 'clustering', 'pagerank']

    print("正在生成视图 2：知识演化投影 (Topological + Temporal)...")
    X_topo = StandardScaler().fit_transform(df[features])
    X_year = StandardScaler().fit_transform(df[['year']])

    # 核心逻辑：将年份权重放大（例如乘以 3），让时间成为主导分布的轴
    X_hybrid = np.hstack([X_topo, X_year * 3.0])

    reducer = UMAP(n_components=2, init='random', n_neighbors=30, min_dist=0.3, n_jobs=-1)
    embedding = reducer.fit_transform(X_hybrid)

    df['x_hybrid'] = embedding[:, 0]
    df['y_hybrid'] = embedding[:, 1]

    df[['id', 'x_hybrid', 'y_hybrid']].to_csv(OUT_PATH, index=False)
    print("✨ 视图 2 坐标已生成。 保存到:", OUT_PATH)

if __name__ == '__main__':
    main()

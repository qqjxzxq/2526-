import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from umap import UMAP

HERE = os.path.dirname(__file__)
FEATURE_PATH = os.path.normpath(os.path.join(HERE, '..', 'node_features_and_projection.csv'))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, 'outputs'))
OUT_PATH = os.path.join(OUTPUT_DIR, 'coords_view1_topo.csv')

# ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    df = pd.read_csv(FEATURE_PATH)
    features = ['degree', 'eigenvector', 'betweenness', 'clustering', 'pagerank']

    print("正在生成视图 1：纯拓扑投影...")
    X = StandardScaler().fit_transform(df[features])

    # 加入微小噪声防止重叠点导致初始化失败
    X += np.random.normal(0, 1e-6, X.shape)

    reducer = UMAP(n_components=2, init='random', n_neighbors=15, min_dist=0.1, n_jobs=-1)
    embedding = reducer.fit_transform(X)

    df['x_topo'] = embedding[:, 0]
    df['y_topo'] = embedding[:, 1]

    # 仅保存坐标和 ID 映射
    df[['node_id', 'x_topo', 'y_topo']].to_csv(OUT_PATH, index=False)
    print("✨ 视图 1 坐标已生成。 保存到:", OUT_PATH)

if __name__ == '__main__':
    main()

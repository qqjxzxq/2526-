import pandas as pd
import os
from sklearn.preprocessing import StandardScaler
from umap import UMAP

HERE = os.path.dirname(__file__)
FEATURE_PATH = os.path.normpath(os.path.join(HERE, '..', 'node_features_and_projection.csv'))
OUTPUT_DIR = os.path.normpath(os.path.join(HERE, 'outputs'))
OUT_PATH = os.path.join(OUTPUT_DIR, 'coords_view3_backbone.csv')

os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    df = pd.read_csv(FEATURE_PATH)
    features = ['degree', 'eigenvector', 'betweenness', 'clustering', 'pagerank']

    # 筛选条件：Betweenness 高于全网均值（或设定一个阈值如 top 10%）
    threshold = df['betweenness'].mean()
    core_df = df[df['betweenness'] > threshold].copy()

    print(f"正在生成视图 3：骨架图。剩余节点数: {len(core_df)}")

    X_core = StandardScaler().fit_transform(core_df[features])

    reducer = UMAP(n_components=2, init='random', n_neighbors=10, min_dist=0.05, n_jobs=-1)
    embedding = reducer.fit_transform(X_core)

    core_df['x_backbone'] = embedding[:, 0]
    core_df['y_backbone'] = embedding[:, 1]

    core_df[['id', 'x_backbone', 'y_backbone']].to_csv(OUT_PATH, index=False)
    print("✨ 视图 3 骨架坐标已生成。 保存到:", OUT_PATH)

if __name__ == '__main__':
    main()

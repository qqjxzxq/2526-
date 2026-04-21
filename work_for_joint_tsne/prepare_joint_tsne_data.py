import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler

# --- 路径配置 ---
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_SCRIPT_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, 'CitationNetworkVisualization', 'backend')

FEATURES_CSV = os.path.join(BACKEND_DIR, 'features', 'node_features_and_projection.csv')
YEARLY_NETS_DIR = os.path.join(BACKEND_DIR, 'yearly_networks')

def prepare_data(year_t1, year_t2):
    print(f"🚀 正在准备 {year_t1} 和 {year_t2} 的对齐数据...")
    
    folder_name = f"{year_t1}_{year_t2}"
    output_dir = os.path.join(CURRENT_SCRIPT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(FEATURES_CSV):
        print(f"❌ 错误: 找不到特征文件 {FEATURES_CSV}")
        return
    
    df_all = pd.read_csv(FEATURES_CSV).set_index('node_id')
    
    nodes_t1 = set(pd.read_csv(os.path.join(YEARLY_NETS_DIR, f'nodes_{year_t1}.csv'))['id'])
    nodes_t2 = set(pd.read_csv(os.path.join(YEARLY_NETS_DIR, f'nodes_{year_t2}.csv'))['id'])
    
    union_ids = sorted(list(nodes_t1 | nodes_t2))
    print(f"📊 并集节点数: {len(union_ids)} (T1: {len(nodes_t1)}, T2: {len(nodes_t2)})")
    
    feature_cols = ['degree', 'eigenvector', 'betweenness', 'clustering', 'pagerank']
    
    # --- 调试：打印标准化前的原始特征范围 ---
    print("\n🔍 原始特征统计 (Pre-scaling):")
    print(df_all[feature_cols].describe().loc[['min', 'max', 'mean']])
    
    # 将原始特征取对数（+1 是为了处理 0 值）
    df_all[feature_cols] = np.log1p(df_all[feature_cols])

    # 执行标准化
    scaler = StandardScaler()
    df_all[feature_cols] = scaler.fit_transform(df_all[feature_cols])

    # --- 调试：打印标准化后的特征范围 ---
    print("\n🔍 标准化后特征统计 (Post-scaling):")
    print(df_all[feature_cols].describe().loc[['min', 'max', 'mean']])

    def save_frame(target_nodes, all_ids, filename):
        target_path = os.path.join(output_dir, filename)
        output_data = []
        exist_count = 0
        
        for nid in all_ids:
            if nid in target_nodes and nid in df_all.index:
                feats = df_all.loc[nid, feature_cols].values
                label = 1
                exist_count += 1
            else:
                # 优化：使用 -10 填充缺失节点，使其在空间上与正常节点彻底分离
                # 或者使用很小的随机数。这里尝试使用 -10
                feats = np.full(len(feature_cols), -10.0)
                label = 0
            
            output_data.append(np.append(feats, label))
            
        # 使用 numpy 高效保存
        np.savetxt(target_path, output_data, fmt='%.6f', delimiter='\t')
        print(f"✅ 已生成: {filename} (有效节点: {exist_count}/{len(all_ids)})")

    save_frame(nodes_t1, union_ids, 'f_0.txt')
    save_frame(nodes_t2, union_ids, 'f_1.txt')
    
    print("-" * 30)
    print(f"✨ 准备就绪！请将 {folder_name} 内的文件放入 Joint_tsne/data/ 下")

if __name__ == "__main__":
    prepare_data(2010, 2020)
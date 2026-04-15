import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler

# --- 路径配置 ---
# 脚本位于 /work_for_joint_tsne/
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 根目录
BASE_DIR = os.path.dirname(CURRENT_SCRIPT_DIR)
# Backend 目录
BACKEND_DIR = os.path.join(BASE_DIR,'CitationNetworkVisualization', 'backend')

# 输入路径
FEATURES_CSV = os.path.join(BACKEND_DIR, 'features', 'node_features_and_projection.csv')
YEARLY_NETS_DIR = os.path.join(BACKEND_DIR, 'yearly_networks')

def prepare_data(year_t1, year_t2):
    print(f"🚀 正在准备 {year_t1} 和 {year_t2} 的对齐数据...")
    
    # 1. 创建以年份命名的目标文件夹
    # 路径：/work_for_joint_tsne/2020_2024/
    folder_name = f"{year_t1}_{year_t2}"
    output_dir = os.path.join(CURRENT_SCRIPT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 加载全量特征库
    if not os.path.exists(FEATURES_CSV):
        print(f"❌ 错误: 找不到特征文件 {FEATURES_CSV}")
        return
    
    df_all = pd.read_csv(FEATURES_CSV).set_index('node_id')
    
    # 3. 加载两年的节点 ID 以获取并集
    file_t1 = os.path.join(YEARLY_NETS_DIR, f'nodes_{year_t1}.csv')
    file_t2 = os.path.join(YEARLY_NETS_DIR, f'nodes_{year_t2}.csv')
    
    if not (os.path.exists(file_t1) and os.path.exists(file_t2)):
        print(f"❌ 错误: 找不到指定的年度节点文件 ({year_t1} 或 {year_t2})")
        return
        
    nodes_t1 = pd.read_csv(file_t1)['id'].tolist()
    nodes_t2 = pd.read_csv(file_t2)['id'].tolist()
    
    # 核心：获取两年的所有节点并集并排序，确保矩阵行索引一致
    union_ids = sorted(list(set(nodes_t1) | set(nodes_t2)))
    
    # 4. 特征标准化 (针对 t-SNE 算法必须执行)
    feature_cols = ['degree', 'eigenvector', 'betweenness', 'clustering', 'pagerank']
    scaler = StandardScaler()
    # 仅对特征库中存在的节点进行标准化计算
    df_all[feature_cols] = scaler.fit_transform(df_all[feature_cols])

    def save_frame(target_nodes, all_ids, filename):
        target_path = os.path.join(output_dir, filename)
        output_lines = []
        
        for nid in all_ids:
            # 如果节点在当前年份存在，取其特征，否则填充 0 向量
            if nid in target_nodes and nid in df_all.index:
                feats = df_all.loc[nid, feature_cols].values
                label = 1  # 基础标签
            else:
                feats = np.zeros(len(feature_cols))
                label = 0
            
            # Joint t-SNE 格式：feat1 \t feat2 ... \t label
            line = "\t".join(map(str, feats)) + "\t" + str(label)
            output_lines.append(line)
            
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        print(f"✅ 已生成: {target_path}")

    # 5. 执行保存
    save_frame(nodes_t1, union_ids, 'f_1.txt')
    save_frame(nodes_t2, union_ids, 'f_2.txt')
    
    print("-" * 30)
    print(f"✨ 处理完成！")
    print(f"📁 输出目录: {output_dir}")
    print(f"📊 矩阵对齐行数: {len(union_ids)}")

if __name__ == "__main__":
    # 你可以修改这里来指定想要对比的年份
    prepare_data(2020, 2024)
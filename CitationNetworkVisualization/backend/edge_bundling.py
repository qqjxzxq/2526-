import json
import os
import pandas as pd
import numpy as np
from datashader.bundling import hammer_bundle

# 配置路径
JSON_DIR = '../web/data'

def process_bundling_for_view(nodes_df, links_df, view_suffix):
    """
    针对特定视图计算边绑定路径
    """
    x_col = f'x_{view_suffix}'
    y_col = f'y_{view_suffix}'
    
    # 准备 Hammer Bundle 需要的节点数据
    # 只提取含有当前视图坐标的节点
    nodes_for_hb = nodes_df[[x_col, y_col]].rename(columns={x_col: 'x', y_col: 'y'})
    
    # 执行 Hammer Bundle 算法
    # initial_bandwidth 建议设为布局范围的 1/20 到 1/50
    try:
        hb_paths = hammer_bundle(nodes_for_hb, links_df, initial_bandwidth=0.05, decay=0.7)
        
        # hb_paths 是一个 DataFrame，包含 x, y 坐标，边与边之间用 NaN 分隔
        # 我们需要将其解析回每条边对应的 list
        all_paths = []
        current_path = []
        
        for _, row in hb_paths.iterrows():
            if np.isnan(row['x']):
                if current_path:
                    all_paths.append(current_path)
                    current_path = []
            else:
                current_path.append([round(row['x'], 4), round(row['y'], 4)])
        
        if current_path:
            all_paths.append(current_path)
            
        return all_paths
    except Exception as e:
        print(f"视图 {view_suffix} 计算失败: {e}")
        return None

def run():
    for filename in os.listdir(JSON_DIR):
        if not filename.endswith('.json'): continue
        
        path = os.path.join(JSON_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data['links']: continue

        # 转换为 DataFrame 方便处理
        nodes_df = pd.DataFrame(data['nodes']).set_index('id')
        links_df = pd.DataFrame(data['links'])[['source', 'target']]

        # 视图列表
        views = ['topo', 'hybrid', 'backbone']
        
        for view in views:
            print(f"正在处理 {filename} 的 {view} 视图边绑定...")
            paths = process_bundling_for_view(nodes_df, links_df, view)
            
            if paths and len(paths) == len(data['links']):
                # 将计算好的路径写回对应的 link 对象中
                for i in range(len(data['links'])):
                    data['links'][i][f'path_{view}'] = paths[i]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✅ {filename} 处理完成")

if __name__ == "__main__":
    run()
import json
import pandas as pd
import os

# 路径配置
JSON_DIR = '../web/data'
OUT_DIR = './features/projections/outputs'

def inject():
    print("正在加载坐标映射表...")
    # 读取三个视图的 CSV
    v1 = pd.read_csv(os.path.join(OUT_DIR, 'coords_view1_topo.csv')).set_index('id')
    v2 = pd.read_csv(os.path.join(OUT_DIR, 'coords_view2_hybrid.csv')).set_index('id')
    v3 = pd.read_csv(os.path.join(OUT_DIR, 'coords_view3_backbone.csv')).set_index('id')

    # 遍历 JSON 文件
    for filename in os.listdir(JSON_DIR):
        if filename.endswith('.json'):
            path = os.path.join(JSON_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for node in data['nodes']:
                nid = node['id']
                # 注入视图 1：纯拓扑
                if nid in v1.index:
                    node['x_topo'] = float(v1.loc[nid, 'x_topo'])
                    node['y_topo'] = float(v1.loc[nid, 'y_topo'])
                
                # 注入视图 2：知识演化
                if nid in v2.index:
                    node['x_hybrid'] = float(v2.loc[nid, 'x_hybrid'])
                    node['y_hybrid'] = float(v2.loc[nid, 'y_hybrid'])
                
                # 注入视图 3：骨架标识
                if nid in v3.index:
                    node['x_backbone'] = float(v3.loc[nid, 'x_backbone'])
                    node['y_backbone'] = float(v3.loc[nid, 'y_backbone'])
                    node['is_core'] = True
                else:
                    node['is_core'] = False

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"✅ 已注入数据至: {filename}")

if __name__ == "__main__":
    inject()
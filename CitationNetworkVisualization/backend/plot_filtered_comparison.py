import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datashader.bundling import hammer_bundle
from matplotlib.colors import LinearSegmentedColormap

# --- 调整后的深色系代码 (基于图片，但颜色加深) ---
C_BG = "#FFFFFF"        # 纯白背景
C_T1_NODE = "#1A3678"   # 加深的深靛蓝 (2010年点)
C_T1_EDGE = "#4E5D8F"   # 加深的中蓝紫 (2010年边)
C_T2_NODE = "#2A8A96"   # 加深的湖绿色 (2020年点)
C_T2_EDGE = "#66B191"   # 加深的薄荷绿 (2020年边)
C_TITLE = "#333333"     # 深灰色标题

# 自定义渐变色 (从白到深)
cmap_2010 = LinearSegmentedColormap.from_list("nature_blue", [C_BG, C_T1_EDGE, C_T1_NODE])
cmap_2020 = LinearSegmentedColormap.from_list("nature_cyan", [C_BG, C_T2_EDGE, C_T2_NODE])

# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDS_DIR = os.path.join(BASE_DIR, 'features/projections/joint_output/2020_2024')
EDGES_DIR = os.path.join(BASE_DIR, 'yearly_networks')

def plot_nature_white_style(year_t1, year_t2):
    print(f"🔬 正在应用白底深色系绘图 (Nature 风格升级版)...")
    
    # 1. 加载数据
    n1 = pd.read_csv(os.path.join(EDGES_DIR, f'nodes_{year_t1}.csv'))['id'].tolist()
    n2 = pd.read_csv(os.path.join(EDGES_DIR, f'nodes_{year_t2}.csv'))['id'].tolist()
    union_ids = sorted(list(set(n1) | set(n2)))

    def load_data(year):
        df_c = pd.read_csv(os.path.join(COORDS_DIR, f'coords_{year}.csv'), sep='\s+', header=None, names=['x', 'y', 'label'])
        df_c['node_id'] = union_ids
        df_v = df_c[df_c['label'] == 1.0].set_index('node_id')
        df_e = pd.read_csv(os.path.join(EDGES_DIR, f'edges_{year}.csv'))
        df_e = df_e[df_e['source'].isin(df_v.index) & df_e['target'].isin(df_v.index)]
        return df_v, df_e

    df1_v, df1_e = load_data(year_t1)
    df2_v, df2_e = load_data(year_t2)

    # 2. 绘图配置
    fig, axes = plt.subplots(2, 2, figsize=(20, 18), facecolor=C_BG)
    plt.subplots_adjust(wspace=0.1, hspace=0.15)

    draw_params = [
        (df1_v, df1_e, C_T1_EDGE, C_T1_NODE, cmap_2010, year_t1, 0),
        (df2_v, df2_e, C_T2_EDGE, C_T2_NODE, cmap_2020, year_t2, 1)
    ]

    for df_v, df_e, e_c, n_c, d_cmap, year, col in draw_params:
        ax_top, ax_btm = axes[0, col], axes[1, col]
        for ax in [ax_top, ax_btm]: ax.set_facecolor(C_BG)

        # --- A. 边捆绑 ---
        # 白底连线：alpha 稍微增加到 0.25，lw 改为 0.5，确保能看清流向
        hb_paths = hammer_bundle(df_v[['x', 'y']], df_e, initial_bandwidth=0.05)
        ax_top.plot(hb_paths['x'], hb_paths['y'], color=e_c, lw=0.5, alpha=0.25, zorder=1)

        # --- B. 节点 ---
        # 增加点的对比度，去掉外晕，改用实心深色点
        ax_top.scatter(df_v['x'], df_v['y'], s=4, c=n_c, alpha=0.7, edgecolors='none', zorder=2)
        ax_top.set_title(f"Temporal Structure ({year})", color=C_TITLE, fontsize=22, pad=20, fontweight='bold')

        # --- C. 密度图 ---
        # 使用较高的 thresh (0.05) 让背景更干净
        sns.kdeplot(data=df_v, x='x', y='y', fill=True, cmap=d_cmap, thresh=0.05, alpha=0.9, ax=ax_btm)
        ax_btm.set_title(f"Knowledge Hotspots ({year})", color=C_TITLE, fontsize=22, pad=20)

    # 3. 统一视图
    all_x = pd.concat([df1_v['x'], df2_v['x']])
    all_y = pd.concat([df1_v['y'], df2_v['y']])
    for ax in axes.flatten():
        ax.set_xlim(all_x.min()-5, all_x.max()+5)
        ax.set_ylim(all_y.min()-5, all_y.max()+5)
        ax.set_aspect('equal')
        ax.set_axis_off()

    output_path = f"Nature_White_Bold_{year_t1}_{year_t2}.png"
    plt.savefig(output_path, dpi=300, facecolor=C_BG, bbox_inches='tight')
    print(f"✅ 绘图完成！已生成白底加深版: {output_path}")
    plt.show()

if __name__ == "__main__":
    plot_nature_white_style(2020, 2024)
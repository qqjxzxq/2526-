import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.collections import LineCollection

# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 刚才拷贝过来的坐标
JOINT_COORDS_DIR = os.path.join(BASE_DIR, 'features/projections/joint_output')
# 年度边数据
YEARLY_NETS_DIR = os.path.join(BASE_DIR, 'yearly_networks')

def draw_raw_network(ax, coords_df, edges_df, color_theme, title):
    """绘制原始点线图"""
    # 建立 ID 到坐标的映射
    # 注意：Joint t-SNE 输出没 ID，假设顺序与 edges 里的 node 列表一致
    # 这里的 ID 映射逻辑需要根据你生成 f_1.txt 时的 union_ids 顺序来
    # 暂时我们先画散点和密度，边连线如果 ID 对应不上会乱，我们先重点看分布
    
    ax.scatter(coords_df['x'], coords_df['y'], s=2, c=color_theme, alpha=0.3)
    ax.set_axis_off()
    ax.set_title(title, fontsize=14)

def plot_2x2_comparison(year_t1, year_t2):
    print(f"🎨 正在生成 {year_t1} & {year_t2} 对比图...")
    
    # 加载数据 (sep='\s+' 处理 txt 的空格分隔)
    df_t1 = pd.read_csv(os.path.join(JOINT_COORDS_DIR, f'coords_{year_t1}.csv'), sep='\s+', header=None, names=['x', 'y'])
    df_t2 = pd.read_csv(os.path.join(JOINT_COORDS_DIR, f'coords_{year_t2}.csv'), sep='\s+', header=None, names=['x', 'y'])

    fig, axes = plt.subplots(2, 2, figsize=(18, 15), facecolor='white')
    plt.subplots_adjust(wspace=0.1, hspace=0.1)

    # 1. 上排：原始点分布
    draw_raw_network(axes[0, 0], df_t1, None, '#1f77b4', f"Nodes in {year_t1}")
    draw_raw_network(axes[0, 1], df_t2, None, '#d62728', f"Nodes in {year_t2}")

    # 2. 下排：密度分布
    print("📊 计算 T1 密度...")
    sns.kdeplot(data=df_t1, x='x', y='y', fill=True, cmap="Blues", thresh=0.05, ax=axes[1, 0])
    axes[1, 0].set_axis_off()
    
    print("📊 计算 T2 密度...")
    sns.kdeplot(data=df_t2, x='x', y='y', fill=True, cmap="Reds", thresh=0.05, ax=axes[1, 1])
    axes[1, 1].set_axis_off()

    # 统一坐标轴范围，确保对齐效果
    all_data = pd.concat([df_t1, df_t2])
    x_min, x_max = all_data['x'].min() - 5, all_data['x'].max() + 5
    y_min, y_max = all_data['y'].min() - 5, all_data['y'].max() + 5
    
    for ax in axes.flatten():
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')

    out_file = os.path.join(BASE_DIR, f'Final_Comparison_{year_t1}_{year_t2}.png')
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    print(f"✨ 成功生成对比图：{out_file}")

if __name__ == "__main__":
    plot_2x2_comparison(2020, 2024)
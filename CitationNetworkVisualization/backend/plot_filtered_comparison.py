import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDS_DIR = os.path.join(BASE_DIR, 'features/projections/joint_output/2010_2020')

def plot_filtered_2x2(year_t1, year_t2):
    print(f"🚀 正在绘制过滤后的对比图 ({year_t1} vs {year_t2})...")
    
    # 1. 加载数据 (读取三列：x, y, label)
    # 这里的文件名对应你 cp 过去的名字，如果没有 cp，直接指向 results 目录也可以
    path_t1 = os.path.join(COORDS_DIR, f'coords_{year_t1}.csv')
    path_t2 = os.path.join(COORDS_DIR, f'coords_{year_t2}.csv')
    
    df1 = pd.read_csv(path_t1, sep='\s+', header=None, names=['x', 'y', 'label'])
    df2 = pd.read_csv(path_t2, sep='\s+', header=None, names=['x', 'y', 'label'])

    # 2. 核心步骤：过滤掉那些 label=0 的占位节点
    df1_valid = df1[df1['label'] == 1.0]
    df2_valid = df2[df2['label'] == 1.0]
    
    print(f"   - {year_t1} 有效点数: {len(df1_valid)}")
    print(f"   - {year_t2} 有效点数: {len(df2_valid)}")

    # 3. 创建画布
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), facecolor='white')
    
    # 颜色配置
    color1, cmap1 = '#1f77b4', 'Blues'
    color2, cmap2 = '#d62728', 'Reds'

    # --- 上排：散点分布图 ---
    axes[0, 0].scatter(df1_valid['x'], df1_valid['y'], s=8, c=color1, alpha=0.5)
    axes[0, 0].set_title(f"Nodes in {year_t1} (Filtered)", fontsize=14)
    
    axes[0, 1].scatter(df2_valid['x'], df2_valid['y'], s=8, c=color2, alpha=0.5)
    axes[0, 1].set_title(f"Nodes in {year_t2} (Filtered)", fontsize=14)

    # --- 下排：密度分布图 ---
    sns.kdeplot(data=df1_valid, x='x', y='y', fill=True, cmap=cmap1, thresh=0.05, ax=axes[1, 0])
    axes[1, 0].set_title(f"Knowledge Density {year_t1}", fontsize=14)
    
    sns.kdeplot(data=df2_valid, x='x', y='y', fill=True, cmap=cmap2, thresh=0.05, ax=axes[1, 1])
    axes[1, 1].set_title(f"Knowledge Density {year_t2}", fontsize=14)

    # --- 统一视觉标准 (非常重要) ---
    # 计算所有有效点的共同边界，确保对比具有物理意义
    all_valid_x = pd.concat([df1_valid['x'], df2_valid['x']])
    all_valid_y = pd.concat([df1_valid['y'], df2_valid['y']])
    x_lim = (all_valid_x.min() - 5, all_valid_x.max() + 5)
    y_lim = (all_valid_y.min() - 5, all_valid_y.max() + 5)

    for ax in axes.flatten():
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)
        ax.set_aspect('equal') # 强制 1:1 比例，防止被压扁
        ax.set_axis_off()

    plt.tight_layout()
    file_name = f"Filtered_Joint_TSNE_{year_t1}_{year_t2}.png"
    output_path = os.path.join(BASE_DIR, file_name)
    plt.savefig(output_path, dpi=300)
    print(f"✨ 过滤后的对比图已保存至: {output_path}")
    plt.show()

if __name__ == "__main__":
    plot_filtered_2x2(2010, 2020)
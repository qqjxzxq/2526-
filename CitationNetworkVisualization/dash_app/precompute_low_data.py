import numpy as np
import os
import pandas as pd
from tsne_model import SpatialPyramidTSNE

# 配置
HIGH_DATA_DIR = "./tsne_data/high_data/"
LOW_DATA_DIR = "./tsne_data/low_data/"
START_YEAR = 1990
END_YEAR = 2025  # 对应 i 从 0 到 35

if not os.path.exists(LOW_DATA_DIR):
    os.makedirs(LOW_DATA_DIR, exist_ok=True)

def precompute():
    # 实例化模型
    model = SpatialPyramidTSNE(theta=0.8, cluster_number=7)
    
    for year in range(START_YEAR, END_YEAR + 1):
        i = year - START_YEAR
        high_file = os.path.join(HIGH_DATA_DIR, f"high{i}.txt")
        
        if not os.path.exists(high_file):
            print(f"File {high_file} not found, stopping.")
            break
            
        print(f"Computing Year {year} (high{i}.txt)...")
        
        # 1. 加载高维特征
        X_high = np.loadtxt(high_file)
        
        # 2. 调用模型 step 方法计算 Y
        # 该方法内部会自动处理 prev_X, prev_Y 等所有时序对齐逻辑
        Y_low = model.step(X_high)
        
        # 3. 保存结果供 app.py 直接使用
        output_path = os.path.join(LOW_DATA_DIR, f"low_data_{year}.csv")
        df = pd.DataFrame(Y_low, columns=['x_tsne', 'y_tsne'])
        df.to_csv(output_path, index=False)
        
        print(f"Successfully saved {output_path}")

if __name__ == "__main__":
    precompute()
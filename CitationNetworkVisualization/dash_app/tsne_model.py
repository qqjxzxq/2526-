import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

class SpatialPyramidTSNE:
    def __init__(self, theta=0.8, cluster_number=7):
        self.theta = theta
        self.cluster_number = cluster_number
        # 以下变量对应你源码中的 nodesxy.txt 和 kmeans.txt 的内存副本
        self.prev_X = None  # 上一帧的高维特征 (XI_1)
        self.prev_Y = None  # 上一帧的 t-SNE 坐标 (nodesxy)
        self.prev_kmeans_dim = None  # 上一帧的空间金字塔特征 (kmeans)

    def _km(self, n_cluster, y):
        """对应源码内部定义的 km 函数"""
        kmf = KMeans(n_clusters=n_cluster, n_init="auto")
        kmf.fit(y)
        return kmf.cluster_centers_, kmf.labels_

    def step(self, X_current):
        if X_current.ndim == 1:
            X_current = X_current.reshape(1, -1)
            
        n_samples = X_current.shape[0]
        X = X_current.copy()
        
        # 动态调整 perplexity
        current_perplexity = min(30, max(1, n_samples - 1))

        # --- 修改后的联合逻辑：兼容节点数变化 ---
        if self.prev_Y is not None:
            # 情况 1：点数完全一致（维持原源码逻辑）
            if self.prev_X.shape[0] == n_samples:
                x_move = np.sqrt(np.sum(np.square(self.prev_X - X), axis=1))
                old_min, old_max = x_move.min(), x_move.max()
                if old_max > old_min:
                    x_move = (((x_move - old_min) * (4 - 0.4)) / (old_max - old_min)) + 0.4
                else:
                    x_move = np.full_like(x_move, 0.4)
                
                x_move_weight = self.theta / x_move
                X_combined = np.concatenate((X, self.prev_kmeans_dim * x_move_weight[:, np.newaxis]), axis=1)
                iY = self.prev_Y
            
            # 情况 2：点数不一致（新节点加入）
            else:
                # 对齐前一部分共有的节点特征，剩余部分补零
                min_n = min(self.prev_kmeans_dim.shape[0], n_samples)
                kmeans_padding = np.zeros((n_samples, self.prev_kmeans_dim.shape[1]))
                # 继承前几个点的金字塔特征
                kmeans_padding[:min_n] = self.prev_kmeans_dim[:min_n]
                
                X_combined = np.concatenate((X, kmeans_padding), axis=1)
                
                # 初始化 Y：前一部分继承，新节点随机或 PCA
                # 为了最稳健，点数变动时我们建议使用 "pca" 重新布局
                iY = "pca"
        else:
            X_combined = X
            iY = "pca"

        # --- t-SNE 降维 ---
        tsm = TSNE(n_components=2, perplexity=current_perplexity, n_iter=1500, init=iY)
        Y = tsm.fit_transform(X_combined)

        # --- 计算当前帧的空间金字塔 KMeans (加入兜底防止点数太少) ---
        if n_samples < self.cluster_number:
            current_kmeans_dim = np.zeros((n_samples, self.cluster_number * 2))
        else:
            try:
                center0, label0 = self._km(self.cluster_number, Y)
                dim0 = np.array([np.sqrt(np.sum(np.square(Y - c), axis=1)) for c in center0]).T
                
                dim1 = np.zeros((Y.shape[0], self.cluster_number))
                for pc1 in range(self.cluster_number):
                    idx = np.where(label0 == pc1)[0]
                    if len(idx) > 0:
                        y_sub = Y[idx]
                        k_sub = min(len(idx), self.cluster_number)
                        c_sub, _ = self._km(k_sub, y_sub)
                        d_sub = np.array([np.sqrt(np.sum(np.square(y_sub - c), axis=1)) for c in c_sub]).T
                        dim1[idx, :d_sub.shape[1]] = d_sub

                # 归一化
                mm0 = MinMaxScaler((np.min(X), np.max(X)))
                mm1 = MinMaxScaler((np.min(X), np.max(X) / 2))
                dim0_n = mm0.fit_transform(dim0)
                dim1_n = mm1.fit_transform(dim1)
                
                dim_combined = np.concatenate((dim0_n, dim1_n), axis=1)
                current_kmeans_dim = MinMaxScaler((0, 1)).fit_transform(dim_combined)
            except:
                current_kmeans_dim = np.zeros((n_samples, self.cluster_number * 2))

        # 更新状态
        self.prev_X = X_current
        self.prev_Y = Y
        self.prev_kmeans_dim = current_kmeans_dim

        return Y
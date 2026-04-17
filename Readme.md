# Citation Network Visualization System

## 1. 项目简介

本项目实现了一个面向学术论文的**知识演化可视分析系统**，以可视化领域论文数据为基础，构建引用网络，并通过动态投影方法对知识结构进行多视角可视化分析。

系统主要包括数据采集、数据处理、网络构建、特征提取、降维投影以及前端可视化等模块。

---

## 2. 项目结构

```
CitationNetworkVisualization/
```

### 2.1 数据获取与清洗模块

```
vispubs.csv
vispub_with_openalex.csv
output_cleaned/
```

* `vispubs.csv`：原始爬取的 VisPub 数据
* `vispub_with_openalex.csv`：融合 OpenAlex 数据后的结果
* `output_cleaned/`：

  * `vispub_cleaned.csv`：清洗后的数据
  * `vispub_final.csv`：最终可用数据
  * `vispub_valid_only.csv`：筛选后的高质量数据
  * `vispub_errors.csv`：异常数据记录

相关脚本：

* `fetch_citations.py`：获取引用数据
* `fetch_citation_timeline.py`：获取引用时间线
* `check_clean_vispub_openalex.py`：数据清洗与校验

---

### 2.2 引用网络构建模块

```
backend/citation_network/
```

* `citation_edges.csv`：论文引用关系边
* `nodes_with_citations.csv`：节点及引用统计信息

核心脚本：

* `build_citation_network.py`：构建全局引用网络

---

### 2.3 时间切片网络模块

```
backend/yearly_networks/
```

* `edges_YYYY.csv`：某年引用关系
* `nodes_YYYY.csv`：某年节点数据

脚本：

* `split_by_year.py`：按年份划分网络
* `export_json_by_year.py`：导出前端使用的 JSON 数据

---

### 2.4 特征提取模块

```
backend/features/
```

* `node_features_and_projection.csv`：节点特征及部分投影结果

脚本：

* `compute_topology_features.py`：计算拓扑特征（如度、中心性等）

---

### 2.5 动态投影模块

```
backend/features/projections/
```

实现多视角投影方法：

* `gen_view1_topology.py`：拓扑结构视图
* `gen_view2_hybrid.py`：混合特征视图
* `gen_view3_backbone.py`：骨架结构视图

输出结果：

```
outputs/
```

* `coords_view1_topo.csv`
* `coords_view2_hybrid.csv`
* `coords_view3_backbone.csv`

联合投影（跨时间）：

```
joint_output/
```

* `coords_2020.csv`
* `coords_2024.csv`

---

### 2.6 Joint t-SNE 模块（核心算法）

```
work_for_joint_tsne/
```

用于实现跨时间一致性的动态投影：

* `Joint_tsne/`：核心算法实现
* `thesne/`：t-SNE 与 joint t-SNE 实现
* `graphSim/`：图结构相似度计算（C++实现）
* `prepare_joint_tsne_data.py`：数据预处理

---

### 2.7 可视化模块（前端）

```
backend/web/
```

* `index.html`：主页面
* `main.js`：可视化逻辑（D3.js）
* `style.css`：样式
* `data/`：按年份存储的网络数据（JSON）

功能：

* 动态展示知识网络演化
* 多视图切换
* 节点与引用关系交互

---

### 2.8 辅助分析与可视化脚本

```
backend/
```

* `plot_yearly_network.py`：绘制年度网络
* `plot_comparison_raw_2x2.py`：多视图对比
* `edge_bundling.py`：边捆绑优化
* `count.py`：统计分析

---

## 3. 数据处理流程

整体流程如下：

1. 数据采集（VisPub + OpenAlex）
2. 数据清洗与校验
3. 引用网络构建
4. 时间切片划分
5. 拓扑特征提取
6. 动态投影（多视图）
7. 前端可视化展示

---

## 4. 项目特点

* 多源数据融合（VisPub + OpenAlex）
* 时间切片知识网络建模
* 多视角动态投影方法
* 基于 D3.js 的交互式可视分析
* 支持跨时间一致性的 Joint t-SNE

---

## 5. 运行说明（简要）

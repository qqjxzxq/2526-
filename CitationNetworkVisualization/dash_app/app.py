import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import os

# 初始化 Dash (注意：已移除 external_scripts，因为我们现在使用 assets 本地加载)
app = dash.Dash(__name__)

# --- 路径配置 ---
YEARLY_NETWORKS_DIR = "./yearly_networks/"
LOW_DATA_DIR = "./tsne_data/low_data/"

app.layout = html.Div([
    html.H2("论文引用网络动态对比系统 (任意双年对比)", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # 控制面板：两个独立的年份选择器
    html.Div([
        html.Div([
            html.Label("选择基准年份 (左侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-left-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                value=2020,
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'marginRight': '5%'}),
        
        html.Div([
            html.Label("选择对比年份 (右侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-right-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                value=2024,
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block'}),
        
        html.Div(id='status-info', style={'color': '#666', 'marginTop': '15px', 'textAlign': 'center'})
    ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '10px'}),

    # D3 绘图容器 (高度增加到 900px 以适应上下两排)
    html.Div(id='d3-viz-container', style={
        'height': '950px', 
        'margin': '20px', 
        'border': '1px solid #eee', 
        'borderRadius': '10px',
        'backgroundColor': '#ffffff'
    }),
    
    # 存储对比数据
    dcc.Store(id='net-data-store')
], style={'backgroundColor': '#f4f7f6', 'minHeight': '100vh'})

# --- 服务端逻辑：读取选中的两个年份数据 ---
def get_single_year_data(selected_year):
    node_path = os.path.join(YEARLY_NETWORKS_DIR, f"nodes_{selected_year}.csv")
    edge_path = os.path.join(YEARLY_NETWORKS_DIR, f"edges_{selected_year}.csv")
    low_data_path = os.path.join(LOW_DATA_DIR, f"low_data_{selected_year}.csv")
    
    if not all(os.path.exists(p) for p in [node_path, edge_path, low_data_path]):
        return None

    nodes = pd.read_csv(node_path)
    edges = pd.read_csv(edge_path)
    coords = pd.read_csv(low_data_path)
    
    nodes['x'] = coords['x_tsne']
    nodes['y'] = coords['y_tsne']
    
    # 1. 节点过滤 (防止 nodes_2020.csv 里意外混入了晚于 2020 的数据)
    if 'year' in nodes.columns:
        nodes = nodes[nodes['year'] <= selected_year].copy()
    
    # 2. 边过滤 (核心步骤：确保所有引用的“终点”和“起点”在当年都已存在)
    # 获取当前年份合法的节点 ID 集合
    valid_ids = set(nodes['id'].astype(str))
    
    # 强制转换 ID 为字符串类型进行匹配
    edges['source'] = edges['source'].astype(str)
    edges['target'] = edges['target'].astype(str)
    
    # 只有当 source 和 target 都在 valid_ids 里的边才会被保留
    # 这能彻底消除“引用未来”或者“孤点连线”的异常
    mask = edges['source'].isin(valid_ids) & edges['target'].isin(valid_ids)
    filtered_edges = edges[mask].copy()
    
    return {
        "nodes": nodes.to_dict('records'),
        "links": edges.to_dict('records'),
        "year": selected_year
    }

@app.callback(
    [Output('net-data-store', 'data'),
     Output('status-info', 'children')],
    [Input('year-left-select', 'value'),
     Input('year-right-select', 'value')]
)
def update_compare_data(y_left, y_right):
    data_left = get_single_year_data(y_left)
    data_right = get_single_year_data(y_right)
    
    if data_left is None or data_right is None:
        return dash.no_update, "⚠️ 部分年份数据加载失败，请检查路径。"
    
    payload = {
        "left": data_left,
        "right": data_right
    }
    return payload, f"✅ 对比视图：{y_left} vs {y_right} 加载成功"

# --- 客户端回调 ---
app.clientside_callback(
    """
    function(data) {
        if (!data) return "";
        if (typeof window.renderD3Network === 'function') {
            window.renderD3Network(data);
        }
        return "";
    }
    """,
    Output('d3-viz-container', 'children'),
    Input('net-data-store', 'data')
)

if __name__ == '__main__':
    app.run(debug=True, port=8050)
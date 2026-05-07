import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import os

# 初始化 Dash
app = dash.Dash(__name__)

# --- 路径配置 ---
YEARLY_NETWORKS_DIR = "./yearly_networks/"
LOW_DATA_DIR = "./tsne_data/low_data/"

app.layout = html.Div([
    html.H2("论文引用网络动态对比系统 (任意双年对比)", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # 控制面板
    html.Div([
        html.Div([
            html.Label("选择基准年份 (左侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-left-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                # 去掉 value 默认值，改为使用 placeholder
                placeholder="请选择你要对比的 A 年份", 
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'marginRight': '5%'}),
        
        html.Div([
            html.Label("选择对比年份 (右侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-right-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                # 去掉 value 默认值，改为使用 placeholder
                placeholder="请选择你要对比的 B 年份",
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block'}),
        
        # 初始状态为空白，只有选择后才显示
        html.Div(id='status-info', style={'color': '#666', 'marginTop': '15px', 'textAlign': 'center', 'height': '20px'})
    ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '10px'}),

    # D3 绘图容器
    html.Div(id='d3-viz-container', style={
        'height': '950px', 
        'margin': '20px', 
        'border': '1px solid #eee', 
        'borderRadius': '10px',
        'backgroundColor': '#ffffff'
    }),
    
    dcc.Store(id='net-data-store')
], style={'backgroundColor': '#f4f7f6', 'minHeight': '100vh'})

# --- 服务端逻辑 ---
def get_single_year_data(selected_year):
    if selected_year is None:
        return None
        
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

    # 边过滤逻辑
    valid_ids = set(nodes['id'].astype(str))
    edges['source'] = edges['source'].astype(str)
    edges['target'] = edges['target'].astype(str)
    mask = edges['source'].isin(valid_ids) & edges['target'].isin(valid_ids)
    filtered_edges = edges[mask].copy()
    
    return {
        "nodes": nodes.to_dict('records'),
        "links": filtered_edges.to_dict('records'),
        "year": selected_year
    }

@app.callback(
    [Output('net-data-store', 'data'),
     Output('status-info', 'children')],
    [Input('year-left-select', 'value'),
     Input('year-right-select', 'value')]
)
def update_compare_data(y_left, y_right):
    # 核心判断：如果任何一个年份还没选，就不显示成功字样，也不更新数据
    if y_left is None or y_right is None:
        return dash.no_update, ""
    
    data_left = get_single_year_data(y_left)
    data_right = get_single_year_data(y_right)
    
    if data_left is None or data_right is None:
        return dash.no_update, "⚠️ 选定年份的数据加载失败，请检查 CSV 文件。"
    
    payload = {
        "left": data_left,
        "right": data_right
    }
    # 只有当两个年份都加载成功，才返回这条信息
    return payload, f"✅ 对比视图：{y_left} vs {y_right} 加载成功"

# 客户端 D3 触发
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
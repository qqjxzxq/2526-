import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import os

# 初始化 Dash
app = dash.Dash(
    __name__,
    external_scripts=[
        'https://d3js.org/d3.v7.min.js',
        'https://d3js.org/d3-contour.v4.min.js'
    ]
)


# --- 路径配置 ---
# 确保这些路径与你的目录结构一致
YEARLY_NETWORKS_DIR = "./yearly_networks/"
LOW_DATA_DIR = "./tsne_data/low_data/"

app.layout = html.Div([
    html.H2("论文引用网络动态演化系统", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # 控制面板
    html.Div([
        html.Label("选择演化年份:", style={'fontWeight': 'bold'}),
        dcc.Slider(
            id='year-slider',
            min=1990,
            max=2025,
            step=1,
            value=1990,
            marks={i: str(i) for i in range(1990, 2026, 5)},
            # 使用 drag 模式可以实时平滑滑动，mouseup 模式则释放后才更新
            updatemode='drag' 
        ),
        html.Div(id='status-info', style={'color': '#666', 'marginTop': '10px'})
    ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px'}),

    # D3 绘图容器
    html.Div(id='d3-viz-container', style={
        'height': '800px', 
        'margin': '20px', 
        'border': '1px solid #ccc', 
        'borderRadius': '10px',
        'backgroundColor': '#f9f9f9'
    }),
    
    # 存储网络数据
    dcc.Store(id='net-data-store')
])

# --- 服务端回调：读取预计算数据 ---
@app.callback(
    [Output('net-data-store', 'data'),
     Output('status-info', 'children')],
    Input('year-slider', 'value')
)

def load_yearly_data(selected_year):
    try:
        # 1. 拼接文件路径
        node_path = os.path.join(YEARLY_NETWORKS_DIR, f"nodes_{selected_year}.csv")
        edge_path = os.path.join(YEARLY_NETWORKS_DIR, f"edges_{selected_year}.csv")
        low_data_path = os.path.join(LOW_DATA_DIR, f"low_data_{selected_year}.csv")
        
        # 2. 检查文件是否存在
        if not all(os.path.exists(p) for p in [node_path, edge_path, low_data_path]):
            return dash.no_update, f"⚠️ 数据不完整：请检查 {selected_year} 年的 CSV 和 low_data 文件"

        # 3. 读取数据
        nodes = pd.read_csv(node_path)
        edges = pd.read_csv(edge_path)
        coords = pd.read_csv(low_data_path)

        # 4. 关键步骤：将预计算的坐标注入到节点数据中
        # 假设 nodes 和 coords 的行顺序在预处理时已完全对齐
        nodes['x'] = coords['x_tsne']
        nodes['y'] = coords['y_tsne']

        # 5. 组装 Payload
        data_payload = {
            "nodes": nodes.to_dict('records'),
            "links": edges.to_dict('records'),
            "year": selected_year
        }
        
        return data_payload, f"✅ 已成功加载 {selected_year} 年数据"

    except Exception as e:
        return dash.no_update, f"❌ 加载出错: {str(e)}"


# --- 客户端回调：触发 D3 渲染 ---
app.clientside_callback(
    """
    function(data) {
        if (!data) return "";
        // 这里的 window.renderD3Network 必须在 assets/viz_render.js 中定义
        if (typeof window.renderD3Network === 'function') {
            window.renderD3Network(data);
        } else {
            console.error("D3 渲染函数 window.renderD3Network 未找到，请检查 assets 文件夹。");
        }
        return "";
    }
    """,
    Output('d3-viz-container', 'children'),
    Input('net-data-store', 'data')
)

if __name__ == '__main__':
    app.run(debug=True, port=8050)
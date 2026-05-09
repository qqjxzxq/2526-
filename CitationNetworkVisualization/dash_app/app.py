import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import os

# 初始化 Dash
app = dash.Dash(__name__)

# --- 路径配置 (使用绝对路径确保稳定) ---
# 1. 原始元数据路径
RAW_METADATA_PATH = './data/vispub_final.csv'

# 2. 坐标与网络数据路径 (假设在当前 dash_app 目录的同级或子目录下)
# 如果这些文件夹就在 dash_app 目录下，保持现状；如果不在，请改为绝对路径
YEARLY_NETWORKS_DIR = "./yearly_networks/"
LOW_DATA_DIR = "./tsne_data/low_data/"

# --- 预加载原始元数据 ---
print(f"正在加载原始元数据: {RAW_METADATA_PATH}...")
if os.path.exists(RAW_METADATA_PATH):
    # 为了节省内存，只读取需要的列
    # 这里的列名对应你提供的：title, authorNamesDeduped, abstract, oa_openalex_id 等
    needed_columns = [
        'oa_openalex_id', 'title', 'authorNamesDeduped', 
        'abstract', 'conference', 'oa_cited_by_count', 'year'
    ]
    df_raw = pd.read_csv(
        RAW_METADATA_PATH, 
        usecols=['oa_openalex_id', 'title', 'authorNamesDeduped', 'abstract', 'conference', 'oa_cited_by_count'],
        dtype={'oa_openalex_id': str} # 强制 ID 为字符串，避免科学计数法错误
    )    
    
    # 统一 ID 格式：去掉 OpenAlex 的 URL 前缀，只保留 Wxxx 部分
    if 'oa_openalex_id' in df_raw.columns:
        df_raw['oa_id_clean'] = df_raw['oa_openalex_id'].astype(str).str.replace(
            "https://openalex.org/", "", regex=False
        )
    print("✅ 原始元数据加载成功")
else:
    print(f"❌ 错误: 找不到文件 {RAW_METADATA_PATH}")
    df_raw = pd.DataFrame()

app.layout = html.Div([
    html.H2("论文引用网络动态对比系统", style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#1A3678'}),
    
    # 控制面板
    html.Div([
        html.Div([
            html.Label("选择基准年份 (左侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-left-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                placeholder="选择年份 A", 
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'marginRight': '5%'}),
        
        html.Div([
            html.Label("选择对比年份 (右侧):", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='year-right-select',
                options=[{'label': str(i), 'value': i} for i in range(1990, 2026)],
                placeholder="选择年份 B",
                clearable=False
            ),
        ], style={'width': '45%', 'display': 'inline-block'}),
        
        html.Div(id='status-info', style={'color': '#1A3678', 'marginTop': '15px', 'textAlign': 'center', 'fontWeight': 'bold'})
    ], style={'width': '90%', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': '#fff', 'borderRadius': '10px', 'boxShadow': '0 2px 10px rgba(0,0,0,0.05)'}),

    # D3 绘图容器 (JS 将在此处构建 flex 布局：左侧 80% 画布，右侧 20% 信息面板)
    html.Div(id='d3-viz-container', style={
        'margin': '20px', 
        'border': '1px solid #eee', 
        'borderRadius': '10px',
        'backgroundColor': '#ffffff',
        'minHeight': '900px'
    }),
    
    dcc.Store(id='net-data-store')
], style={'backgroundColor': '#f4f7f6', 'minHeight': '100vh', 'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'})

# --- 服务端数据处理逻辑 ---
def get_single_year_data(selected_year):
    if selected_year is None:
        return None
        
    node_path = os.path.join(YEARLY_NETWORKS_DIR, f"nodes_{selected_year}.csv")
    edge_path = os.path.join(YEARLY_NETWORKS_DIR, f"edges_{selected_year}.csv")
    low_data_path = os.path.join(LOW_DATA_DIR, f"low_data_{selected_year}.csv")
    
    # 检查文件是否存在
    if not all(os.path.exists(p) for p in [node_path, edge_path, low_data_path]):
        print(f"数据缺失: {selected_year}")
        return None

    nodes = pd.read_csv(node_path)
    edges = pd.read_csv(edge_path)
    coords = pd.read_csv(low_data_path)
    
    # 1. 注入 t-SNE 坐标
    nodes['x'] = coords['x_tsne']
    nodes['y'] = coords['y_tsne']

    # 2. 合并元数据
    if not df_raw.empty:
        # 确保 nodes 表中的 id 为字符串
        nodes['id_str'] = nodes['id'].astype(str)
        
        # 将原始数据合并到节点信息中
        # left_on 为 nodes 的 id，right_on 为原始数据的清理后 ID
        nodes = nodes.merge(
            df_raw, 
            left_on='id_str', 
            right_on='oa_id_clean', 
            how='left'
        )
        
        # 填充缺失值，防止前端 JS 渲染时出现 "undefined"
        nodes['title'] = nodes['title'].fillna("Title Not Found")
        nodes['authorNamesDeduped'] = nodes['authorNamesDeduped'].fillna("Unknown Authors")
        nodes['abstract'] = nodes['abstract'].fillna("Abstract not available.")
        nodes['oa_cited_by_count'] = nodes['oa_cited_by_count'].fillna(0)
    
    # 3. 边过滤逻辑 (确保边两端的点都在 nodes 中)
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
    if y_left is None or y_right is None:
        return dash.no_update, "💡 请选择两个年份以查看学术演化对比"
    
    data_left = get_single_year_data(y_left)
    data_right = get_single_year_data(y_right)
    
    if data_left is None or data_right is None:
        return dash.no_update, "⚠️ 选定年份的数据文件不完整，请检查后端目录。"
    
    payload = {
        "left": data_left,
        "right": data_right
    }
    return payload, f"✅ 成功加载 {y_left} 与 {y_right} 的对比视图"

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
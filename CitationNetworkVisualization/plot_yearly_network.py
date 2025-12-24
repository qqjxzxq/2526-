import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import os
import argparse


def plot_year(year, data_dir="yearly_networks"):
    nodes_file = os.path.join(data_dir, f"nodes_{year}.csv")
    edges_file = os.path.join(data_dir, f"edges_{year}.csv")

    if not os.path.exists(nodes_file):
        raise FileNotFoundError(f"Missing {nodes_file}")
    if not os.path.exists(edges_file):
        raise FileNotFoundError(f"Missing {edges_file}")

    # ---------- Load data ----------
    nodes = pd.read_csv(nodes_file)
    edges = pd.read_csv(edges_file)

    print(f"📊 Year {year}: nodes={len(nodes)}, edges={len(edges)}")

    # ---------- Build graph ----------
    G = nx.DiGraph()

    for _, row in nodes.iterrows():
        G.add_node(
            row["id"],
            year=row["year"],
            total_citations=row["total_citations"]
        )

    for _, row in edges.iterrows():
        G.add_edge(row["source"], row["target"])

    if G.number_of_nodes() == 0:
        print("⚠ Empty graph")
        return

    # ---------- Force-directed layout ----------
    pos = nx.spring_layout(G, seed=42, k=0.7)

    # ---------- Edge trace ----------
    edge_x = []
    edge_y = []

    for src, tgt in G.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[tgt]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=0.5, color="rgba(160,160,160,0.4)"),
        hoverinfo="none"
    )

    # ---------- Node trace ----------
    node_x = []
    node_y = []
    node_size = []
    node_text = []

    for node in G.nodes():
        x, y = pos[node]
        c = G.nodes[node].get("total_citations", 0)


        node_x.append(x)
        node_y.append(y)

        # size scaling
        node_size.append(max(6, min(30, c ** 0.5 * 2)))

        node_text.append(
            f"ID: {node}<br>"
            f"Citations: {c}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            size=node_size,
            color=node_size,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Total citations")
        )
    )

    # ---------- Plot ----------
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=f"Citation Network ({year})",
            title_x=0.5,
            showlegend=False,
            hovermode="closest",
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
    )

    fig.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()

    plot_year(args.year)

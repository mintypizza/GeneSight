"""
visualizations.py — Interactive Plotly visualizations for GeneSight.

Includes ACMG criteria radar chart, variant impact gauge,
gene-disease network graph, and population frequency charts.
"""
import plotly.graph_objects as go
import plotly.express as px
import json
from typing import Optional


# Common dark theme layout
DARK_LAYOUT = dict(
    paper_bgcolor="rgba(10, 14, 26, 0)",
    plot_bgcolor="rgba(10, 14, 26, 0)",
    font=dict(family="Inter, sans-serif", color="#E5E7EB"),
    margin=dict(l=40, r=40, t=50, b=40),
)


def create_acmg_radar_chart(acmg_score: dict) -> go.Figure:
    """
    Create a radar chart showing ACMG criteria evidence distribution.

    Args:
        acmg_score: Dictionary with ACMG evidence counts:
            {pathogenic_very_strong, pathogenic_strong, pathogenic_moderate,
             pathogenic_supporting, benign_standalone, benign_strong, benign_supporting}
    """
    categories = [
        "Pathogenic\nVery Strong",
        "Pathogenic\nStrong",
        "Pathogenic\nModerate",
        "Pathogenic\nSupporting",
        "Benign\nStandalone",
        "Benign\nStrong",
        "Benign\nSupporting"
    ]

    values = [
        acmg_score.get("pathogenic_very_strong", 0),
        acmg_score.get("pathogenic_strong", 0),
        acmg_score.get("pathogenic_moderate", 0),
        acmg_score.get("pathogenic_supporting", 0),
        acmg_score.get("benign_standalone", 0),
        acmg_score.get("benign_strong", 0),
        acmg_score.get("benign_supporting", 0),
    ]

    # Max values for normalization
    max_vals = [1, 4, 6, 5, 1, 4, 7]
    normalized = [min(v / m, 1.0) if m > 0 else 0 for v, m in zip(values, max_vals)]

    # Close the polygon
    categories_closed = categories + [categories[0]]
    normalized_closed = normalized + [normalized[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    # Pathogenic fill (red tones)
    fig.add_trace(go.Scatterpolar(
        r=normalized_closed[:5] + [normalized_closed[0]],
        theta=categories_closed[:5] + [categories_closed[0]],
        fill='toself',
        fillcolor='rgba(239, 68, 68, 0.15)',
        line=dict(color='#EF4444', width=2),
        name='Pathogenic Evidence',
        text=[f"Count: {v}" for v in values_closed[:5]] + [f"Count: {values_closed[0]}"],
        hoverinfo='text+name'
    ))

    # Benign fill (green tones)
    fig.add_trace(go.Scatterpolar(
        r=[0, 0, 0, 0] + normalized_closed[4:],
        theta=categories_closed[:4] + categories_closed[4:],
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.15)',
        line=dict(color='#10B981', width=2),
        name='Benign Evidence',
        text=[f"Count: 0"] * 4 + [f"Count: {v}" for v in values_closed[4:]],
        hoverinfo='text+name'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0.25, 0.5, 0.75, 1.0],
                ticktext=["Low", "Med", "High", "Max"],
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.08)",
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.08)",
            ),
            bgcolor="rgba(10, 14, 26, 0)",
        ),
        title=dict(text="ACMG Evidence Radar", font=dict(size=16, color="#00D4AA")),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        **DARK_LAYOUT
    )

    return fig


def create_pathogenicity_gauge(classification: str, confidence: str) -> go.Figure:
    """
    Create a gauge chart showing pathogenicity classification.

    Args:
        classification: One of Pathogenic, Likely Pathogenic, VUS, Likely Benign, Benign
        confidence: One of high, moderate, low
    """
    score_map = {
        "pathogenic": 90,
        "likely pathogenic": 70,
        "uncertain significance (vus)": 50,
        "vus": 50,
        "uncertain significance": 50,
        "likely benign": 30,
        "benign": 10,
        "risk factor": 60,
        "drug response": 55,
    }

    score = score_map.get(classification.lower(), 50)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title=dict(text="Pathogenicity Score", font=dict(size=16, color="#00D4AA")),
        number=dict(
            font=dict(size=36, color="#E5E7EB"),
            suffix="/100"
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#4B5563"),
            bar=dict(color="#00D4AA", thickness=0.3),
            bgcolor="rgba(17, 24, 39, 0.5)",
            bordercolor="rgba(255,255,255,0.1)",
            steps=[
                dict(range=[0, 20], color="rgba(16, 185, 129, 0.3)"),   # Benign
                dict(range=[20, 40], color="rgba(34, 197, 94, 0.2)"),   # Likely Benign
                dict(range=[40, 60], color="rgba(234, 179, 8, 0.2)"),   # VUS
                dict(range=[60, 80], color="rgba(249, 115, 22, 0.2)"),  # Likely Pathogenic
                dict(range=[80, 100], color="rgba(239, 68, 68, 0.3)"),  # Pathogenic
            ],
            threshold=dict(
                line=dict(color="#E5E7EB", width=3),
                thickness=0.8,
                value=score
            )
        )
    ))

    # Add classification labels
    fig.add_annotation(x=0.1, y=-0.15, text="Benign", showarrow=False,
                       font=dict(size=10, color="#10B981"), xref="paper", yref="paper")
    fig.add_annotation(x=0.5, y=-0.15, text="VUS", showarrow=False,
                       font=dict(size=10, color="#EAB308"), xref="paper", yref="paper")
    fig.add_annotation(x=0.9, y=-0.15, text="Pathogenic", showarrow=False,
                       font=dict(size=10, color="#EF4444"), xref="paper", yref="paper")

    fig.update_layout(
        height=280,
        **DARK_LAYOUT
    )

    return fig


def create_evidence_bar_chart(tool_calls: list) -> go.Figure:
    """Create a horizontal bar chart showing evidence sources and their contributions."""
    tool_labels = {
        "tool_query_clinvar": "ClinVar",
        "tool_query_uniprot": "UniProt",
        "tool_search_pubmed": "PubMed",
        "tool_assess_pathogenicity": "ACMG",
        "tool_check_drug_interactions": "PharmGKB",
    }

    tool_colors = {
        "tool_query_clinvar": "#EF4444",
        "tool_query_uniprot": "#3B82F6",
        "tool_search_pubmed": "#10B981",
        "tool_assess_pathogenicity": "#F97316",
        "tool_check_drug_interactions": "#A855F7",
    }

    tools_used = []
    data_sizes = []
    colors = []

    for tc in tool_calls:
        name = tc["tool"]
        label = tool_labels.get(name, name)
        if label not in tools_used:
            tools_used.append(label)
            data_sizes.append(len(tc.get("result_preview", "")))
            colors.append(tool_colors.get(name, "#6B7280"))

    fig = go.Figure(go.Bar(
        y=tools_used,
        x=data_sizes,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color="rgba(255,255,255,0.1)", width=1)
        ),
        text=[f"{s:,} chars" for s in data_sizes],
        textposition='auto',
        textfont=dict(size=11, color="#E5E7EB"),
        hovertemplate="<b>%{y}</b><br>Data retrieved: %{x:,} characters<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Evidence Sources", font=dict(size=16, color="#00D4AA")),
        xaxis=dict(
            title="Data Retrieved (characters)",
            gridcolor="rgba(255,255,255,0.05)",
            showgrid=True,
        ),
        yaxis=dict(autorange="reversed"),
        height=250,
        **DARK_LAYOUT
    )

    return fig


def create_gene_disease_network(
    gene: str,
    diseases: list,
    drugs: list = None,
    domains: list = None
) -> go.Figure:
    """
    Create an interactive network graph showing gene-disease-drug relationships.

    Args:
        gene: Gene symbol (central node)
        diseases: List of disease names
        drugs: Optional list of affected drugs
        domains: Optional list of protein domains
    """
    import networkx as nx
    import math

    G = nx.Graph()

    # Central gene node
    G.add_node(gene, node_type="gene")

    # Disease nodes
    for d in (diseases or [])[:6]:
        name = d if isinstance(d, str) else d.get("name", str(d))
        if name:
            G.add_node(name, node_type="disease")
            G.add_edge(gene, name)

    # Drug nodes
    for d in (drugs or [])[:6]:
        name = d if isinstance(d, str) else d.get("drug", str(d))
        if name:
            G.add_node(name, node_type="drug")
            G.add_edge(gene, name)

    # Domain nodes
    for d in (domains or [])[:4]:
        name = d if isinstance(d, str) else d.get("name", str(d))
        if name:
            G.add_node(name, node_type="domain")
            G.add_edge(gene, name)

    if len(G.nodes) < 2:
        # Not enough data for a meaningful graph
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for network visualization",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=14, color="#6B7280")
        )
        fig.update_layout(height=300, **DARK_LAYOUT)
        return fig

    # Layout
    pos = nx.spring_layout(G, seed=42, k=2.5)

    # Color/size maps
    color_map = {"gene": "#00D4AA", "disease": "#EF4444", "drug": "#A855F7", "domain": "#3B82F6"}
    size_map = {"gene": 35, "disease": 22, "drug": 20, "domain": 18}

    # Build edge traces
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1.5, color='rgba(255,255,255,0.15)'),
        hoverinfo='none'
    )

    # Build node traces
    node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        ntype = G.nodes[node].get("node_type", "other")
        node_text.append(f"{node}<br>Type: {ntype.title()}")
        node_colors.append(color_map.get(ntype, "#6B7280"))
        node_sizes.append(size_map.get(ntype, 15))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[n for n in G.nodes()],
        textposition="top center",
        textfont=dict(size=10, color="#E5E7EB"),
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='rgba(255,255,255,0.2)'),
            opacity=0.9,
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])

    # Add legend annotations
    legend_items = [
        ("Gene", "#00D4AA", 0.02),
        ("Disease", "#EF4444", 0.17),
        ("Drug", "#A855F7", 0.32),
        ("Domain", "#3B82F6", 0.47),
    ]
    for label, color, x_pos in legend_items:
        fig.add_annotation(
            x=x_pos, y=1.08, text=f"● {label}",
            showarrow=False, xref="paper", yref="paper",
            font=dict(size=11, color=color)
        )

    fig.update_layout(
        title=dict(text="Gene-Disease-Drug Network", font=dict(size=16, color="#00D4AA")),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
        **DARK_LAYOUT
    )

    return fig

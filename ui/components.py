"""
components.py — Reusable Streamlit UI components for GeneSight.
"""
import streamlit as st
import json
from pathlib import Path


def render_header():
    """Render the animated GeneSight header."""
    st.markdown("""
    <div class="genesight-header">
        <div class="header-title">🧬 GeneSight</div>
        <div class="header-subtitle">AI-Powered Genetic Variant Interpretation — Powered by Gemma 4</div>
        <div class="header-badge">
            🔒 Privacy-First • Your genetic data never leaves this device
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pathogenicity_badge(classification: str) -> str:
    """Return HTML for a color-coded pathogenicity badge."""
    badge_map = {
        "pathogenic": ("🔴 Pathogenic", "badge-pathogenic"),
        "likely pathogenic": ("🟠 Likely Pathogenic", "badge-likely-pathogenic"),
        "uncertain significance": ("🟡 VUS", "badge-vus"),
        "vus": ("🟡 VUS", "badge-vus"),
        "likely benign": ("🟢 Likely Benign", "badge-likely-benign"),
        "benign": ("🟢 Benign", "badge-benign"),
        "risk factor": ("🟣 Risk Factor", "badge-risk-factor"),
        "drug response": ("🔵 Drug Response", "badge-drug-response"),
    }

    key = classification.lower().strip()
    label, css_class = badge_map.get(key, (f"⚪ {classification}", "badge-vus"))
    return f'<span class="badge {css_class}">{label}</span>'


def render_star_rating(stars: int, max_stars: int = 4) -> str:
    """Return HTML for a ClinVar-style star rating."""
    filled = "★" * stars
    empty = "★" * (max_stars - stars)
    return f'<span class="star-rating">{filled}</span><span class="star-rating star-empty">{empty}</span>'


def render_metric_cards(metrics: dict):
    """Render a row of metric cards."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_tool_timeline(tool_calls: list):
    """Render the tool call timeline showing the agent's reasoning steps."""
    if not tool_calls:
        return

    st.markdown('<div class="glass-card-header">🔗 Evidence Trail</div>', unsafe_allow_html=True)
    st.markdown('<div class="tool-timeline">', unsafe_allow_html=True)

    tool_icons = {
        "tool_query_clinvar": "🏥",
        "tool_query_uniprot": "🧬",
        "tool_search_pubmed": "📚",
        "tool_assess_pathogenicity": "⚖️",
        "tool_check_drug_interactions": "💊",
    }

    tool_labels = {
        "tool_query_clinvar": "ClinVar Database",
        "tool_query_uniprot": "UniProt Protein DB",
        "tool_search_pubmed": "PubMed Literature",
        "tool_assess_pathogenicity": "ACMG Assessment",
        "tool_check_drug_interactions": "Pharmacogenomics",
    }

    for tc in tool_calls:
        icon = tool_icons.get(tc["tool"], "🔧")
        label = tool_labels.get(tc["tool"], tc["tool"])
        args = ", ".join(f"{k}={v}" for k, v in tc.get("args", {}).items())

        st.markdown(f"""
        <div class="tool-step">
            <div class="tool-name">{icon} {label}</div>
            <div class="tool-args">{args}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show expandable result
        with st.expander(f"View {label} results", expanded=False):
            try:
                result_data = json.loads(tc.get("result_preview", "{}").rstrip("..."))
                st.json(result_data)
            except json.JSONDecodeError:
                st.code(tc.get("result_preview", "No data"), language="json")

    st.markdown('</div>', unsafe_allow_html=True)


def render_demo_variant_selector() -> str:
    """Render demo variant selector cards and return the selected variant query."""
    data_path = Path(__file__).parent.parent / "data" / "sample_variants.json"
    with open(data_path, 'r', encoding='utf-8') as f:
        sample_data = json.load(f)

    demos = sample_data["demo_variants"]

    st.markdown("### 🎯 Quick Demo — Select a Variant")
    st.markdown(
        '<p style="color: #6B7280; font-size: 0.85rem; margin-bottom: 1rem;">'
        'Choose a well-known variant to see GeneSight in action</p>',
        unsafe_allow_html=True
    )

    cols = st.columns(len(demos))
    selected = None

    for i, (col, demo) in enumerate(zip(cols, demos)):
        with col:
            if st.button(
                f"🧬 {demo['gene']}\n{demo['variant']}",
                key=f"demo_{i}",
                use_container_width=True,
                help=demo["description"][:100] + "..."
            ):
                selected = demo

    if selected:
        return f"Analyze the genetic variant {selected['gene']} {selected['variant']} ({selected['rsid']}). " \
               f"What is its clinical significance and what does it mean for a patient?"

    return ""


def render_glass_card(header: str, content: str, icon: str = ""):
    """Render a glassmorphism card with content."""
    st.markdown(f"""
    <div class="glass-card">
        <div class="glass-card-header">{icon} {header}</div>
        {content}
    </div>
    """, unsafe_allow_html=True)


def render_privacy_banner():
    """Render the privacy-first banner."""
    st.markdown("""
    <div class="privacy-banner">
        🔒 <strong>Privacy First:</strong>&nbsp;GeneSight processes genetic data locally. 
        Your sequences and variant data are never stored on external servers. 
        Only database queries (gene names, rsIDs) are sent to public scientific APIs.
    </div>
    """, unsafe_allow_html=True)


def render_gradient_divider():
    """Render a gradient divider line."""
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

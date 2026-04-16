"""
GeneSight — AI-Powered Genetic Variant Interpreter
Powered by Gemma 4 with Native Function Calling

A privacy-first tool that brings clinical-grade genetic variant
interpretation to any device, using Gemma 4's agentic capabilities
to query ClinVar, UniProt, PubMed, and apply ACMG guidelines.

Usage:
    streamlit run app.py
"""
import sys
import os
import json
import streamlit as st
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.styles import get_custom_css
from ui.components import (
    render_header,
    render_pathogenicity_badge,
    render_metric_cards,
    render_tool_timeline,
    render_demo_variant_selector,
    render_privacy_banner,
    render_gradient_divider,
    render_glass_card,
    render_star_rating,
)
from ui.visualizations import (
    create_acmg_radar_chart,
    create_pathogenicity_gauge,
    create_evidence_bar_chart,
    create_gene_disease_network,
)
from utils.variant_parser import parse_variant
from core.report_generator import generate_clinical_report, generate_report_summary_card


# ========================
# Page Configuration
# ========================
st.set_page_config(
    page_title="GeneSight — AI Genetic Variant Interpreter",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "GeneSight: AI-Powered Genetic Variant Interpretation. Powered by Gemma 4.",
        "Report a Bug": "https://github.com/genesight/issues",
    }
)

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# ========================
# Session State Init
# ========================
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "patient_report" not in st.session_state:
    st.session_state.patient_report = None
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemma-4-31b-it"


# ========================
# Sidebar
# ========================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # API Key input
    api_key = st.text_input(
        "Google AI Studio API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your free API key at https://aistudio.google.com/apikey",
        placeholder="Enter your API key..."
    )
    if api_key:
        st.session_state.api_key = api_key

    if not api_key:
        st.warning("⚠️ Enter your API key to enable AI analysis")
        st.markdown(
            "[🔑 Get a free API key →](https://aistudio.google.com/apikey)",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Model selection
    st.session_state.selected_model = st.selectbox(
        "Gemma 4 Model",
        options=["gemma-4-31b-it", "gemma-4-26b-a4b-it"],
        index=0,
        help="31B Dense: Best quality. 26B MoE: Faster, efficient."
    )

    st.markdown("---")

    # Gene panel info
    st.markdown("### 📋 Gene Panels")
    panels_path = Path(__file__).parent / "data" / "gene_panels.json"
    if panels_path.exists():
        with open(panels_path, 'r') as f:
            panels = json.load(f)["panels"]
        for panel_key, panel_data in panels.items():
            with st.expander(f"🧬 {panel_data['name']}", expanded=False):
                st.caption(panel_data["description"])
                genes_str = ", ".join(panel_data["genes"][:10])
                if len(panel_data["genes"]) > 10:
                    genes_str += f" +{len(panel_data['genes'])-10} more"
                st.code(genes_str, language=None)

    st.markdown("---")

    # Privacy info
    render_privacy_banner()

    st.markdown("---")
    st.markdown(
        '<p style="color: #4B5563; font-size: 0.7rem; text-align: center;">'
        'GeneSight v1.0 • Powered by Gemma 4<br>'
        'For research & educational use only</p>',
        unsafe_allow_html=True
    )


# ========================
# Main Content
# ========================
render_header()

# Tabs
tab_analyze, tab_results, tab_report, tab_about = st.tabs([
    "🧬 Analyze Variant",
    "📊 Results Dashboard",
    "📄 Reports",
    "ℹ️ About"
])


# ========================
# TAB 1: Analyze Variant
# ========================
with tab_analyze:
    col_input, col_info = st.columns([2, 1])

    with col_input:
        st.markdown("### Enter a Genetic Variant")
        st.markdown(
            '<p style="color: #6B7280; font-size: 0.85rem;">'
            'Type a variant in any format: rsID, HGVS, gene + variant, or genomic coordinates</p>',
            unsafe_allow_html=True
        )

        # Variant input
        user_input = st.text_area(
            "Variant Query",
            height=100,
            placeholder="Examples:\n• BRCA1 c.68_69del\n• rs80357714\n• TP53 R175H\n• chr17:41276045 G>A",
            label_visibility="collapsed"
        )

        # Demo variant selector
        render_gradient_divider()
        demo_query = render_demo_variant_selector()

        if demo_query and not user_input:
            user_input = demo_query
            st.info(f"📋 Selected demo variant. Click 'Analyze' to proceed.")

    with col_info:
        st.markdown("### Supported Formats")
        st.markdown("""
        | Format | Example |
        |--------|---------|
        | **rsID** | `rs80357714` |
        | **Gene + HGVS** | `BRCA1 c.68_69del` |
        | **Gene + Protein** | `TP53 R175H` |
        | **Star Allele** | `CYP2D6 *4` |
        | **Genomic Coords** | `chr17:41276045 G>A` |
        | **HGVS Transcript** | `NM_007294.4:c.68_69del` |
        """)

        if user_input:
            parsed = parse_variant(user_input)
            st.markdown("#### Parsed Variant")
            parsed_dict = parsed.to_dict()
            for key, val in parsed_dict.items():
                if key != "raw_input" and val:
                    st.markdown(f"**{key.replace('_', ' ').title()}:** `{val}`")

    render_gradient_divider()

    # Analyze button
    col_btn, col_status = st.columns([1, 2])

    with col_btn:
        analyze_clicked = st.button(
            "🔬 Analyze with Gemma 4",
            use_container_width=True,
            disabled=not (user_input and st.session_state.api_key),
            type="primary"
        )

    if analyze_clicked and user_input and st.session_state.api_key:
        with col_status:
            status_container = st.empty()
            progress_bar = st.progress(0)

        # Initialize agent
        try:
            from core.gemma_agent import GemmaAgent

            agent = GemmaAgent(
                api_key=st.session_state.api_key,
                model=st.session_state.selected_model
            )

            tool_calls_display = st.container()
            step_count = [0]

            def on_thinking(msg):
                status_container.markdown(
                    f'<div class="loading-pulse">{msg}</div>',
                    unsafe_allow_html=True
                )
                step_count[0] += 1
                progress_bar.progress(min(step_count[0] * 12, 95))

            def on_tool_call(name, args, result):
                tool_labels = {
                    "tool_query_clinvar": "🏥 Querying ClinVar...",
                    "tool_query_uniprot": "🧬 Querying UniProt...",
                    "tool_search_pubmed": "📚 Searching PubMed...",
                    "tool_assess_pathogenicity": "⚖️ Applying ACMG Criteria...",
                    "tool_check_drug_interactions": "💊 Checking Drug Interactions...",
                }
                with tool_calls_display:
                    st.success(tool_labels.get(name, f"🔧 {name}"))

            # Run analysis
            with st.spinner("🧠 Gemma 4 is analyzing your variant..."):
                result = agent.analyze_variant(
                    user_query=user_input,
                    on_tool_call=on_tool_call,
                    on_thinking=on_thinking
                )

            progress_bar.progress(100)
            status_container.markdown(
                '<div class="loading-pulse" style="border-color: rgba(16,185,129,0.3); '
                'color: #10B981;">✅ Analysis complete!</div>',
                unsafe_allow_html=True
            )

            st.session_state.analysis_result = result
            st.session_state.patient_report = None  # Reset patient report

            st.rerun()

        except ImportError as e:
            st.error(f"❌ Missing dependency: {e}. Run `pip install -r requirements.txt`")
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            progress_bar.empty()


# ========================
# TAB 2: Results Dashboard
# ========================
with tab_results:
    if st.session_state.analysis_result is None:
        st.markdown(
            '<div style="text-align: center; padding: 4rem 2rem; color: #4B5563;">'
            '<h2 style="color: #6B7280;">No Analysis Yet</h2>'
            '<p>Enter a variant in the Analyze tab to see results here.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        result = st.session_state.analysis_result
        summary = generate_report_summary_card(result)

        # Metric cards
        render_metric_cards({
            "Classification": summary.get("classification", "N/A"),
            "Databases Queried": str(summary.get("num_databases", 0)),
            "Agentic Turns": str(result.get("turns_used", 0)),
            "Analysis Time": f"{result.get('elapsed_seconds', 0)}s",
        })

        render_gradient_divider()

        # Main analysis content
        col_analysis, col_viz = st.columns([3, 2])

        with col_analysis:
            st.markdown("### 📋 Clinical Analysis")
            st.markdown(result.get("analysis", "No analysis available."))

            render_gradient_divider()

            # Tool call timeline
            render_tool_timeline(result.get("tool_calls", []))

        with col_viz:
            # Pathogenicity gauge
            gauge_fig = create_pathogenicity_gauge(
                summary.get("classification", "VUS"),
                summary.get("confidence", "low")
            )
            st.plotly_chart(gauge_fig, use_container_width=True)

            # Evidence sources bar chart
            if result.get("tool_calls"):
                bar_fig = create_evidence_bar_chart(result["tool_calls"])
                st.plotly_chart(bar_fig, use_container_width=True)

            # Try to extract ACMG data for radar chart
            for tc in result.get("tool_calls", []):
                if tc["tool"] == "tool_assess_pathogenicity":
                    try:
                        acmg_data = json.loads(tc.get("result_preview", "{}").rstrip("..."))
                        if "acmg_score" in acmg_data:
                            radar_fig = create_acmg_radar_chart(acmg_data["acmg_score"])
                            st.plotly_chart(radar_fig, use_container_width=True)
                    except (json.JSONDecodeError, KeyError):
                        pass
                    break

            # Try to build gene-disease network
            diseases = []
            drugs = []
            domains = []
            gene_name = ""

            for tc in result.get("tool_calls", []):
                try:
                    data = json.loads(tc.get("result_preview", "{}").rstrip("..."))

                    if tc["tool"] == "tool_query_clinvar":
                        for v in data.get("variants", []):
                            diseases.extend(v.get("conditions", []))

                    elif tc["tool"] == "tool_query_uniprot":
                        prot = data.get("protein", {})
                        if prot:
                            gene_name = prot.get("gene_symbol", "")
                            diseases.extend([d.get("name", "") for d in prot.get("diseases", [])])
                            domains.extend([d.get("name", "") for d in prot.get("domains", [])])

                    elif tc["tool"] == "tool_check_drug_interactions":
                        drug_data = data.get("data", {})
                        if drug_data:
                            drugs.extend([d.get("drug", "") for d in drug_data.get("affected_drugs", [])])

                except (json.JSONDecodeError, AttributeError):
                    pass

            if gene_name and (diseases or drugs or domains):
                network_fig = create_gene_disease_network(
                    gene=gene_name,
                    diseases=diseases,
                    drugs=drugs,
                    domains=domains
                )
                st.plotly_chart(network_fig, use_container_width=True)


# ========================
# TAB 3: Reports
# ========================
with tab_report:
    if st.session_state.analysis_result is None:
        st.markdown(
            '<div style="text-align: center; padding: 4rem 2rem; color: #4B5563;">'
            '<h2 style="color: #6B7280;">No Analysis Yet</h2>'
            '<p>Run an analysis first to generate reports.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        result = st.session_state.analysis_result

        col_clinical, col_patient = st.columns(2)

        with col_clinical:
            st.markdown("### 🏥 Clinical Report")
            st.markdown(
                '<p style="color: #6B7280; font-size: 0.85rem;">'
                'Technical report for healthcare providers</p>',
                unsafe_allow_html=True
            )

            # Parse variant for report
            parsed = parse_variant(result.get("query", ""))
            clinical_report = generate_clinical_report(
                result,
                variant_info=parsed.to_dict()
            )

            with st.expander("📄 View Clinical Report", expanded=True):
                st.markdown(clinical_report)

            st.download_button(
                label="⬇️ Download Clinical Report",
                data=clinical_report,
                file_name="genesight_clinical_report.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col_patient:
            st.markdown("### 👤 Patient-Friendly Report")
            st.markdown(
                '<p style="color: #6B7280; font-size: 0.85rem;">'
                'Plain-language explanation for patients & families</p>',
                unsafe_allow_html=True
            )

            if st.session_state.patient_report:
                with st.expander("📄 View Patient Report", expanded=True):
                    st.markdown(st.session_state.patient_report)

                st.download_button(
                    label="⬇️ Download Patient Report",
                    data=st.session_state.patient_report,
                    file_name="genesight_patient_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                if st.button(
                    "🤖 Generate Patient Report with Gemma 4",
                    use_container_width=True,
                    disabled=not st.session_state.api_key
                ):
                    try:
                        from core.gemma_agent import GemmaAgent
                        agent = GemmaAgent(
                            api_key=st.session_state.api_key,
                            model=st.session_state.selected_model
                        )
                        with st.spinner("🧠 Generating patient-friendly explanation..."):
                            patient_text = agent.generate_patient_report(
                                result.get("analysis", "")
                            )
                        st.session_state.patient_report = patient_text
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating report: {e}")


# ========================
# TAB 4: About
# ========================
with tab_about:
    col_about, col_arch = st.columns([1, 1])

    with col_about:
        st.markdown("""
        ### 🧬 About GeneSight

        GeneSight is an AI-powered genetic variant interpretation platform built for the 
        **Gemma 4 Impact Challenge**. It demonstrates how Gemma 4's native function calling 
        capabilities can be used to create an autonomous genetic counseling agent.

        #### The Problem

        > **300+ million people** worldwide are affected by rare diseases. Patients wait an 
        > average of **4–7 years** for a correct diagnosis. Meanwhile, access to clinical 
        > geneticists is severely limited, especially in underserved communities.

        #### The Solution

        GeneSight brings expert-level variant interpretation to any device:

        - 🔒 **Privacy-First** — Genetic data never leaves your device
        - 🧠 **AI-Powered** — Gemma 4 reasons through complex genetic evidence
        - 🌐 **Multi-Database** — Queries ClinVar, UniProt, PubMed in real-time
        - ⚖️ **ACMG-Compliant** — Follows clinical variant classification guidelines
        - 💊 **Pharmacogenomics** — Identifies drug interaction risks
        - 📄 **Dual Reports** — Clinical & patient-friendly outputs

        #### Hackathon Tracks

        | Track | Coverage |
        |-------|----------|
        | Health & Sciences | ✅ Clinical genetic interpretation |
        | Digital Equity | ✅ Runs locally, accessible anywhere |
        | Safety & Trust | ✅ Grounded outputs with citations |
        | Global Resilience | ✅ Offline-capable edge deployment |
        """)

    with col_arch:
        st.markdown("""
        ### 🏗️ Architecture

        #### Gemma 4 Integration

        GeneSight uses **Gemma 4 31B-IT** with **native function calling** via the 
        `google-genai` SDK. The model autonomously:

        1. **Parses** the variant from natural language input
        2. **Plans** which databases to query
        3. **Calls tools** — ClinVar, UniProt, PubMed APIs
        4. **Applies** ACMG/AMP classification criteria
        5. **Synthesizes** all evidence into a clinical report
        6. **Generates** patient-friendly explanations

        #### Tech Stack

        | Component | Technology |
        |-----------|-----------|
        | AI Model | Gemma 4 31B-IT |
        | Framework | Python + Streamlit |
        | Function Calling | google-genai SDK |
        | Databases | ClinVar, UniProt, PubMed |
        | Guidelines | ACMG/AMP 2015 Criteria |
        | Visualization | Plotly + NetworkX |
        | Pharmacogenomics | PharmGKB / CPIC |

        #### Privacy Architecture

        ```
        ┌─────────────────────────┐
        │    User's Device        │
        │  ┌───────────────────┐  │
        │  │ GeneSight App     │  │
        │  │  ├─ Variant Data  │  │ ← Never leaves device
        │  │  ├─ Gemma 4 API   │──┼──→ Google AI (model only)
        │  │  └─ Reports       │  │ ← Generated locally
        │  └───────────────────┘  │
        │         │               │
        │    Only gene names &    │
        │    rsIDs are sent to:   │
        │         ↓               │
        │  Public Scientific APIs │
        │  (ClinVar, UniProt,     │
        │   PubMed)               │
        └─────────────────────────┘
        ```
        """)

    render_gradient_divider()

    st.markdown("""
    > ⚠️ **Disclaimer**: GeneSight is an educational and research tool. It is NOT a substitute 
    > for professional genetic counseling or clinical diagnosis. All findings should be reviewed 
    > by a qualified healthcare professional before any clinical decisions are made.
    """)

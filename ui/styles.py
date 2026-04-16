"""
styles.py — Custom CSS for GeneSight's premium biotech-inspired dark theme.

Includes glassmorphism cards, DNA helix animations, color-coded pathogenicity
badges, and smooth transitions.
"""


def get_custom_css() -> str:
    """Return the full custom CSS for the GeneSight app."""
    return """
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ===== GLOBAL OVERRIDES ===== */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: rgba(10, 14, 26, 0.8);
        backdrop-filter: blur(20px);
    }

    /* ===== ANIMATED HEADER ===== */
    .genesight-header {
        background: linear-gradient(135deg, #0A0E1A 0%, #111827 40%, #0f2027 100%);
        border-bottom: 1px solid rgba(0, 212, 170, 0.2);
        padding: 2rem 2rem 1.5rem;
        margin: -1rem -1rem 2rem -1rem;
        position: relative;
        overflow: hidden;
    }

    .genesight-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00D4AA, #7C3AED, #3B82F6, #00D4AA);
        background-size: 300% 100%;
        animation: shimmer 4s ease-in-out infinite;
    }

    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    .header-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D4AA 0%, #3B82F6 50%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }

    .header-subtitle {
        font-size: 1.05rem;
        color: #9CA3AF;
        font-weight: 400;
        letter-spacing: 0.01em;
    }

    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.8rem;
        background: rgba(0, 212, 170, 0.1);
        border: 1px solid rgba(0, 212, 170, 0.3);
        border-radius: 20px;
        font-size: 0.75rem;
        color: #00D4AA;
        font-weight: 600;
        margin-top: 0.75rem;
    }

    /* ===== DNA HELIX ANIMATION ===== */
    .dna-container {
        position: absolute;
        right: 2rem;
        top: 50%;
        transform: translateY(-50%);
        opacity: 0.15;
        pointer-events: none;
    }

    /* ===== GLASSMORPHISM CARDS ===== */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(0, 212, 170, 0.3);
        box-shadow: 0 8px 32px rgba(0, 212, 170, 0.08);
        transform: translateY(-1px);
    }

    .glass-card-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #00D4AA;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ===== PATHOGENICITY BADGES ===== */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .badge-pathogenic {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .badge-likely-pathogenic {
        background: rgba(249, 115, 22, 0.15);
        color: #F97316;
        border: 1px solid rgba(249, 115, 22, 0.3);
    }

    .badge-vus {
        background: rgba(234, 179, 8, 0.15);
        color: #EAB308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }

    .badge-likely-benign {
        background: rgba(34, 197, 94, 0.15);
        color: #22C55E;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .badge-benign {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-risk-factor {
        background: rgba(168, 85, 247, 0.15);
        color: #A855F7;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    .badge-drug-response {
        background: rgba(59, 130, 246, 0.15);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* ===== TOOL CALL TIMELINE ===== */
    .tool-timeline {
        position: relative;
        padding-left: 2rem;
    }

    .tool-timeline::before {
        content: '';
        position: absolute;
        left: 0.75rem;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #00D4AA, #3B82F6, #7C3AED);
        border-radius: 1px;
    }

    .tool-step {
        position: relative;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    .tool-step::before {
        content: '';
        position: absolute;
        left: -1.6rem;
        top: 1rem;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #00D4AA;
        box-shadow: 0 0 8px rgba(0, 212, 170, 0.5);
    }

    .tool-step:hover {
        border-color: rgba(0, 212, 170, 0.2);
        background: rgba(17, 24, 39, 0.8);
    }

    .tool-name {
        font-weight: 700;
        color: #E5E7EB;
        font-size: 0.9rem;
    }

    .tool-args {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #9CA3AF;
        margin-top: 0.25rem;
    }

    /* ===== METRIC CARDS ===== */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        flex: 1;
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
    }

    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00D4AA, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .metric-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6B7280;
        margin-top: 0.25rem;
        font-weight: 600;
    }

    /* ===== ANIMATED LOADING ===== */
    .loading-pulse {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        background: rgba(0, 212, 170, 0.05);
        border: 1px solid rgba(0, 212, 170, 0.15);
        border-radius: 10px;
        color: #00D4AA;
        font-weight: 500;
        animation: pulse-glow 2s ease-in-out infinite;
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0, 212, 170, 0); }
        50% { box-shadow: 0 0 20px 0 rgba(0, 212, 170, 0.1); }
    }

    /* ===== STAR RATING ===== */
    .star-rating {
        color: #EAB308;
        font-size: 1rem;
        letter-spacing: 2px;
    }

    .star-empty {
        color: #374151;
    }

    /* ===== DEMO VARIANT SELECTOR ===== */
    .demo-card {
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .demo-card:hover {
        border-color: rgba(0, 212, 170, 0.4);
        background: rgba(0, 212, 170, 0.05);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 212, 170, 0.1);
    }

    .demo-card-gene {
        font-size: 1.1rem;
        font-weight: 700;
        color: #E5E7EB;
    }

    .demo-card-variant {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #00D4AA;
        margin-top: 0.15rem;
    }

    .demo-card-desc {
        font-size: 0.75rem;
        color: #6B7280;
        margin-top: 0.35rem;
        line-height: 1.4;
    }

    /* ===== TABS STYLE ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(17, 24, 39, 0.5);
        border-radius: 12px;
        padding: 0.35rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.25rem;
        font-weight: 600;
        font-size: 0.85rem;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0, 212, 170, 0.15) !important;
        color: #00D4AA !important;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(17, 24, 39, 0.5);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0, 212, 170, 0.3);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 212, 170, 0.5);
    }

    /* ===== BUTTON OVERRIDES ===== */
    .stButton > button {
        background: linear-gradient(135deg, #00D4AA 0%, #059669 100%);
        color: #0A0E1A;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        letter-spacing: 0.02em;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0, 212, 170, 0.3);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* ===== TEXT INPUT OVERRIDES ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #E5E7EB;
        font-family: 'JetBrains Mono', monospace;
        padding: 0.75rem;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #00D4AA;
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2);
    }

    /* ===== EXPANDER STYLE ===== */
    .streamlit-expanderHeader {
        background: rgba(17, 24, 39, 0.5);
        border-radius: 10px;
        font-weight: 600;
    }

    /* ===== DIVIDER ===== */
    .gradient-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 170, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* ===== PRIVACY BANNER ===== */
    .privacy-banner {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        color: #10B981;
    }
</style>
"""

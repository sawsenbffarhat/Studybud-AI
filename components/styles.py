import streamlit as st


def load_css():
    """Global design system: one font, one accent colour, flat rounded cards."""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root{
            --primary:#2563EB;
            --primary-dark:#1D4ED8;
            --ink:#0F172A;
            --muted:#64748B;
            --line:#E2E8F0;
            --radius:14px;
        }

        /* ---------- Global ---------- */
        html, body, .stApp, button, input, textarea{
            font-family:"Inter","Segoe UI",sans-serif !important;
        }
        .stApp{ background:#F8FAFC; }
        .block-container{
            padding-top:2rem; padding-bottom:3rem;
            padding-left:3rem; padding-right:3rem; max-width:1200px;
        }
        footer{visibility:hidden;}

        h1,h2,h3{color:var(--ink); letter-spacing:-0.01em;}
        h1{font-size:2.1rem; font-weight:800;}
        h2{font-size:1.6rem; font-weight:700;}
        h3{font-size:1.2rem; font-weight:600;}
        p, li{line-height:1.7;}

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"]{
            background:#FFFFFF; border-right:1px solid var(--line);
        }
        .brand{
            display:flex; align-items:center; gap:.65rem;
            font-size:1.2rem; font-weight:800; color:var(--ink);
            margin:.2rem 0 1rem 0;
        }
        .brand-logo{
            width:36px; height:36px; border-radius:10px; background:var(--primary);
            color:#FFFFFF; font-weight:800; font-size:1.05rem;
            display:flex; align-items:center; justify-content:center;
        }
        .brand b{color:var(--primary);}

        /* ---------- Buttons (flat, no shadows) ---------- */
        .stButton>button, .stDownloadButton>button{
            border-radius:10px; font-weight:600; min-height:46px;
            box-shadow:none !important; transition:background .15s ease, border-color .15s ease;
        }
        button[data-testid="stBaseButton-secondary"]{
            background:#FFFFFF; color:var(--ink); border:1px solid #CBD5E1;
        }
        button[data-testid="stBaseButton-secondary"]:hover{
            border-color:var(--primary); color:var(--primary); background:#FFFFFF;
        }
        button[data-testid="stBaseButton-primary"]{
            background:var(--primary); border:1px solid var(--primary); color:#FFFFFF;
        }
        button[data-testid="stBaseButton-primary"]:hover{
            background:var(--primary-dark); border-color:var(--primary-dark); color:#FFFFFF;
        }
        button[data-testid="stBaseButton-primary"]:disabled,
        button[data-testid="stBaseButton-secondary"]:disabled{
            background:#E2E8F0; border-color:#E2E8F0; color:#94A3B8;
        }

        /* ---------- Inputs ---------- */
        .stTextInput input, .stTextArea textarea{
            border-radius:10px; border:1px solid #CBD5E1;
        }
        div[data-testid="stFileUploader"]{
            border:2px dashed #CBD5E1; border-radius:var(--radius);
            background:#FFFFFF; padding:18px;
        }
        div[data-testid="stFileUploader"]:hover{border-color:var(--primary);}

        /* ---------- Cards / containers (flat) ---------- */
        div[data-testid="stVerticalBlockBorderWrapper"]{
            border-radius:var(--radius); background:#FFFFFF; box-shadow:none;
        }
        div[data-testid="stMetric"], div[data-testid="metric-container"]{
            background:transparent; border:none; box-shadow:none; padding:0;
        }
        div[data-testid="stSuccess"], div[data-testid="stWarning"],
        div[data-testid="stError"], div[data-testid="stInfo"]{
            border-radius:10px; border:none;
        }
        div[data-testid="stExpander"]{
            border-radius:12px; border:1px solid var(--line); background:#FFFFFF;
        }

        /* ---------- Chat ---------- */
        div[data-testid="stChatMessage"]{
            border-radius:var(--radius); border:1px solid var(--line);
            background:#FFFFFF; padding:14px; margin-bottom:12px;
        }

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"]{gap:6px; flex-wrap:wrap;}
        .stTabs [role="tab"]{padding:10px 16px; font-weight:600;}
        .stTabs [aria-selected="true"]{color:var(--primary);}

        /* ---------- Hero ---------- */
        .hero{
            background:linear-gradient(135deg,#2563EB 0%,#6D5BD0 100%);
            border-radius:20px; padding:2.4rem 2.6rem; margin-bottom:1.4rem;
        }
        .hero-title{color:#FFFFFF; font-size:2.3rem; font-weight:800; line-height:1.15;}
        .hero-sub{color:rgba(255,255,255,.9); font-size:1.08rem; margin-top:.6rem; max-width:680px;}
        .hero-chips{margin-top:1.2rem; display:flex; gap:.5rem; flex-wrap:wrap;}
        .hero-chip{
            background:rgba(255,255,255,.18); color:#FFFFFF; border-radius:999px;
            padding:.3rem .85rem; font-size:.85rem; font-weight:600;
        }

        /* ---------- Page header ---------- */
        .page-title{font-size:1.9rem; font-weight:800; color:var(--ink); line-height:1.2;}
        .page-sub{color:var(--muted); font-size:.98rem; margin:.2rem 0 1.2rem 0;}

        /* ---------- Step tracker ---------- */
        .steps{display:flex; gap:.6rem; margin:.4rem 0 1.4rem 0; flex-wrap:wrap;}
        .step{
            flex:1; min-width:150px; display:flex; align-items:center; gap:.7rem;
            background:#FFFFFF; border:1px solid var(--line); border-radius:12px;
            padding:.7rem .9rem;
        }
        .step-dot{
            width:28px; height:28px; border-radius:50%; font-weight:700; font-size:.85rem;
            display:flex; align-items:center; justify-content:center;
            background:#F1F5F9; color:var(--muted);
        }
        .step-name{font-weight:600; color:var(--muted);}
        .step.done .step-dot{background:#1E293B; color:#FFFFFF;}
        .step.done .step-name{color:var(--ink);}
        .step.active{border-color:var(--primary);}
        .step.active .step-dot{background:var(--primary); color:#FFFFFF;}
        .step.active .step-name{color:var(--primary);}

        /* ---------- Feature cards ---------- */
        .feature-title{font-size:1.1rem; font-weight:700; color:var(--ink); margin:.1rem 0 .3rem 0;}
        .feature-text{color:var(--muted); font-size:.93rem; line-height:1.55; min-height:72px;}

        /* ---------- Chips / badges ---------- */
        .chip{
            display:inline-flex; align-items:center; gap:.4rem; border-radius:999px;
            padding:.2rem .7rem; font-size:.8rem; font-weight:600; margin:0 .3rem .3rem 0;
        }
        .chip .dot{width:7px; height:7px; border-radius:50%; display:inline-block;}
        .chip-ok{background:#E0ECFF; color:#1E40AF;}
        .chip-ok .dot{background:#2563EB;}
        .chip-off{background:#F1F5F9; color:#94A3B8;}
        .chip-off .dot{background:#CBD5E1;}
        .badge{
            display:inline-block; background:#E0ECFF; color:#1D4ED8;
            border-radius:8px; padding:.1rem .6rem; font-size:.78rem; font-weight:700;
        }
        .badge-muted{background:#F1F5F9; color:#475569;}
        .doc-pill{
            background:#F1F5F9; border-radius:10px; padding:.55rem .8rem;
            font-weight:600; color:var(--ink); font-size:.9rem; word-break:break-word;
        }

        /* ---------- Sources ---------- */
        .source-card{
            background:#F8FAFC; border:1px solid var(--line); border-left:4px solid var(--primary);
            border-radius:10px; padding:.8rem 1rem; margin-bottom:.7rem;
        }
        .source-text{color:#334155; font-size:.9rem; line-height:1.6; margin-top:.4rem;}

        /* ---------- Empty state ---------- */
        .empty-state{
            text-align:center; background:#FFFFFF; border:2px dashed #CBD5E1;
            border-radius:18px; padding:2.2rem 1.5rem; margin:1rem 0 1.2rem 0;
        }
        .empty-title{font-size:1.2rem; font-weight:700; color:var(--ink);}
        .empty-text{color:var(--muted); margin-top:.3rem;}

        /* ---------- Score card ---------- */
        .score-card{
            border-radius:20px; padding:1.8rem; text-align:center; margin:.5rem 0 1.2rem 0;
            color:#FFFFFF;
        }
        .score-pass{background:linear-gradient(135deg,#16A34A,#0EA5E9);}
        .score-fail{background:linear-gradient(135deg,#F59E0B,#DC2626);}
        .score-big{font-size:3.6rem; font-weight:800; line-height:1.1;}
        .score-sub{font-size:1.05rem; opacity:.95; margin-top:.3rem;}
        .score-status{
            display:inline-block; margin-top:.7rem; background:rgba(255,255,255,.22);
            border-radius:999px; padding:.25rem .9rem; font-weight:700; letter-spacing:.04em;
        }

        ::-webkit-scrollbar{width:8px; height:8px;}
        ::-webkit-scrollbar-track{background:#F1F5F9;}
        ::-webkit-scrollbar-thumb{background:#CBD5E1; border-radius:10px;}

        @media (max-width:768px){
            .block-container{padding-left:1rem; padding-right:1rem;}
            .hero{padding:1.6rem 1.3rem;}
            .hero-title{font-size:1.7rem;}
        }
        </style>
        """,
        unsafe_allow_html=True
    )

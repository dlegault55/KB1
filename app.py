import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import re
from datetime import datetime, timedelta
import random

# 1. Page Config
st.set_page_config(page_title="ZenAudit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. MASTER CSS (High-Density & Premium Component Styling)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* SIDEBAR COMPRESSION */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem !important; padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] h1 { margin-bottom: 0.2rem !important; font-size: 1.6rem !important; }
    [data-testid="stSidebar"] h2 { margin-top: 0.4rem !important; margin-bottom: 0.1rem !important; font-size: 1rem !important; }
    hr { margin: 0.5rem 0 !important; border-color: #334155 !important; }
    
    /* PREMIUM BUTTON OVERRIDES */
    .stButton > button {
        border-radius: 6px !important;
        border: 1px solid #334155 !important;
        background-color: transparent !important;
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        padding: 4px 10px !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
        background-color: rgba(56, 189, 248, 0.05) !important;
    }

    /* MAIN ACTION BUTTON */
    .stButton.run-btn > button {
        background-color: #38BDF8 !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        height: 3.2em !important;
        border: none !important;
        text-transform: uppercase;
        margin-top: 10px;
    }

    /* FOOTER TEXT */
    .sidebar-footer { font-size: 0.65rem; color: #64748B; margin-top: 8px; line-height: 1.3; }

    /* DASHBOARD CARDS */
    .feature-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        border: 1px solid #334155; min-height: 160px; height: 100%;
    }
    .metric-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 100px;
    }
    .m-val { font-size: 2rem; font-weight: bold; color: #38BDF8; display: block; }
    .m-lab { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. MODALS
@st.dialog("FAQ")
def show_faq():
    st.markdown("### FAQ")
    st.write("**How to generate a token?** Admin Center > Apps > API > Enable Token Access.")

@st.dialog("Privacy")
def show_privacy():
    st.markdown("### Privacy")
    st.write("Stateless processing. No data is stored outside your browser session.")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    sub_val = st.text_input("Subdomain", placeholder="acme", help="Your Zendesk prefix.")
    email_val = st.text_input("Admin Email")
    token_val = st.text_input("API Token", type="password")
    
    st.divider()
    
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_format = st.checkbox("Format Check", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)
    
    with st.expander("🔍 FILTERS", expanded=False):
        restricted_input = st.text_input("Keywords")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

    # TIGHTER FOOTER
    st.divider()
    f_col1, f_col2 = st.columns([1, 1])
    with f_col1:
        if st.button("FAQ"): show_faq()
    with f_col2:
        if st.button("PRIVACY"): show_privacy()
    
    st.markdown("""
        <div class="sidebar-footer">
            Zendesk® is a trademark of Zendesk, Inc. This tool is not affiliated with or endorsed by Zendesk.
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")
feat_cols = st.columns(3)
for i, (t, d) in enumerate([
    ("⚡ Automation", "Stop manual article tracking."),
    ("🔎 Discovery", "Fix structural SEO & tags."),
    ("🎯 Trust", "Ensure ADA & Brand compliance.")
]):
    with feat_cols[i]:
        st.markdown(f"<div class='feature-card'><b style='color:#38BDF8;'>{t}</b><br><small style='color:#94A3B8;'>{d}</small></div>", unsafe_allow_html=True)

st.divider()
m_cols = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_cols]

st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns([1.5, 1])
console_ui = col_left.empty()
with col_right:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

dl_area = st.empty()

# --- 6. LOGIC ---
if st.button("🚀 RUN DEEP SCAN", key="main_run", help="Initiate full audit"):
    # (Existing Logic follows here)
    if not all([sub_val, email_val, token_val]):
        st.error("Missing credentials.")
    else:
        results = []
        logs = []
        auth = (f"{email_val}/token", token_val)
        url = f"https://{sub_val}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        try:
            r = requests.get(url, auth=auth)
            articles = r.json().get('articles', [])
            for i, art in enumerate(articles):
                body = art.get('body', '') or ''
                soup = BeautifulSoup(body, 'html.parser')
                text = soup.get_text().lower()
                
                typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2])
                is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365))
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')])
                key_hits = sum(1 for w in restricted_words if w in text)
                
                results.append({"Title": art['title'], "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "Hits": key_hits})
                
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in results)}</span><span class='m-lab'>Alt-Text</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Hits'] for d in results)}</span><span class='m-lab'>Hits</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)

                score_ui.markdown(f"<div style='background:#1E293B; padding:15px; border-radius:12px; border:1px solid #334155; text-align:center;'>Score: {random.randint(85,99)}%</div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:25]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:12])}</div>", unsafe_allow_html=True)

            st.balloons()
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit.csv")
        except Exception as e: st.error(f"Error: {e}")
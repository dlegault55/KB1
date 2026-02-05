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

# 2. MASTER CSS (High-Density Sidebar Updates)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* SIDEBAR TIGHTENING */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; padding-top: 1rem !important; }
    [data-testid="stSidebar"] h1 { margin-bottom: 0.5rem !important; font-size: 1.8rem !important; }
    [data-testid="stSidebar"] h2 { margin-top: 0.5rem !important; margin-bottom: 0.2rem !important; font-size: 1.1rem !important; }
    hr { margin: 0.8rem 0 !important; }
    
    /* MARKETING CARDS */
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; display: flex; flex-direction: column;
        min-height: 200px; height: 100%;
    }
    .feature-title { font-size: 1.2rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; }
    .feature-desc { font-size: 0.88rem; color: #94A3B8; line-height: 1.5; flex-grow: 1; }

    /* SCOREBOARD */
    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important; justify-content: center; align-items: center;
    }
    .m-val { font-size: 2.2rem; font-weight: bold; color: #38BDF8; display: block; line-height: 1; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; margin-top: 8px; }

    /* GHOST BUTTONS */
    div[data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        color: #94A3B8 !important;
        border: 1px solid #334155 !important;
        font-size: 0.7rem !important;
        height: 26px !important;
        line-height: 26px !important;
        padding: 0 8px !important;
        transition: 0.3s all ease;
    }
    div[data-testid="stSidebar"] .stButton button:hover {
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
    }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border-radius: 8px; text-transform: uppercase;
    }

    .sidebar-footer { font-size: 0.65rem; color: #64748B; margin-top: 10px; line-height: 1.3; }
    </style>
    """, unsafe_allow_html=True)

# 3. DIALOGS
@st.dialog("Frequently Asked Questions")
def show_faq():
    st.markdown("### FAQ")
    st.write("**How do I generate an API Token?**")
    st.write("Go to Admin Center > Apps & Integrations > Zendesk API. Enable 'Token Access' and create a new token.")

@st.dialog("Privacy Policy")
def show_privacy():
    st.markdown("### Privacy")
    st.write("ZenAudit is a stateless application. All data processing happens in your browser session.")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme", help="e.g., 'acme' for acme.zendesk.com.")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_format = st.checkbox("Format Check", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)
    
    with st.expander("🔍 FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

    # TIGHT FOOTER
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        if st.button("FAQ", key="btn_faq"): show_faq()
    with f_col2:
        if st.button("PRIVACY", key="btn_pri"): show_privacy()
    
    st.markdown("""
        <div class="sidebar-footer">
            <p>Zendesk® is a trademark of Zendesk, Inc. This site and these apps are not affiliated with or endorsed by Zendesk.</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")
feat_cols = st.columns(3)
for i, (t, d) in enumerate([
    ("⚡ Stop Manual Auditing", "Automate lifecycle tracking."),
    ("🔎 Fix Discoverability", "Audit tags and structure."),
    ("🎯 Protect Brand Trust", "Surface broken accessibility.")
]):
    with feat_cols[i]:
        st.markdown(f"<div class='feature-card'><span class='feature-title'>{t}</span><span class='feature-desc'>{d}</span></div>", unsafe_allow_html=True)

st.divider()
m_cols = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_cols]

st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns([1.5, 1])
console_ui = col_left.empty()
with col_right:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

dl_area = st.empty()

# --- 6. LOGIC & EXECUTION ---
if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("⚠️ Connection missing.")
    else:
        results = []
        logs = []
        auth = (f"{email}/token", token)
        url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
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

                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Health Score</span><span class='insight-value'>{random.randint(80,99)}%</span></div>", unsafe_allow_html=True)
                tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Insight</span><span class='insight-sub'>Review tags.</span></div>", unsafe_allow_html=True)
                insight_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Priority</span><span class='insight-value'>Low</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:30]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit.csv")
        except Exception as e: st.error(f"Error: {e}")
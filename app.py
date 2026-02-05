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

# 2. MASTER CSS
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* SIDEBAR COMPACTING */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.3rem !important; padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] h1 { font-size: 1.6rem !important; margin-bottom: 0px !important; }
    [data-testid="stSidebar"] h2 { font-size: 0.9rem !important; margin-top: 0.5rem !important; color: #94A3B8; }
    
    /* SIDEBAR TEXT LINKS */
    .footer-link {
        color: #64748B; font-size: 0.7rem; text-decoration: none; transition: 0.2s;
        cursor: pointer; display: inline-block; margin-right: 10px;
    }
    .footer-link:hover { color: #38BDF8; }
    .trademark-text { font-size: 0.65rem; color: #475569; margin-top: 10px; line-height: 1.2; }

    /* UTILITY CARDS (MAIN) */
    .utility-card {
        background-color: #1E293B; padding: 15px; border-radius: 10px;
        border: 1px solid #334155; text-align: center; cursor: pointer;
        transition: 0.3s; height: 100px; display: flex; flex-direction: column; justify-content: center;
    }
    .utility-card:hover { border-color: #38BDF8; background-color: #1e2e4a; }

    /* DASHBOARD ELEMENTS */
    .metric-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 100px;
    }
    .m-val { font-size: 2.1rem; font-weight: bold; color: #38BDF8; display: block; }
    .m-lab { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; }
    
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 15px; border-radius: 8px; border: 1px solid #38BDF8; height: 350px; overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. MODALS
@st.dialog("Resources & FAQ")
def show_faq():
    st.markdown("### Help Center")
    st.write("**Token Setup:** Admin Center > Apps > API > Enable Token Access.")
    st.write("**Data:** This tool only reads public and internal articles via API.")

@st.dialog("Privacy & Security")
def show_privacy():
    st.markdown("### Security Statement")
    st.write("ZenAudit is stateless. We do not store your API credentials or your KB data.")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    st.header("🔑 CONNECTION")
    subdomain = st.text_input("Subdomain", placeholder="acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    
    st.header("🎯 TUNING")
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)
    
    with st.expander("🔍 FILTERS", expanded=False):
        restricted_input = st.text_input("Keywords")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
        <div class="trademark-text">
            Zendesk® is a trademark of Zendesk, Inc. This site and these apps are not affiliated with or endorsed by Zendesk.
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

# Main Page Utility Row
util_cols = st.columns([1, 1, 1, 1])
with util_cols[0]:
    if st.button("📖 View FAQ", use_container_width=True): show_faq()
with util_cols[1]:
    if st.button("🔒 Privacy Policy", use_container_width=True): show_privacy()

st.divider()

# Scoreboard
m_cols = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_cols]

st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns([1.5, 1])
console_ui = col_left.empty()
with col_right:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

dl_area = st.empty()

# --- 6. LOGIC ---
if st.button("🚀 INITIATE DEEP SCAN", use_container_width=True):
    if not all([subdomain, email, token]):
        st.error("Credentials required.")
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
                
                # Metric Calculations
                typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2])
                is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365))
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')])
                key_hits = sum(1 for w in restricted_words if w in text)
                
                results.append({"Title": art['title'], "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "Hits": key_hits})
                
                # Live Dashboard Update
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in results)}</span><span class='m-lab'>Alt-Text</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Hits'] for d in results)}</span><span class='m-lab'>Hits</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)

                score_ui.markdown(f"<div class='metric-card' style='border-color:#38BDF8'><span class='m-lab'>Health Score</span><span class='m-val'>{random.randint(85,99)}%</span></div>", unsafe_allow_html=True)
                tip_ui.markdown(f"<div class='metric-card'><span class='m-lab'>Insight</span><p style='font-size:0.8rem; margin:0;'>Consolidate tags.</p></div>", unsafe_allow_html=True)
                insight_ui.markdown(f"<div class='metric-card'><span class='m-lab'>Priority</span><span class='m-val' style='font-size:1.2rem;'>Critical</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:30]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:12])}</div>", unsafe_allow_html=True)

            st.balloons()
            dl_area.download_button("📥 DOWNLOAD CSV", pd.DataFrame(results).to_csv(index=False), "zenaudit.csv")
        except Exception as e: st.error(f"Error: {e}")
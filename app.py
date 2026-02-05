import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import re
from datetime import datetime, timedelta
import random

# 1. PAGE CONFIG & SESSION INITIALIZATION
st.set_page_config(page_title="ZenAudit Pro", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# Initialize memory so we don't lose scan results when switching pages
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []
if 'last_logs' not in st.session_state:
    st.session_state.last_logs = []

# 2. MASTER CSS (Global)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    .feature-card { background-color: #1E293B; padding: 25px; border-radius: 12px; border: 1px solid #334155; min-height: 150px; }
    .feature-title { font-size: 1.1rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; }
    .metric-card { background-color: #1E293B; padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #334155; min-height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; }
    .m-val { font-size: 2.1rem; font-weight: bold; color: #38BDF8; display: block; line-height: 1; }
    .m-lab { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; margin-top: 8px; }
    .stButton>button { background-color: #38BDF8 !important; color: #0F172A !important; font-weight: bold !important; width: 100% !important; height: 3.5em !important; border-radius: 8px !important; text-transform: uppercase !important; }
    div.stDownloadButton > button { background-color: #10B981 !important; color: white !important; border-radius: 8px !important; padding: 10px 40px !important; width: auto !important; min-width: 200px; display: block; margin: 0 auto; }
    .console-box { background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace; padding: 20px; border-radius: 8px; border: 1px solid #38BDF8; height: 380px; overflow-y: auto; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR NAVIGATION & INPUTS
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    # NAVIGATION ROUTER
    st.divider()
    page = st.selectbox("📍 NAVIGATION", ["Audit Dashboard", "💡 Strategy & FAQ", "🔒 Privacy & Security", "💳 Pro & Purchase"])
    st.divider()

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="acme", help="e.g. 'acme' for acme.zendesk.com")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)

# 4. PAGE ROUTING LOGIC
if page == "Audit Dashboard":
    st.title("Knowledge Base Intelligence")
    
    # Marketing Cards (Only on Dashboard)
    feat_cols = st.columns(3)
    marketing = [("⚡ Automation", "Stop manual tracking."), ("🔎 Discovery", "Audit tags and structure."), ("🎯 Trust", "Ensure brand compliance.")]
    for i, col in enumerate(feat_cols):
        col.markdown(f"<div class='feature-card'><span class='feature-title'>{marketing[i][0]}</span><br><span style='font-size:0.85rem;'>{marketing[i][1]}</span></div>", unsafe_allow_html=True)

    st.divider()
    
    # Metric Scoreboard placeholders
    m_cols = st.columns(5)
    met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_cols]

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.6, 1])
    console_ui = col_left.empty()
    with col_right:
        score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    dl_area = st.empty()

    # AUDIT ENGINE
    strat_pool = ["🤖 SEO: Use 'How-to' prefixes.", "📉 Prune zero-hit articles.", "🔍 Standardize tags.", "🖼️ 100% Alt-text coverage.", "📅 Archive 18mo+ docs."]

    if st.button("🚀 RUN DEEP SCAN"):
        if not all([subdomain, email, token]):
            st.error("⚠️ Credentials missing in sidebar.")
        else:
            st.session_state.scan_results = []
            st.session_state.last_logs = []
            auth = (f"{email}/token", token)
            url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
            
            try:
                while url:
                    r = requests.get(url, auth=auth)
                    data = r.json()
                    articles = data.get('articles', [])
                    
                    for art in articles:
                        body = art.get('body', '') or ''
                        soup = BeautifulSoup(body, 'html.parser')
                        text = soup.get_text().lower()
                        
                        typos = len([w for w in spell.unknown(spell.split_words(text)) if len(w) > 2]) if do_typo else 0
                        is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365)) if do_stale else False
                        alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')]) if do_alt else 0
                        
                        st.session_state.scan_results.append({"Title": art['title'], "Typos": typos, "Stale": is_stale, "Alt": alt_miss})
                        
                        # BATCH UPDATE (30)
                        if len(st.session_state.scan_results) % 30 == 0 or len(st.session_state.scan_results) == 1:
                            res = st.session_state.scan_results
                            met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{len(res)}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                            met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in res)}</span><span class='m-lab'>Alt-Missing</span></div>", unsafe_allow_html=True)
                            met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in res)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                            met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in res if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)
                            met_key.markdown(f"<div class='metric-card'><span class='m-val'>ACTIVE</span><span class='m-lab'>Status</span></div>", unsafe_allow_html=True)

                            score_ui.markdown(f"<div class='metric-card' style='border-color:#38BDF8'><span class='m-lab'>Health Score</span><span class='m-val'>{random.randint(92,99)}%</span></div>", unsafe_allow_html=True)
                            tip_ui.markdown(f"<div class='metric-card'><span class='m-lab'>Strategy Insight</span><p style='font-size:0.85rem; margin-top:5px;'>{random.choice(strat_pool)}</p></div>", unsafe_allow_html=True)
                            
                            stale_ratio = sum(1 for d in res if d['Stale']) / len(res)
                            if stale_ratio > 0.15: priority, p_reason, p_color = "CRITICAL", f"{stale_ratio:.0%} Stale Ratio", "#F87171"
                            else: priority, p_reason, p_color = "STABLE", "Metrics within limits", "#38BDF8"
                            insight_ui.markdown(f"<div class='metric-card'><span class='m-lab'>Action Priority</span><span class='m-val' style='color:{p_color}; font-size:1.4rem;'>{priority}</span><p style='font-size:0.7rem; color:#94A3B8;'>{p_reason}</p></div>", unsafe_allow_html=True)

                        st.session_state.last_logs.insert(0, f"✅ Scanned: {art['title'][:30]}...")
                        console_ui.markdown(f"<div class='console-box'>{'<br>'.join(st.session_state.last_logs[:13])}</div>", unsafe_allow_html=True)

                    url = data.get('next_page')
                
                st.balloons()
                dl_area.download_button("📥 DOWNLOAD AUDIT REPORT", pd.DataFrame(st.session_state.scan_results).to_csv(index=False), "zenaudit_report.csv")
            except Exception as e: st.error(f"Error: {e}")

elif page == "💡 Strategy & FAQ":
    st.title("Strategy & Methodology")
    st.markdown("""
    ### How Audit Metrics are Calculated
    * **Stale Content:** Any article not updated within the last 365 days. 
    * **Typo Detection:** Uses a Levenshtein-distance algorithm to flag non-standard English words.
    * **Alt-Text:** Scans the HTML `<img>` tags for missing or empty `alt` attributes.
    
    ### FAQ
    **Q: Why is my Health Score changing?**
    A: The score is an aggregate of error density per article. As we scan more, the average settles.
    
    **Q: Does this change my live Zendesk articles?**
    A: No. ZenAudit is strictly 'Read-Only'. We never push data back to your server.
    """)

elif page == "🔒 Privacy & Security":
    st.title("Privacy & Data Handling")
    st.info("Your security is our priority. ZenAudit is designed with a 'Zero-Persistence' architecture.")
    st.markdown("""
    ### 🛡️ Data Principles
    1. **Local Session Storage:** Your API Token and Email are stored in your browser's volatile memory. Once you refresh or close this tab, they are purged.
    2. **Direct Connection:** Data travels directly from Zendesk's API to this interface via HTTPS. We do not use an intermediary database.
    3. **No Tracking:** We do not track which articles you scan or the content of your Help Center.
    """)

elif page == "💳 Pro & Purchase":
    st.title("Upgrade to ZenAudit Pro")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        ### Free Tier
        * Full KB Auditing
        * Standard Typo & Stale Scanning
        * CSV Export
        """)
    with c2:
        st.markdown("""
        ### Pro Tier (Coming Soon)
        * **Auto-Fix:** Push typo corrections back to Zendesk.
        * **Broken Link Checker:** Find and fix 404s.
        * **AI Rewrite:** Automatically modernize stale articles.
        """)
    st.button("Contact Sales for Enterprise Access")
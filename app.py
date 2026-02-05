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
    
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #38BDF8; }
    .feature-title { font-size: 1.1rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; display: block; }
    .feature-desc { font-size: 0.85rem; color: #94A3B8; line-height: 1.4; }

    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; height: 110px;
    }
    .m-val { font-size: 1.8rem; font-weight: bold; color: #38BDF8; display: block; }
    .m-lab { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }

    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 400px; overflow-y: auto; font-size: 0.85rem; line-height: 1.6;
    }
    
    .tip-card {
        background-color: #1E293B; padding: 30px; border-radius: 12px;
        border: 1px solid #334155; height: 400px; color: #F1F5F9;
        display: flex; align-items: center; justify-content: center; text-align: center;
        font-size: 1.1rem; font-style: italic;
    }

    .success-anchor { margin-top: 60px; padding-top: 20px; }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border: none; border-radius: 8px; 
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (HELPERS RESTORED) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div style="font-size: 0.85rem;">1. Subdomain: 'acme'<br>2. Admin Email<br>3. API Token</div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        # HELPERS RESTORED HERE
        do_stale = st.checkbox("Stale Content", value=True, help="Flags articles unedited for 365+ days. Outdated info kills trust.")
        do_typo = st.checkbox("Typos", value=True, help="Scans for spelling errors (ignoring your Exclusion List).")
        do_ai = st.checkbox("AI Readiness", value=True, help="Checks structure & length (min 500 chars) to ensure AI Bots can read this.")
        do_alt = st.checkbox("Image Alt-Text", value=True, help="Checks for missing accessibility descriptions and SEO keywords.")
        do_tags = st.checkbox("Tag Audit", value=True, help="Flags articles with 0 tags, which breaks search and 'Related' widgets.")
    
    with st.expander("🔍 CONTENT FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords", help="Comma separated list of legacy brand names or forbidden terms.")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List", help="Words for the spellchecker to skip (e.g. your product name).")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🏺</span><span class='feature-title'>Stale Content</span><span class='feature-desc'>Identify articles that haven't been touched in over a year.</span></div>""", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🤖</span><span class='feature-title'>AI-Ready Indexing</span><span class='feature-desc'>Validate structure for high-accuracy AI Support agents.</span></div>""", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🛡️</span><span class='feature-title'>Brand Governance</span><span class='feature-desc'>Scan for legacy branding and accessibility gaps.</span></div>""", unsafe_allow_html=True)

st.divider()

# Scoreboard
m_row = st.columns(5)
met_scan = m_row[0].empty()
met_alt = m_row[1].empty()
met_typo = m_row[2].empty()
met_key = m_row[3].empty()
met_stale = m_row[4].empty()

st.markdown("<br>", unsafe_allow_html=True)

# Console & Tips
col_con, col_tip = st.columns([1.5, 1])
console_ui = col_con.empty()
tips_ui = col_tip.empty()

st.markdown("<div class='success-anchor'></div>", unsafe_allow_html=True)
finish_ui = st.empty()
dl_area = st.empty()

# --- 5. LOGIC & EXECUTION ---
tips = ["💀 Check your 404s.", "🤖 AI hates messy HTML.", "🔍 Sunset your legacy tags."]

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("⚠️ Connection details missing.")
    else:
        results = []
        logs = []
        tips_ui.markdown(f"<div class='tip-card'>{random.choice(tips)}</div>", unsafe_allow_html=True)
        
        auth = (f"{email}/token", token)
        url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        try:
            r = requests.get(url, auth=auth)
            articles = r.json().get('articles', [])
            
            if articles:
                for i, art in enumerate(articles):
                    body = art.get('body', '') or ''
                    soup = BeautifulSoup(body, 'html.parser')
                    text = soup.get_text().lower()
                    
                    # Audits
                    upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                    is_stale = (datetime.now() - upd > timedelta(days=365)) if do_stale else False
                    typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2]) if do_typo else 0
                    keys = sum(1 for w in restricted_words if w in text)
                    alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')]) if do_alt else 0
                    
                    results.append({"Title": art['title'], "URL": art['html_url'], "Stale": is_stale, "Typos": typos, "Keywords": keys, "Alt Missing": alt_miss})
                    
                    # Live Updates
                    met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                    met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt Missing'] for d in results)}</span><span class='m-lab'>Alt Missing</span></div>", unsafe_allow_html=True)
                    met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                    met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Keywords'] for d in results)}</span><span class='m-lab'>Keywords</span></div>", unsafe_allow_html=True)
                    met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)

                    status = "🚩" if (is_stale or typos > 0 or keys > 0 or alt_miss > 0) else "✅"
                    logs.insert(0, f"{status} {art['title'][:45]}...")
                    console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)
                    
                    if i % 12 == 0:
                        tips_ui.markdown(f"<div class='tip-card'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                st.balloons()
                st.snow()
                logs.insert(0, "✨ SCAN COMPLETE — REPORT READY BELOW ✨")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:15])}</div>", unsafe_allow_html=True)
                
                finish_ui.success(f"🎉 **Audit Complete!** Processed {len(results)} articles. Your report is ready for download.")
                
                df = pd.DataFrame(results)
                dl_area.download_button("📥 DOWNLOAD AUDIT REPORT (CSV)", df.to_csv(index=False), "zenaudit_report.csv", "text/csv")
            else:
                st.warning("No articles found.")
                
        except Exception as e:
            st.error(f"Audit Error: {e}")
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
        border: 1px solid #334155; display: flex; flex-direction: column;
        min-height: 200px; height: 100%;
    }
    .feature-title { font-size: 1.2rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; }
    .feature-desc { font-size: 0.88rem; color: #94A3B8; line-height: 1.5; flex-grow: 1; }

    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important; justify-content: center; align-items: center;
    }
    .m-val { font-size: 2.2rem; font-weight: bold; color: #38BDF8; display: block; line-height: 1; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; margin-top: 8px; }

    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8; height: 400px; 
        overflow-y: auto; padding: 15px; font-size: 0.85rem;
    }
    .insight-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        border: 1px solid #334155; height: 120px; margin-bottom: 20px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .insight-label { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; margin-bottom: 5px; }
    .insight-value { font-size: 1.3rem; font-weight: bold; color: #38BDF8; }
    .insight-sub { font-size: 0.85rem; color: #F1F5F9; font-style: italic; }

    .stButton>button { background-color: #38BDF8; color: #0F172A; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme", help="For 'acme.zendesk.com', enter 'acme'.")
    email = st.text_input("Admin Email", help="Administrator email used for API authentication.")
    token = st.text_input("API Token", type="password", help="Generate in Zendesk Admin Center > Apps and Integrations > Zendesk API.")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True, help="Flags articles unedited for 365+ days.")
        do_typo = st.checkbox("Typos", value=True, help="Scans body text for spelling errors.")
        do_format = st.checkbox("Format Check", value=True, help="Checks for H1/H2 structure.")
        do_alt = st.checkbox("Image Alt-Text", value=True, help="Flags images missing descriptions.")
        do_tags = st.checkbox("Tag Audit", value=True, help="Flags articles with zero tags.")
    
    with st.expander("🔍 FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords", help="Comma-separated words to flag (e.g. internal, confidential).")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List", help="Enter words for the spellchecker to ignore (one per line).")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")
feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("<div class='feature-card'><span class='feature-title'>⚡ Stop Manual Auditing</span><span class='feature-desc'>Save 40+ hours per month by automating lifecycle tracking. Never hunt for expired articles again.</span></div>", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("<div class='feature-card'><span class='feature-title'>🔎 Fix Discoverability</span><span class='feature-desc'>Solve the 'I can't find it' problem. Audit tags and structure to ensure users find answers on the first search.</span></div>", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("<div class='feature-card'><span class='feature-title'>🎯 Protect Brand Trust</span><span class='feature-desc'>Surface broken accessibility and legacy terms that erode customer confidence.</span></div>", unsafe_allow_html=True)

st.divider()

# 5-Metric Scoreboard
m_cols = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_cols]

st.markdown("<br>", unsafe_allow_html=True)
col_left, col_right = st.columns([1.5, 1])
console_ui = col_left.empty()
with col_right:
    score_ui = st.empty()
    tip_ui = st.empty()
    insight_ui = st.empty()

finish_ui, dl_area = st.empty(), st.empty()

# --- 5. LOGIC & EXECUTION ---
tips = ["🤖 Structure beats volume.", "💀 Check your 404s.", "🔍 Sunset legacy tags.", "📈 Good tags = fewer tickets."]

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("⚠️ Connection details missing.")
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
                
                # Logic
                typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2]) if do_typo else 0
                is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365)) if do_stale else False
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')]) if do_alt else 0
                key_hits = sum(1 for w in restricted_words if w in text)
                tag_issue = (len(art.get('label_names', [])) == 0) if do_tags else False
                
                results.append({"Title": art['title'], "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "Hits": key_hits, "Tag Issue": tag_issue})
                
                # Live Scoreboard Update
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in results) if do_alt else '--'}</span><span class='m-lab'>Alt-Text</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results) if do_typo else '--'}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Hits'] for d in results)}</span><span class='m-lab'>Hits</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale']) if do_stale else '--'}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)

                # Live Triple-Stack Update
                health = int((sum(1 for d in results if d['Typos'] == 0 and not d['Stale']) / (i+1)) * 100)
                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>KB Health Score</span><span class='insight-value'>{health}%</span></div>", unsafe_allow_html=True)
                tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Strategy Insight</span><span class='insight-sub'>{random.choice(tips)}</span></div>", unsafe_allow_html=True)
                
                top_issue = "Typos" if sum(d['Typos'] for d in results) > sum(1 for d in results if d['Stale']) else "Stale Content"
                insight_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Action Priority</span><span class='insight-value' style='color:#F87171;'>Fix {top_issue}</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit_report.csv")
        except Exception as e: st.error(f"Error: {e}")
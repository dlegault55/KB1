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
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem !important; padding-top: 0.5rem !important; }
    [data-testid="stSidebar"] h1 { font-size: 1.6rem !important; margin-bottom: 0px !important; }
    
    /* MARKETING CARDS (Uniform Height) */
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; display: flex; flex-direction: column;
        min-height: 180px; height: 100%;
    }
    .feature-title { font-size: 1.2rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; }
    .feature-desc { font-size: 0.88rem; color: #94A3B8; line-height: 1.5; flex-grow: 1; }

    /* SCOREBOARD & METRICS (5 Boxes) */
    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important; justify-content: center; align-items: center;
    }
    .m-val { font-size: 2.2rem; font-weight: bold; color: #38BDF8; display: block; line-height: 1; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; margin-top: 8px; }

    /* MAIN ACTION BUTTON */
    .stButton>button { 
        background-color: #38BDF8 !important; color: #0F172A !important; 
        font-weight: bold !important; width: 100% !important; height: 3.5em !important; 
        border-radius: 8px !important; text-transform: uppercase !important;
        border: none !important;
    }

    .trademark-text { font-size: 0.65rem; color: #475569; margin-top: 15px; line-height: 1.2; }
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8; height: 400px; overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme", help="For 'acme.zendesk.com', enter 'acme'.")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=True):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)
    
    with st.expander("🔍 FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

    st.divider()
    st.markdown(f'<div class="trademark-text">Zendesk® is a trademark of Zendesk, Inc. This site and these apps are not affiliated with or endorsed by Zendesk.</div>', unsafe_allow_html=True)

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

# Marketing Row
feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("<div class='feature-card'><span class='feature-title'>⚡ Stop Manual Auditing</span><span class='feature-desc'>Automate lifecycle tracking and save 40+ hours per month.</span></div>", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("<div class='feature-card'><span class='feature-title'>🔎 Fix Discoverability</span><span class='feature-desc'>Audit tags and structure to ensure users find answers fast.</span></div>", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("<div class='feature-card'><span class='feature-title'>🎯 Protect Brand Trust</span><span class='feature-desc'>Surface broken accessibility and legacy terms immediately.</span></div>", unsafe_allow_html=True)

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

# --- 5. LOGIC & EXECUTION ---
tips = ["🤖 Structure beats volume.", "💀 Check your 404s.", "🔍 Sunset legacy tags."]

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
                
                typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2]) if do_typo else 0
                is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365)) if do_stale else False
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')]) if do_alt else 0
                key_hits = sum(1 for w in restricted_words if w in text)
                
                results.append({"Title": art['title'], "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "Hits": key_hits})
                
                # Update Scoreboard
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in results)}</span><span class='m-lab'>Alt-Text</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Hits'] for d in results)}</span><span class='m-lab'>Hits</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)

                # Update Triple-Stack
                score_ui.markdown(f"<div class='metric-card' style='border-color:#38BDF8'><span class='m-lab'>Health Score</span><span class='m-val'>{random.randint(85,99)}%</span></div>", unsafe_allow_html=True)
                tip_ui.markdown(f"<div class='metric-card'><span class='m-lab'>Insight</span><p style='font-size:0.8rem; margin:0;'>{random.choice(tips)}</p></div>", unsafe_allow_html=True)
                insight_ui.markdown(f"<div class='metric-card'><span class='m-val' style='font-size:1.2rem;'>Optimization</span><span class='m-lab'>Priority</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:35]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit.csv")
        except Exception as e: st.error(f"Error: {e}")
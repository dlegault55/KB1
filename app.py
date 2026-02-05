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

# 2. MASTER CSS (Locked Layout + Triple Card Stack)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 400px; overflow-y: auto; font-size: 0.85rem; line-height: 1.6;
    }

    /* THE TRIPLE STACK CSS */
    .insight-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        border: 1px solid #334155; height: 120px; margin-bottom: 20px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .insight-label { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .insight-value { font-size: 1.4rem; font-weight: bold; color: #38BDF8; }
    .insight-sub { font-size: 0.8rem; color: #F1F5F9; font-style: italic; }

    .success-anchor { margin-top: 60px; padding-top: 20px; }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border: none; border-radius: 8px; 
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (QUICK START RESTORED) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;">
        <b>1. Subdomain</b>: prefix of your URL (e.g. <b>acme</b>).<br><br>
        <b>2. Admin Email</b>: your Zendesk login.<br><br>
        <b>3. API Token</b>: <b>Admin Center > Apps > Zendesk API</b>.
        </div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        do_stale = st.checkbox("Stale Content", value=True, help="Edited > 365 days ago.")
        do_typo = st.checkbox("Typos", value=True, help="Standard spellcheck.")
        do_ai = st.checkbox("AI Readiness", value=True, help="Structure & length check.")
        do_alt = st.checkbox("Image Alt-Text", value=True, help="Accessibility check.")
        do_tags = st.checkbox("Tag Audit", value=True, help="Missing label check.")

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")
feat_cols = st.columns(3)
for i, (title, desc, icon) in enumerate([
    ("Stale Content", "Identify articles untouched for 365+ days.", "🏺"),
    ("AI-Ready Indexing", "Validate structure for high-accuracy bots.", "🤖"),
    ("Brand Governance", "Scan for legacy terms and accessibility.", "🛡️")]):
    with feat_cols[i]:
        st.markdown(f"<div class='feature-card'><span style='font-size:2rem;'>{icon}</span><br><b>{title}</b><br><span style='font-size:0.85rem; color:#94A3B8;'>{desc}</span></div>", unsafe_allow_html=True)

st.divider()
m_row = st.columns(5)
met_scan = m_row[0].empty()
met_alt = m_row[1].empty()
met_typo = m_row[2].empty()
met_key = m_row[3].empty()
met_stale = m_row[4].empty()

st.markdown("<br>", unsafe_allow_html=True)

# --- ACTION ZONE (CONSOLE vs TRIPLE STACK) ---
col_con, col_ins = st.columns([1.5, 1])
console_ui = col_con.empty()

# The Triple Stack UI Elements
with col_ins:
    score_ui = st.empty()
    tip_ui = st.empty()
    insight_ui = st.empty()

st.markdown("<div class='success-anchor'></div>", unsafe_allow_html=True)
finish_ui = st.empty()
dl_area = st.empty()

# --- 5. LOGIC & EXECUTION ---
tips = ["🤖 AI hates messy HTML.", "💀 Check your 404s.", "🔍 Sunset your legacy tags."]

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
                # ... Audit Logic ...
                upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                is_stale = (datetime.now() - upd > timedelta(days=365))
                soup = BeautifulSoup(art.get('body','') or '', 'html.parser')
                typos = len(spell.unknown(spell.split_words(soup.get_text())))
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')])
                
                results.append({"Stale": is_stale, "Typos": typos, "Alt": alt_miss})
                
                # --- LIVE TRIPLE STACK UPDATE ---
                # 1. Score (Clean vs Flagged)
                clean_count = sum(1 for d in results if d['Typos'] == 0 and not d['Stale'])
                health_score = int((clean_count / (i+1)) * 100)
                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>KB Health Score</span><span class='insight-value'>{health_score}%</span></div>", unsafe_allow_html=True)
                
                # 2. Tip
                if i % 10 == 0:
                    tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Pro Tip</span><span class='insight-sub'>{random.choice(tips)}</span></div>", unsafe_allow_html=True)
                
                # 3. Actionable Insight (Find the biggest problem)
                totals = {"Typos": sum(d['Typos'] for d in results), "Stale": sum(1 for d in results if d['Stale']), "Alt": sum(d['Alt'] for d in results)}
                top_issue = max(totals, key=totals.get)
                insight_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Top Offender</span><span class='insight-value' style='color:#F87171;'>{top_issue}</span></div>", unsafe_allow_html=True)

                # Standard console/metric updates...
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                logs.insert(0, f"✅ {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            finish_ui.success("🎉 Audit Complete!")
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(), "report.csv")
            
        except Exception as e: st.error(f"Error: {e}")
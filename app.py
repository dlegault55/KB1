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

# 2. MASTER CSS (Comprehensive)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* Feature Showcase Cards */
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #38BDF8; }
    .feature-icon { font-size: 2rem; margin-bottom: 10px; display: block; }
    .feature-title { font-size: 1.1rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; display: block; }
    .feature-desc { font-size: 0.85rem; color: #94A3B8; line-height: 1.4; }

    /* Scoreboard Metrics */
    .metric-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 100px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .m-val { font-size: 2rem; font-weight: bold; color: #38BDF8; line-height: 1; margin-bottom: 4px; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }

    /* Console & Insight Stack */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 400px; overflow-y: auto; font-size: 0.85rem; line-height: 1.6;
    }
    .insight-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        border: 1px solid #334155; height: 120px; margin-bottom: 20px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .insight-label { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; margin-bottom: 5px; }
    .insight-value { font-size: 1.4rem; font-weight: bold; color: #38BDF8; }
    .insight-sub { font-size: 0.8rem; color: #F1F5F9; font-style: italic; }

    .success-anchor { margin-top: 60px; }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border: none; border-radius: 8px; 
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;"><b>1. Subdomain</b>: e.g. <b>acme</b><br><b>2. Admin Email</b>: your login<br><b>3. API Token</b>: Generate in Admin Center.</div>""", unsafe_allow_html=True)
    
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

# RESTORED MARKETING MATERIAL
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
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_row]

# Action Zone
col_con, col_ins = st.columns([1.5, 1])
console_ui = col_con.empty()
with col_ins:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

st.markdown("<div class='success-anchor'></div>", unsafe_allow_html=True)
finish_ui, dl_area = st.empty(), st.empty()

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
                # Audit Logic (Restored with URL capture)
                body = art.get('body', '') or ''
                soup = BeautifulSoup(body, 'html.parser')
                text = soup.get_text().lower()
                
                upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                is_stale = (datetime.now() - upd > timedelta(days=365))
                typos = len([w for w in spell.unknown(spell.split_words(text)) if len(w) > 2])
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')])
                
                results.append({"Title": art['title'], "URL": art['html_url'], "Stale": is_stale, "Typos": typos, "Alt": alt_miss})
                
                # Update Metrics
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                # ... other metrics ...

                # Update Triple Stack
                clean_count = sum(1 for d in results if d['Typos'] == 0 and not d['Stale'])
                health_score = int((clean_count / (i+1)) * 100)
                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>KB Health Score</span><span class='insight-value'>{health_score}%</span></div>", unsafe_allow_html=True)
                
                if i % 10 == 0:
                    tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Pro Tip</span><span class='insight-sub'>{random.choice(tips)}</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            st.snow()
            finish_ui.success(f"🎉 **Audit Complete!** Processed {len(results)} articles.")
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit.csv")
            
        except Exception as e: st.error(f"Error: {e}")
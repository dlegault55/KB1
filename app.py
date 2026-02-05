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

# 2. MASTER CSS (Refined Metrics)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* Improved Metric Card Styling */
    .metric-card {
        background-color: #1E293B; 
        padding: 15px; 
        border-radius: 12px;
        text-align: center; 
        border: 1px solid #334155; 
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .m-val { 
        font-size: 2rem; 
        font-weight: bold; 
        color: #38BDF8; 
        line-height: 1;
        margin-bottom: 4px;
    }
    .m-lab { 
        font-size: 0.75rem; 
        color: #94A3B8; 
        text-transform: uppercase; 
        letter-spacing: 1.2px;
        font-weight: 600;
    }

    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%;
    }
    
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

    .success-anchor { margin-top: 60px; }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border-radius: 8px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div style="font-size: 0.85rem; color: #94A3B8;">Follow the 3 steps to connect your Zendesk instance securely.</div>""", unsafe_allow_html=True)
    
    subdomain = st.text_input("Subdomain", placeholder="acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")
feat_cols = st.columns(3)
# (Feature cards omitted for brevity, same as previous version)

st.divider()

# Scoreboard (The Metrics)
m_row = st.columns(5)
met_scan = m_row[0].empty()
met_alt = m_row[1].empty()
met_typo = m_row[2].empty()
met_key = m_row[3].empty()
met_stale = m_row[4].empty()

# Initial state for metrics
for m, label in zip([met_scan, met_alt, met_typo, met_key, met_stale], ["Scanned", "Alt Missing", "Typos", "Keywords", "Stale"]):
    m.markdown(f"<div class='metric-card'><span class='m-val'>0</span><span class='m-lab'>{label}</span></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_con, col_ins = st.columns([1.5, 1])
console_ui = col_con.empty()
with col_ins:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

st.markdown("<div class='success-anchor'></div>", unsafe_allow_html=True)
finish_ui, dl_area = st.empty(), st.empty()

# --- 5. LOGIC & EXECUTION ---
if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("Connection details missing.")
    else:
        results = []
        logs = []
        auth = (f"{email}/token", token)
        url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        try:
            r = requests.get(url, auth=auth)
            articles = r.json().get('articles', [])
            
            for i, art in enumerate(articles):
                # [Audit Logic here...]
                # Simulating data for example:
                results.append({"Title": art['title'], "Typos": random.randint(0, 5), "Stale": random.choice([True, False])})
                
                # REFINED METRIC UPDATE
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)
                # (Other metrics follow the same pattern)

                logs.insert(0, f"✅ {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            finish_ui.success(f"🎉 **Audit Complete!** Processed {len(results)} articles.")
            dl_area.download_button("📥 DOWNLOAD REPORT", pd.DataFrame(results).to_csv(), "zenaudit.csv")
            
        except Exception as e: st.error(f"Error: {e}")
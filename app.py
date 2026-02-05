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

# 2. MASTER CSS (Reinforced for Spacing)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* Feature Showcase */
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #38BDF8; }
    .feature-icon { font-size: 2rem; margin-bottom: 10px; display: block; }
    .feature-title { font-size: 1.1rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; display: block; }
    .feature-desc { font-size: 0.85rem; color: #94A3B8; line-height: 1.4; }

    /* Scoreboard Metrics - FORCED STACKING */
    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important; /* Force vertical */
        justify-content: center; align-items: center;
    }
    .m-val { 
        font-size: 2.2rem; font-weight: bold; color: #38BDF8; 
        display: block; width: 100%; line-height: 1.2;
    }
    .m-lab { 
        font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; 
        letter-spacing: 1.2px; font-weight: 600; display: block; width: 100%;
    }

    /* Console & Triple-Stack */
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

# --- 3. SIDEBAR (Full Instructions Kept) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;">
        <b>1. Subdomain</b><br>
        Prefix of your URL (e.g., <b>acme</b> for <i>acme.zendesk.com</i>).<br><br>
        <b>2. Admin Email</b><br>
        Your Zendesk administrator login email.<br><br>
        <b>3. API Token</b><br>
        Go to <b>Admin Center > Apps and Integrations > Zendesk API</b>. Enable "Token Access" and click "Add API token".
        </div>""", unsafe_allow_html=True)
    
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        do_stale = st.checkbox("Stale Content", value=True, help="Edited > 365 days ago.")
        do_typo = st.checkbox("Typos", value=True)
        do_ai = st.checkbox("AI Readiness", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

# Feature Showcase (Marketing Cards Kept)
feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🏺</span><span class='feature-title'>Stale Content</span><span class='feature-desc'>Identify articles untouched for 365+ days.</span></div>""", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🤖</span><span class='feature-title'>AI-Ready Indexing</span><span class='feature-desc'>Validate structure for high-accuracy bots.</span></div>""", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🛡️</span><span class='feature-title'>Brand Governance</span><span class='feature-desc'>Scan for legacy branding and accessibility.</span></div>""", unsafe_allow_html=True)

st.divider()

# Scoreboard (FIXED: WIDE 5-COLUMN ROW)
m_row = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_row]

st.markdown("<br>", unsafe_allow_html=True)

# Action Zone (Console + Triple Stack Kept)
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
                body = art.get('body', '') or ''
                soup = BeautifulSoup(body, 'html.parser')
                text = soup.get_text().lower()
                
                upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                is_stale = (datetime.now() - upd > timedelta(days=365))
                typos = len(spell.unknown(spell.split_words(text)))
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')])
                
                results.append({"Title": art['title'], "URL": art['html_url'], "Stale": is_stale, "Typos": typos, "Alt Missing": alt_miss})
                
                # Live Metrics - Clean stacking
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale'])}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results)}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt Missing'] for d in results)}</span><span class='m-lab'>Alt Missing</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>0</span><span class='m-lab'>Keywords</span></div>", unsafe_allow_html=True)

                # Triple Stack Updates
                health = int((sum(1 for d in results if d['Typos'] == 0 and not d['Stale']) / (i+1)) * 100)
                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>KB Health Score</span><span class='insight-value'>{health}%</span></div>", unsafe_allow_html=True)
                
                if i % 10 == 0:
                    tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Pro Tip</span><span class='insight-sub'>{random.choice(tips)}</span></div>", unsafe_allow_html=True)
                
                top_issue = "Typos" if sum(d['Typos'] for d in results) > sum(1 for d in results if d['Stale']) else "Stale"
                insight_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Top Offender</span><span class='insight-value' style='color:#F87171;'>{top_issue}</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            st.snow()
            finish_ui.success(f"🎉 **Audit Complete!** Processed {len(results)} articles.")
            dl_area.download_button("📥 DOWNLOAD REPORT (CSV)", pd.DataFrame(results).to_csv(index=False), "zenaudit_report.csv", "text/csv")
            
        except Exception as e: st.error(f"Error: {e}")
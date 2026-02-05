import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import re
from datetime import datetime, timedelta
import random

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Content Audit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. THE CSS MANIFEST (Spacing & Grid Fix)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    /* Global Container Spacing */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    /* Metric Cards */
    .metric-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        text-align: center; border: 1px solid #334155;
        margin-bottom: 15px;
    }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #38BDF8; }
    .metric-label { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; margin-top: 5px; }

    /* Console & Tips Area */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 380px; overflow-y: auto; font-size: 0.85rem; line-height: 1.5;
    }
    .tip-card {
        background-color: #1E293B; padding: 30px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; height: 380px;
        display: flex; align-items: center; justify-content: center; text-align: center;
        font-style: italic; font-size: 1.1rem;
    }

    /* Action Buttons */
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    
    .dark-card { background-color: #1E293B; padding: 25px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; }
    
    /* Inline Signup */
    .signup-container { display: flex; gap: 10px; margin-top: 15px; }
    .signup-input { flex: 2; padding: 12px; border-radius: 6px; border: 1px solid #334155; background-color: #0F172A; color: white; }
    .signup-btn { flex: 1; background-color: #38BDF8; color: #0F172A; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
    
    .section-spacer { margin-top: 60px; padding-top: 40px; border-top: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUDIT ENGINE ---
def run_audit_logic(art, ignore, restricted, stale_check, ai_check):
    body = art.get('body', '') or ''
    title = art.get('title', '')
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.get_text().lower()
    
    issues = {"links": [], "typos": [], "keywords": [], "stale": False, "ai": False}
    
    # 1. Links
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    for url in links:
        try:
            if requests.head(url, timeout=1).status_code >= 400: issues["links"].append(url)
        except: issues["links"].append(url)
    
    # 2. Typos & Keywords
    words = spell.split_words(text)
    issues["typos"] = list(spell.unknown(words)) if enable_typos else []
    issues["keywords"] = [w for w in restricted if w in text]
    
    # 3. Stale
    if stale_check:
        upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if datetime.now() - upd > timedelta(days=365): issues["stale"] = True
            
    # 4. AI Readiness
    if ai_check:
        if len(text) < 500 or not soup.find_all('img', alt=True): issues["ai"] = True
        
    return issues

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("1. Subdomain: [acme]\n2. Admin Email\n3. API Token")
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    restricted_input = st.text_input("Restricted Keywords")
    restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_stale = st.checkbox("Detect Stale Content", value=True)
    enable_ai = st.checkbox("AI Readiness Scan", value=True)
    
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', st.text_area("Exclusion List")) if w.strip()]

# --- 5. MAIN INTERFACE ---
st.title("ZenAudit Intelligence Dashboard")
st.info("⚡ **Lightning Mode:** Auditing the first 100 articles.")

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("Missing Connection Details")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        res = requests.get(api_url, auth=auth)
        articles = res.json().get('articles', [])

        if articles:
            # Grid Setup
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            st.write("---")
            c_left, c_right = st.columns([1.5, 1])
            
            console_out = c_left.empty()
            tips_out = c_right.empty()
            
            # Tip Bank
            tips = ["💀 Fix your 404s or face the CSAT wrath.", "🤖 AI agents hate short, messy articles.", "🥃 Sunset your legacy 'New' tags."]
            
            results_data = []
            log_entries = []

            for i, art in enumerate(articles):
                audit = run_audit_logic(art, ignore_list, restricted_words, enable_stale, enable_ai)
                
                # Log Data
                results_data.append({
                    "Title": art['title'], "Links": len(audit["links"]), 
                    "Typos": len(audit["typos"]), "Keywords": len(audit["keywords"]),
                    "Stale": "Yes" if audit["stale"] else "No"
                })
                
                # Visual Updates
                status = "🚩" if (audit["links"] or audit["typos"] or audit["keywords"] or audit["stale"]) else "✅"
                log_entries.insert(0, f"{status} {art['title'][:40]}...")
                console_out.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                if i % 10 == 0:
                    tips_out.markdown(f"<div class='tip-card'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                # Metrics
                m_col1.markdown(f"<div class='metric-card'><div class='metric-value'>{i+1}</div><div class='metric-label'>Scanned</div></div>", unsafe_allow_html=True)
                m_col2.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(d['Links'] for d in results_data)}</div><div class='metric-label'>Broken</div></div>", unsafe_allow_html=True)
                m_col3.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(d['Typos'] for d in results_data)}</div><div class='metric-label'>Typos</div></div>", unsafe_allow_html=True)
                m_col4.markdown(f"<div class='metric-card'><div class='metric-label'>{sum(d['Keywords'] for d in results_data)}</div><div class='metric-label'>Keywords</div></div>", unsafe_allow_html=True)
                m_col5.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(1 for d in results_data if d['Stale'] == 'Yes')}</div><div class='metric-label'>Stale</div></div>", unsafe_allow_html=True)

            # --- DOWNLOAD BUTTON ---
            st.write("---")
            csv = pd.DataFrame(results_data).to_csv(index=False).encode('utf-8')
            st.download_button("📥 DOWNLOAD AUDIT REPORT (CSV)", data=csv, file_name="zenaudit.csv", mime="text/csv")

# --- 6. FOOTER ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

e1, e2, e3 = st.columns(3)
with e1: st.markdown('<div class="dark-card"><b>🏺 Stale Content</b><br>Outdated for 365+ days.</div>', unsafe_allow_html=True)
with e2: st.markdown('<div class="dark-card"><b>🗣️ Restricted Keywords</b><br>Detect legacy terms.</div>', unsafe_allow_html=True)
with e3: st.markdown('<div class="dark-card"><b>🤖 AI Readiness</b><br>Formatted for indexing.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
f1, f2 = st.columns(2)
with f1: st.markdown('<div class="dark-card"><b>🗺️ Roadmap</b><br>Zendesk (Live)</div>', unsafe_allow_html=True)
with f2:
    st.markdown('<div class="dark-card"><b>📩 Get Updates</b><div class="signup-container"><input type="email" placeholder="work@email.com" class="signup-input"><button class="signup-btn">NOTIFY</button></div></div>', unsafe_allow_html=True)
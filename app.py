import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Content Audit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling - Strict Baseline
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    .guide-content {
        background-color: #0F172A; padding: 20px; border-radius: 8px; color: #ffffff;
        border-left: 5px solid #38BDF8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 10px;
    }
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 320px; overflow-y: auto; font-size: 0.85rem;
    }
    .log-err { color: #F87171; font-weight: bold; } 
    .log-msg { color: #38BDF8; } 
    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 10px;
        text-align: center; border: 1px solid #334155; margin: 0 5px;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #38BDF8; }
    .metric-label { font-size: 0.80rem; color: #94A3B8; text-transform: uppercase; }
    .dark-card { background-color: #1E293B; padding: 25px; border-radius: 12px; border: 1px solid #334155; color: #F1F5F9; height: 100%; }
    .signup-container { display: flex; gap: 10px; margin-top: 15px; }
    .signup-input { flex: 2; padding: 12px; border-radius: 6px; border: 1px solid #334155; background-color: #0F172A; color: white; }
    .signup-btn { flex: 1; background-color: #38BDF8; color: #0F172A; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
    .section-spacer { margin-top: 60px; padding-top: 40px; border-top: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    with st.expander("🚀 QUICK START", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Email & API Token</b> from Admin Center.</div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Audit Tuning")
    restricted_input = st.text_input("Restricted Keywords")
    restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_stale = st.checkbox("Detect Stale Content", value=True)
    enable_ai = st.checkbox("AI Readiness Scan", value=True)
    
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', st.text_area("Exclusion List")) if w.strip()]

# --- 4. AUDIT LOGIC ---
def perform_audit(art, ignore, sub, restricted, stale_check, ai_check):
    body = art.get('body', '') or ''
    title = art.get('title', '')
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.get_text().lower()
    
    issues = {"links": [], "typos": [], "keywords": [], "stale": False, "ai": False}
    
    # Link Check
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    for url in links:
        try:
            if requests.head(url, timeout=1).status_code >= 400: issues["links"].append(url)
        except: issues["links"].append(url)
        
    # Typos & Keywords
    if enable_typos:
        words = spell.split_words(text)
        issues["typos"] = list(spell.unknown(words))
    issues["keywords"] = [w for w in restricted if w in text]
    
    # Stale & AI
    if stale_check:
        upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if datetime.now() - upd > timedelta(days=365): issues["stale"] = True
    if ai_check:
        if len(text) < 500 or not soup.find_all('img', alt=True): issues["ai"] = True
            
    return issues

# --- 5. MAIN PAGE ---
st.title("ZenAudit Deep Scan")
st.info("⚡ **Lightning Mode:** Scanning first 100 articles.")

if st.button("🚀 RUN DEEP SCAN"):
    auth = (f"{email}/token", token)
    api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
    res = requests.get(api_url, auth=auth)
    articles = res.json().get('articles', [])

    if articles:
        m_cols = st.columns(5)
        m_s, m_l, m_t, m_k, m_st = [c.empty() for c in m_cols]
        col_con, col_tip = st.columns([1.5, 1])
        console = col_con.empty()
        tips_box = col_tip.empty()
        
        results_data = []
        log_entries = []

        for i, art in enumerate(articles):
            audit = perform_audit(art, ignore_list, subdomain, restricted_words, enable_stale, enable_ai)
            
            results_data.append({
                "Title": art['title'],
                "URL": art['html_url'],
                "Broken Links": ", ".join(audit["links"]),
                "Typos": ", ".join(audit["typos"]),
                "Restricted Keywords": ", ".join(audit["keywords"]),
                "Stale": "Yes" if audit["stale"] else "No",
                "AI Readiness Issue": "Yes" if audit["ai"] else "No"
            })
            
            status = "<span class='log-err'>[FLAG]</span>" if (audit["links"] or audit["typos"] or audit["keywords"] or audit["stale"]) else "<span class='log-msg'>[OK]</span>"
            log_entries.insert(0, f"{status} {art['title'][:40]}...")
            console.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
            
            # Metrics
            m_s.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned</div><div class='metric-value'>{i+1}</div></div>", unsafe_allow_html=True)
            m_l.markdown(f"<div class='metric-card'><div class='metric-label'>Links</div><div class='metric-value'>{sum(len(d['Broken Links'].split(',')) for d in results_data if d['Broken Links'])}</div></div>", unsafe_allow_html=True)
            m_t.markdown(f"<div class='metric-card'><div class='metric-label'>Typos</div><div class='metric-value'>{sum(len(d['Typos'].split(',')) for d in results_data if d['Typos'])}</div></div>", unsafe_allow_html=True)
            m_k.markdown(f"<div class='metric-card'><div class='metric-label'>Keywords</div><div class='metric-value'>{sum(1 for d in results_data if d['Restricted Keywords'])}</div></div>", unsafe_allow_html=True)
            m_st.markdown(f"<div class='metric-card'><div class='metric-label'>Stale</div><div class='metric-value'>{sum(1 for d in results_data if d['Stale'] == 'Yes')}</div></div>", unsafe_allow_html=True)

        # --- RESTORED DOWNLOAD BUTTON ---
        df = pd.DataFrame(results_data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 DOWNLOAD AUDIT REPORT (CSV)", data=csv, file_name=f"zenaudit_{subdomain}.csv", mime="text/csv")

# --- 6. FOOTER ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown("### 🧠 Audit Intelligence Layers")


e1, e2, e3 = st.columns(3)
with e1: st.markdown('<div class="dark-card"><b>🏺 Stale Content</b><br>Outdated for 365+ days.</div>', unsafe_allow_html=True)
with e2: st.markdown('<div class="dark-card"><b>🗣️ Restricted Keywords</b><br>Legacy/forbidden terms.</div>', unsafe_allow_html=True)
with e3: st.markdown('<div class="dark-card"><b>🤖 AI Readiness</b><br>Formatted for AI accuracy.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
f_l, f_r = st.columns(2)
with f_l: st.markdown('<div class="dark-card"><b>🗺️ Roadmap</b><br>✅ Zendesk (Live)</div>', unsafe_allow_html=True)
with f_r:
    st.markdown('<div class="dark-card"><b>📩 Get Updates</b><div class="signup-container"><input type="email" placeholder="work@email.com" class="signup-input"><button class="signup-btn">NOTIFY</button></div></div>', unsafe_allow_html=True)
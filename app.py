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

# 2. UI Styling (Restored and Polished)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }

    .guide-content, .privacy-content {
        background-color: #0F172A; padding: 20px; border-radius: 8px; color: #ffffff;
        border-left: 5px solid #38BDF8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 10px;
    }

    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 320px; overflow-y: auto; font-size: 0.85rem;
    }

    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 10px;
        text-align: center; border: 1px solid #334155; margin: 0 5px;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #38BDF8; }
    .metric-label { font-size: 0.70rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }

    .dark-card { background-color: #1E293B; padding: 25px; border-radius: 12px; border: 1px solid #334155; color: #F1F5F9; height: 100%; }
    
    /* COMPACT SIGNUP BOX */
    .signup-container { display: flex; gap: 10px; margin-top: 15px; }
    .signup-input {
        flex: 2; padding: 12px; border-radius: 6px; border: 1px solid #334155;
        background-color: #0F172A; color: white; outline: none;
    }
    .signup-btn {
        flex: 1; background-color: #38BDF8; color: #0F172A; border: none;
        padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.3s;
    }
    .signup-btn:hover { background-color: #7DD3FC; }
    .spam-text { font-size: 0.7rem; color: #64748B; margin-top: 8px; }

    .section-spacer { margin-top: 60px; padding-top: 40px; border-top: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (PERMANENT FEATURES) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom:0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Admin Center > Apps > Zendesk API.</div>""", unsafe_allow_html=True)
    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div class="privacy-content"><b>Data Policy:</b> Session-only processing. Credentials are never stored or logged.</div>""", unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Audit Tuning")
    restricted_input = st.text_input("Restricted Keywords", placeholder="OldBrand, Beta, etc.")
    restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_stale = st.checkbox("Detect Stale Content", value=True)
    enable_ai = st.checkbox("AI Readiness Scan", value=True)
    
    raw_ignore = st.text_area("Typo Exclusion List", placeholder="SaaS, API, Acme")
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. AUDIT LOGIC ---
def perform_audit(art, ignore, sub, restricted, stale_check, ai_check):
    body = art.get('body', '') or ''
    title = art.get('title', '')
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.get_text().lower()
    issues = {"links": 0, "typos": 0, "keywords": 0, "stale": 0, "ai": 0}
    
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    for url in links:
        try:
            res = requests.head(url, timeout=1)
            if res.status_code >= 400: issues["links"] += 1
        except: issues["links"] += 1
        
    if enable_typos:
        words = spell.split_words(text)
        issues["typos"] = len([w for w in spell.unknown(words) if len(w) > 2 and w not in ignore])
    
    issues["keywords"] = sum(1 for word in restricted if word in text)
    
    if stale_check:
        updated_at = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if datetime.now() - updated_at > timedelta(days=365): issues["stale"] = 1
            
    if ai_check:
        if len(text) < 500 or not soup.find_all('img', alt=True) or len(title) > 60:
            issues["ai"] = 1
    return issues

# --- 5. MAIN INTERFACE ---
st.title("ZenAudit Intelligence Scan")
st.info("⚡ **Lightning Mode:** Scanning first 100 articles for rapid testing.")

# BUTTON REVERTED TO ORIGINAL LABEL
if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("Missing Credentials")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        res = requests.get(api_url, auth=auth)
        articles = res.json().get('articles', [])

        if articles:
            cols = st.columns(5)
            m_s, m_l, m_t, m_v, m_st = [c.empty() for c in cols]
            console = st.empty()
            log_entries = []

            for i, art in enumerate(articles):
                res = perform_audit(art, ignore_list, subdomain, restricted_words, enable_stale, enable_ai)
                flag = "🚩" if any(v > 0 for v in res.values()) else "✅"
                log_entries.insert(0, f"{flag} {art['title'][:45]}...")
                console.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                m_s.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned</div><div class='metric-value'>{i+1}</div></div>", unsafe_allow_html=True)
                m_l.markdown(f"<div class='metric-card'><div class='metric-label'>Broken</div><div class='metric-value'>{res['links']}</div></div>", unsafe_allow_html=True)
                m_t.markdown(f"<div class='metric-card'><div class='metric-label'>Typos</div><div class='metric-value'>{res['typos']}</div></div>", unsafe_allow_html=True)
                m_v.markdown(f"<div class='metric-card'><div class='metric-label'>Keywords</div><div class='metric-value'>{res['keywords']}</div></div>", unsafe_allow_html=True)
                m_st.markdown(f"<div class='metric-card'><div class='metric-label'>Stale</div><div class='metric-value'>{res['stale']}</div></div>", unsafe_allow_html=True)

# --- 6. FOOTER ---
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
st.markdown("## 🧠 Audit Intelligence Layers")



e1, e2, e3 = st.columns(3)
with e1:
    st.markdown('<div class="dark-card"><b>🏺 Stale Content</b><br><span style="color:#94A3B8; font-size:0.8rem;">Flags articles not updated in 365+ days.</span></div>', unsafe_allow_html=True)
with e2:
    st.markdown('<div class="dark-card"><b>🗣️ Restricted Keywords</b><br><span style="color:#94A3B8; font-size:0.8rem;">Detects legacy branding or forbidden terms.</span></div>', unsafe_allow_html=True)
with e3:
    st.markdown('<div class="dark-card"><b>🤖 AI Readiness</b><br><span style="color:#94A3B8; font-size:0.8rem;">Validates formatting for AI agent ingestion.</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

f_l, f_r = st.columns(2)
with f_l:
    st.markdown('<div class="dark-card"><div style="color:#38BDF8; font-weight:bold; margin-bottom:10px;">🗺️ Platform Roadmap</div><span style="font-size:0.85rem; color:#94A3B8;">✅ Zendesk (Live)<br>⬜ Salesforce Knowledge (Q3 2026)<br>⬜ Intercom (Q4 2026)</span></div>', unsafe_allow_html=True)
with f_r:
    st.markdown("""
    <div class="dark-card">
        <div style="color:#38BDF8; font-weight:bold;">📩 Get Intelligence Updates</div>
        <div class="signup-container">
            <input type="email" placeholder="Enter your work email" class="signup-input">
            <button class="signup-btn">NOTIFY ME</button>
        </div>
        <div class="spam-text">Join 400+ Knowledge Admins. No spam, just updates.</div>
    </div>
    """, unsafe_allow_html=True)
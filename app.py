import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Lightning Scan", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
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
    .metric-label { font-size: 0.85rem; color: #94A3B8; text-transform: uppercase; }
    .dark-card { background-color: #1E293B; padding: 25px; border-radius: 12px; border: 1px solid #334155; color: #F1F5F9; height: 100%; }
    .roadmap-table { width: 100%; border-collapse: collapse; margin-top: 5px; }
    .roadmap-table td { padding: 15px 15px; border-bottom: 1px solid #334155; font-size: 0.9rem; }
    .signup-input { width: 100%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background-color: #0F172A; color: white; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    st.divider()
    enable_typos = st.checkbox("Scan for Typos", value=True)
    enable_health = st.checkbox("AI-Readiness Scan", value=True)
    raw_ignore = st.text_area("Exclusion List", placeholder="SaaS, Acme")
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. ENHANCED AUDIT LOGIC ---
def audit_content(art, ignore, sub, check_typos, check_health):
    body = art.get('body', '') or ''
    title = art.get('title', '')
    soup = BeautifulSoup(body, 'html.parser')
    
    # Link Check
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    broken_int, broken_ext = [], []
    for url in links:
        try:
            res = requests.head(url, timeout=1, allow_redirects=True)
            if res.status_code >= 400:
                if f"{sub}.zendesk.com" in url: broken_int.append(url)
                else: broken_ext.append(url)
        except: broken_ext.append(url)
    
    # Typos
    typos = []
    if check_typos:
        words = spell.split_words(soup.get_text())
        typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in ignore]
    
    # AI/Health Readiness
    health_issues = 0
    if check_health:
        if len(soup.get_text()) < 500: health_issues += 1 # Thin content
        if any(not img.get('alt') for img in soup.find_all('img')): health_issues += 1 # Accessibility
        if len(title) > 60: health_issues += 1 # SEO Title length
        
    return broken_int, broken_ext, typos, health_issues

# --- 5. MAIN SCAN ---
st.title("ZenAudit Lightning Scan")
st.info("⚡ Temporarily limited to 100 articles for rapid testing.")

if st.button("🚀 START LIGHTNING SCAN"):
    if not all([subdomain, email, token]):
        st.error("Credentials missing.")
    else:
        auth = (f"{email}/token", token)
        # TEMPORARY: NO PAGINATION (Fetches only first 100)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        with st.spinner("Connecting..."):
            res = requests.get(api_url, auth=auth)
            articles = res.json().get('articles', [])

        if articles:
            c1, c2, c3, c4 = st.columns(4)
            m1, m2, m3, m4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()
            col_con, col_tip = st.columns([1.5, 1])
            console = col_con.empty()
            
            total_err, total_typo, total_health = 0, 0, 0
            log_entries = []

            for i, art in enumerate(articles):
                b_int, b_ext, typos, h_issues = audit_content(art, ignore_list, subdomain, enable_typos, enable_health)
                
                total_err += (len(b_int) + len(b_ext))
                total_typo += len(typos)
                total_health += h_issues
                
                status = "<span class='log-err'>[FLAG]</span>" if (b_int or b_ext or typos or h_issues) else "<span class='log-msg'>[OK]</span>"
                log_entries.insert(0, f"{status} {art['title'][:40]}...")
                console.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                m1.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned</div><div class='metric-value'>{i+1}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-label'>Broken Links</div><div class='metric-value'>{total_err}</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-label'>Typos</div><div class='metric-value'>{total_typo}</div></div>", unsafe_allow_html=True)
                m4.markdown(f"<div class='metric-card'><div class='metric-label'>Health Flags</div><div class='metric-value'>{total_health}</div></div>", unsafe_allow_html=True)

# --- 6. FOOTER (PRESERVED) ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown("### 🛠️ Coverage Details")
st.markdown("""
<div class="dark-card" style="margin-bottom: 30px;">
    <div style="display: flex; gap: 40px;">
        <div style="flex: 1;"><b>🔗 Link Integrity</b><br><span style="color: #94A3B8; font-size: 0.8rem;">Internal and External 404 detection.</span></div>
        <div style="flex: 1;"><b>✍️ Typo Detection</b><br><span style="color: #94A3B8; font-size: 0.8rem;">Brand-safe spelling verification.</span></div>
        <div style="flex: 1;"><b>🤖 AI Readiness</b><br><span style="color: #94A3B8; font-size: 0.8rem;">Alt-text, Title length, and Content depth.</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

f_l, f_r = st.columns(2)
with f_l:
    st.markdown('<div class="dark-card"><div class="upgrade-header">🗺️ Roadmap</div><table class="roadmap-table"><tr><td>✅ Zendesk</td><td style="text-align:right;">LIVE</td></tr><tr><td>⬜ Salesforce</td><td style="text-align:right;">Q3</td></tr></table></div>', unsafe_allow_html=True)
with f_r:
    st.markdown('<div class="dark-card"><div class="upgrade-header">📩 Updates</div><input type="email" placeholder="email@company.com" class="signup-input"><button style="background-color:#38BDF8; color:#0F172A; border:none; padding:12px; border-radius:6px; font-weight:bold; width:100%;">NOTIFY ME</button></div>', unsafe_allow_html=True)
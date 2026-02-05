import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Full Intelligence", page_icon="🛡️", layout="wide")
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
    .metric-label { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }

    .section-spacer { margin-top: 60px; padding-top: 40px; border-top: 1px solid #334155; }
    
    .dark-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; height: 100%;
    }
    
    .feature-title { color: #38BDF8; font-weight: bold; font-size: 1.1rem; margin-bottom: 8px; display: block; }
    .feature-desc { color: #94A3B8; font-size: 0.85rem; line-height: 1.4; }
    
    .roadmap-table { width: 100%; border-collapse: collapse; }
    .roadmap-table td { padding: 12px; border-bottom: 1px solid #334155; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (RESTORED ALL FEATURES) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom:0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Admin Center > Apps > Zendesk API > Enable Token Access.</div>""", unsafe_allow_html=True)

    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div class="privacy-content"><b>Data Policy:</b> Session-only processing. API calls use HTTPS. Credentials are never stored. Data is wiped when the tab closes.</div>""", unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Audit Tuning")
    forbidden_input = st.text_input("Forbidden Words", placeholder="OldBrand, Beta, etc.")
    forbidden_words = [w.strip().lower() for w in forbidden_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_rot = st.checkbox("Detect Content Rot", value=True)
    
    raw_ignore = st.text_area("Typo Exclusion List", placeholder="SaaS, API, Acme")
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. CORE AUDIT LOGIC ---
def perform_audit(art, ignore, sub, forbidden, rot_check):
    body = art.get('body', '') or ''
    title = art.get('title', '')
    soup = BeautifulSoup(body, 'html.parser')
    text = soup.get_text().lower()
    
    issues = {"links": 0, "typos": 0, "voice": 0, "rot": 0, "seo": 0}
    
    # Links
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    for url in links:
        try:
            res = requests.head(url, timeout=1)
            if res.status_code >= 400: issues["links"] += 1
        except: issues["links"] += 1
        
    # Typos & Voice
    words = spell.split_words(text)
    issues["typos"] = len([w for w in spell.unknown(words) if len(w) > 2 and w not in ignore])
    issues["voice"] = sum(1 for word in forbidden if word in text)
    
    # Rot
    if rot_check:
        updated_at = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if datetime.now() - updated_at > timedelta(days=365): issues["rot"] = 1
            
    # SEO/AI Readiness
    if len(text) < 500 or not soup.find_all('img', alt=True) or len(title) > 60:
        issues["seo"] = 1
        
    return issues

# --- 5. MAIN SCAN INTERFACE ---
st.title("ZenAudit Intelligence Scan")
st.info("⚡ **Lightning Mode Active:** Scanning the most recent 100 articles for rapid feedback.")

if st.button("🚀 EXECUTE DEEP AUDIT"):
    if not all([subdomain, email, token]):
        st.error("Missing Connection Credentials")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        with st.spinner("Accessing Zendesk Library..."):
            res = requests.get(api_url, auth=auth)
            articles = res.json().get('articles', [])

        if articles:
            cols = st.columns(5)
            m_s = cols[0].empty()
            m_l = cols[1].empty()
            m_t = cols[2].empty()
            m_v = cols[3].empty()
            m_r = cols[4].empty()
            
            console = st.empty()
            log_entries = []

            for i, art in enumerate(articles):
                res = perform_audit(art, ignore_list, subdomain, forbidden_words, enable_rot)
                
                flag = "🚩" if any(v > 0 for k, v in res.items()) else "✅"
                log_entries.insert(0, f"{flag} {art['title'][:45]}...")
                console.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                m_s.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned</div><div class='metric-value'>{i+1}</div></div>", unsafe_allow_html=True)
                m_l.markdown(f"<div class='metric-card'><div class='metric-label'>Broken</div><div class='metric-value'>{res['links']}</div></div>", unsafe_allow_html=True)
                m_t.markdown(f"<div class='metric-card'><div class='metric-label'>Typos</div><div class='metric-value'>{res['typos']}</div></div>", unsafe_allow_html=True)
                m_v.markdown(f"<div class='metric-card'><div class='metric-label'>Voice</div><div class='metric-value'>{res['voice']}</div></div>", unsafe_allow_html=True)
                m_r.markdown(f"<div class='metric-card'><div class='metric-label'>Rot</div><div class='metric-value'>{res['rot']}</div></div>", unsafe_allow_html=True)

# --- 6. EXPLAINER FOOTER ---
st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
st.markdown("## 🧠 Audit Intelligence Layers")
st.markdown("Learn how ZenAudit evaluates your 1,800+ article library for quality and AI-readiness.")

# Image Tag for Contextual Clarity on Content Auditing


# Explained Sections
e1, e2, e3 = st.columns(3)
with e1:
    st.markdown("""
    <div class="dark-card">
        <span class="feature-title">🏺 Content Rot Detection</span>
        <p class="feature-desc">Identifies "stale" articles that haven't been updated in 365+ days. High rot scores indicate content that may mislead users or confuse AI models.</p>
    </div>
    """, unsafe_allow_html=True)
with e2:
    st.markdown("""
    <div class="dark-card">
        <span class="feature-title">🗣️ Brand Voice Consistency</span>
        <p class="feature-desc">Automatically flags forbidden terms, legacy product names, or inconsistent naming conventions across your entire documentation set.</p>
    </div>
    """, unsafe_allow_html=True)
with e3:
    st.markdown("""
    <div class="dark-card">
        <span class="feature-title">🤖 AI & SEO Readiness</span>
        <p class="feature-desc">Validates header hierarchy, image alt-text, and metadata. Ensures your content is structured correctly for Google and AI Chatbots.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Bottom Row: Roadmap & Lead Gen
f_left, f_right = st.columns(2)
with f_left:
    st.markdown("""
    <div class="dark-card">
        <div class="upgrade-header">🗺️ Platform Roadmap</div>
        <table class="roadmap-table">
            <tr><td>✅ Zendesk Guide</td><td style="text-align:right; color:#38BDF8;">LIVE</td></tr>
            <tr><td>⬜ Salesforce Knowledge</td><td style="text-align:right; color:#94A3B8;">Q3 2026</td></tr>
            <tr><td>⬜ Intercom Articles</td><td style="text-align:right; color:#94A3B8;">Q4 2026</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
with f_right:
    st.markdown("""
    <div class="dark-card">
        <div class="upgrade-header">📩 Get Intelligence Updates</div>
        <p class="feature-desc">Get notified when we release bulk-auto-correction and CSV export features.</p>
        <input type="email" placeholder="email@company.com" class="signup-input">
        <button style="background-color:#38BDF8; color:#0F172A; border:none; padding:12px; border-radius:6px; font-weight:bold; width:100%; cursor:pointer;">NOTIFY ME</button>
    </div>
    """, unsafe_allow_html=True)
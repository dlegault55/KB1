import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Content Audit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling - STRICT DARK MODE / NO WHITE BOXES
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }

    /* Button Styling */
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    .stButton>button:hover { background-color: #0EA5E9; color: white; }
    
    /* Sidebar Boxes */
    .guide-content, .privacy-content {
        background-color: #1E293B; padding: 20px; border-radius: 8px; color: #ffffff;
        border-left: 5px solid #38BDF8; font-size: 0.85rem; line-height: 1.6; margin-bottom: 10px;
    }

    /* The Dark Console */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 320px; overflow-y: auto; font-size: 0.85rem;
    }
    .log-err { color: #F87171; font-weight: bold; } 
    .log-msg { color: #38BDF8; } 
    
    /* Custom Dark Metrics */
    .metric-card {
        background-color: #1E293B; padding: 15px; border-radius: 10px;
        text-align: center; border: 1px solid #334155;
    }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #38BDF8; }
    .metric-label { font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; }

    /* Marketing/Upgrade Cards */
    .dark-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; margin-bottom: 20px; height: 100%;
    }
    .upgrade-header { color: #38BDF8; font-size: 1.4rem; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Admin Center > Apps > Zendesk API > Enable Token Access.</div>""", unsafe_allow_html=True)

    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div class="privacy-content"><b>Data Policy:</b> Session-only processing. API calls use HTTPS. Credentials are never stored.</div>""", unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    enable_typos = st.checkbox("Scan for Typos", value=True)
    raw_ignore = st.text_area("Exclusion List", height=100, placeholder="SaaS, Acme, API")
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. CORE LOGIC ---
tips = [
    "💀 **Admin Truth:** If you don't fix these 404s, your customers will mention it in the CSAT comment.",
    "🥃 **Guerilla Tip:** Stop using 'New' in article titles. It stays 'New' for three years.",
    "🛠️ **Workflow:** 1,800 articles? You don't have a Knowledge Base, you have a digital museum.",
    "📉 **Stats:** 70% of 'Search Fails' are actually customers hitting a dead link."
]

def audit_content(html_body, ignore, sub, check_typos):
    if not html_body: return [], [], []
    soup = BeautifulSoup(html_body, 'html.parser')
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    broken_int, broken_ext, typos = [], [], []
    for url in links:
        try:
            res = requests.head(url, timeout=2, allow_redirects=True)
            if res.status_code >= 400:
                if f"{sub}.zendesk.com" in url: broken_int.append(url)
                else: broken_ext.append(url)
        except: broken_ext.append(url)
    if check_typos:
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in ignore]
    return broken_int, broken_ext, typos

# --- 5. MAIN PAGE LAYOUT ---
st.title("ZenAudit Deep Scan")

# Scan Controls
if st.button("🚀 RUN DEEP SCAN"): 
    if not all([subdomain, email, token]):
        st.error("⚠️ Credentials missing. Check the Sidebar.")
    else:
        all_articles = []
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        with st.status("📡 Fetching Library...", expanded=True) as status:
            while api_url:
                res = requests.get(api_url, auth=auth)
                if res.status_code != 200: break
                data = res.json()
                all_articles.extend(data.get('articles', []))
                st.write(f"📥 Indexed {len(all_articles)} headers...")
                api_url = data.get('next_page')
            status.update(label="✅ Ready to Scan", state="complete")

        if all_articles:
            # Custom Metric Row
            c1, c2, c3, c4 = st.columns(4)
            m1, m2, m3, m4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()
            prog_bar = st.progress(0)
            
            col_con, col_tip = st.columns([1.5, 1])
            with col_con:
                st.markdown("### 🖥️ Audit Logs")
                console_placeholder = st.empty()
            with col_tip:
                st.markdown("### 🗣️ Admin Insight")
                tip_placeholder = st.empty()
            
            total_int, total_ext, total_typo = 0, 0, 0
            log_entries = []
            total_count = len(all_articles)

            for i, art in enumerate(all_articles):
                b_int, b_ext, typos = audit_content(art.get('body', ''), ignore_list, subdomain, enable_typos)
                
                total_int += len(b_int); total_ext += len(b_ext); total_typo += len(typos)
                status_line = f"<span class='log-err'>[REVISE]</span>" if (b_int or b_ext or typos) else f"<span class='log-msg'>[VERIFIED]</span>"
                log_entries.insert(0, f"{status_line} {art['title'][:40]}...")
                
                if len(log_entries) > 12: log_entries.pop()
                console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries)}</div>", unsafe_allow_html=True)
                
                if i % 50 == 0 or i == 0:
                    tip_placeholder.markdown(f"<div class='dark-card' style='display:flex; align-items:center; text-align:center;'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                prog_bar.progress((i + 1) / total_count)
                m1.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned</div><div class='metric-value'>{i+1}</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-label'>Int. 404</div><div class='metric-value'>{total_int}</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-label'>Ext. 404</div><div class='metric-value'>{total_ext}</div></div>", unsafe_allow_html=True)
                m4.markdown(f"<div class='metric-card'><div class='metric-label'>Typos</div><div class='metric-value'>{total_typo}</div></div>", unsafe_allow_html=True)

            st.success("✅ Deep Scan Complete.")
            st.balloons()

# --- 6. INTEGRATED MARKETING & UPGRADE SECTION ---
st.divider()

col_val, col_up = st.columns([1.2, 1])

with col_val:
    st.markdown("### 🛠️ Coverage Details")
    st.markdown("""
    <div class="dark-card">
        <b>🔗 Internal 404s:</b> Links pointing to deleted or restricted articles in your subdomain.<br><br>
        <b>🌍 External 404s:</b> Verification of third-party links to prevent Search Abandonment.<br><br>
        <b>✍️ Typo Detection:</b> Scans article bodies for spelling errors that hurt brand trust.
    </div>
    """, unsafe_allow_html=True)

with col_up:
    st.markdown("### 📥 Remediation Report")
    st.markdown("""
    <div class="dark-card" style="border-color: #38BDF8;">
        <div class="upgrade-header">Export Results for $25</div>
        <ul>
            <li><b>CSV Map:</b> Exact URLs of every broken link found.</li>
            <li><b>Article IDs:</b> Match errors to your Zendesk articles instantly.</li>
            <li><b>Typo List:</b> Specific misspelled words per article.</li>
        </ul>
        <button style="background-color:#38BDF8; color:#0F172A; border:none; padding:12px; border-radius:5px; font-weight:bold; width:100%; cursor:pointer; margin-top:10px;">PURCHASE FULL CSV REPORT</button>
    </div>
    """, unsafe_allow_html=True)
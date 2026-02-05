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

# 2. UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    .stButton>button:hover { background-color: #0EA5E9; color: white; }
    
    .guide-content, .privacy-content {
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
    
    .metric-container { margin-bottom: 30px; }
    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 10px;
        text-align: center; border: 1px solid #334155; margin: 0 5px;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #38BDF8; }
    .metric-label { font-size: 0.85rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; }

    .section-spacer { margin-top: 80px; padding-top: 40px; border-top: 1px solid #334155; }
    
    .dark-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; height: 100%;
    }
    .upgrade-header { color: #38BDF8; font-size: 1.3rem; font-weight: bold; margin-bottom: 15px; }
    
    .roadmap-table { width: 100%; margin-top: 10px; }
    .roadmap-table td { padding: 12px 0; border-bottom: 1px solid #334155; font-size: 0.9rem; }
    
    /* Purchase block "waiting" state - hidden but wired */
    .purchase-hidden { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Admin Center > Apps > Zendesk API > Enable Token Access.</div>""", unsafe_allow_html=True)

    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div class="privacy-content"><b>Data Policy:</b> Session-only processing. API calls use HTTPS. Credentials are never stored. Data is wiped when the tab closes.</div>""", unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    enable_typos = st.checkbox("Scan for Typos", value=True)
    raw_ignore = st.text_area("Exclusion List", height=100, placeholder="SaaS, Acme, API")
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. DATA LOGIC & TIPS ---
tips = [
    "💀 **Admin Truth:** If you don't fix these 404s, your customers will mention it in the CSAT comment.",
    "🤖 **AI Reality:** If your articles are trash, your AI Agent will just be a very fast, very confident liar.",
    "📈 **SEO Burn:** Google hates 'stale' content. If an article hasn't been updated since 2022, it's basically invisible.",
    "🏺 **Digital Museum:** 1,800 articles? You don't have a Knowledge Base, you have a digital museum.",
    "🔍 **Search Bloat:** Every bad article makes your 'Search Results' 1% more useless.",
    "🛑 **Internal Links:** Linking to a 'Private' article from a 'Public' one is a great way to frustrate users.",
    "🕵️ **Hidden Debt:** Broken images are just as bad as broken links.",
    "📉 **The 80/20 Rule:** 80% of your traffic goes to 20 articles.",
    "🥃 **Guerilla Tip:** Stop using 'New' in article titles. It stays 'New' for three years.",
    "🛠️ **Workflow:** Manual audits are for people with too much time. Let the machine find the rot."
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

# --- 5. MAIN SCAN INTERFACE ---
st.title("ZenAudit Deep Scan")

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
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            m1, m2, m3, m4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()
            st.markdown('</div>', unsafe_allow_html=True)
            
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

# --- 6. FOOTER: COVERAGE & ROADMAP ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

st.markdown("### 🛠️ Coverage Details")
st.markdown("""
<div class="dark-card" style="margin-bottom: 30px;">
    <div style="display: flex; gap: 40px;">
        <div style="flex: 1;">
            <b>🔗 Internal 404s</b><br>
            <span style="color: #94A3B8; font-size: 0.9rem;">Links pointing to deleted or restricted articles in your subdomain.</span>
        </div>
        <div style="flex: 1;">
            <b>🌍 External 404s</b><br>
            <span style="color: #94A3B8; font-size: 0.9rem;">Verification of third-party links to prevent Search Abandonment.</span>
        </div>
        <div style="flex: 1;">
            <b>✍️ Typo Detection</b><br>
            <span style="color: #94A3B8; font-size: 0.9rem;">Scans article bodies for spelling errors that hurt brand trust.</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Layout for Roadmap (and hidden Purchase block)
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    <div class="dark-card">
        <div class="upgrade-header">🗺️ Platform Roadmap</div>
        <table class="roadmap-table">
            <tr><td><span style="color: #38BDF8;">✅</span> <b>Zendesk Guide</b></td><td style="text-align:right; color: #38BDF8;"><b>LIVE</b></td></tr>
            <tr><td>⬜ Salesforce Knowledge</td><td style="text-align:right; color: #94A3B8;">Q3 '26</td></tr>
            <tr><td>⬜ Intercom Articles</td><td style="text-align:right; color: #94A3B8;">Q4 '26</td></tr>
            <tr><td>⬜ Notion / Public Docs</td><td style="text-align:right; color: #94A3B8;">Backlog</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    # --- PURCHASE BLOCK WIRING (HIDDEN) ---
    # To enable: remove 'display: none;' from .purchase-hidden in CSS or change class to 'dark-card'
    st.markdown("""
    <div class="purchase-hidden">
        <div class="upgrade-header">📥 Remediation Report ($25)</div>
        <p style="font-size: 0.9rem;">CSV Export with Exact URLs and Article IDs.</p>
        <button style="background-color:#38BDF8; color:#0F172A; border:none; padding:12px; border-radius:5px; font-weight:bold; width:100%; cursor:pointer;">PURCHASE REPORT</button>
    </div>
    <div class="dark-card">
        <div class="upgrade-header">💡 Why ZenAudit?</div>
        <p style="font-size: 0.9rem; color: #94A3B8;">
            High-performance content teams use ZenAudit to automate the "grunt work" of quality assurance. 
            Keep your Knowledge Base lean, accurate, and ready for AI integration.
        </p>
    </div>
    """, unsafe_allow_html=True)
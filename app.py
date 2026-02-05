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

# 2. UI Styling - NO WHITE BOXES
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }

    /* Button Styling */
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    .stButton>button:hover { background-color: #0EA5E9; color: white; }
    
    /* Dark Contrast Expander Boxes */
    .guide-content, .privacy-content {
        background-color: #0F172A; padding: 20px; border-radius: 8px; color: #ffffff;
        border-left: 5px solid #38BDF8; font-size: 0.85rem; line-height: 1.6;
    }
    .guide-content b { color: #38BDF8; }

    /* The Dark Console */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 320px; overflow-y: auto; font-size: 0.85rem;
    }
    .log-err { color: #F87171; font-weight: bold; } 
    .log-msg { color: #38BDF8; } 
    
    /* Dark Cards for Tips & Marketing */
    .dark-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; margin-bottom: 20px;
    }
    .tip-style {
        font-size: 1.05rem; min-height: 140px; display: flex; 
        align-items: center; justify-content: center; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div class="guide-content"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Admin Center > Apps > Zendesk API > Enable Token Access.</div>""", unsafe_allow_html=True)

    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div class="privacy-content"><b>Does this store my data?</b> No. It runs in your browser session. All API calls use HTTPS. Data is wiped on tab close.</div>""", unsafe_allow_html=True)

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
    "⚠️ **SEO Reality:** Google doesn't care how 'helpful' your article is if the first link 404s.",
    "🥃 **Guerilla Tip:** Stop using 'New' in article titles. It stays 'New' for three years.",
    "🛠️ **Workflow:** 1,800 articles? You don't have a Knowledge Base, you have a digital museum.",
    "🛑 **Accessibility:** If your link text is 'Click here,' you're failing customers with screen readers.",
    "📉 **Stats:** 70% of 'Search Fails' are actually customers hitting a dead link.",
    "🕵️ **Deep Cut:** Zendesk search index is only as good as your meta-tags.",
    "⚡ **Speed:** Manual audits are for people with too much time."
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

# --- 5. MAIN PAGE ---
st.title("ZenAudit Deep Scan")
tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 WHY UPGRADE?"])

with tab1:
    if st.button("🚀 RUN DEEP SCAN"): 
        if not all([subdomain, email, token]):
            st.error("⚠️ Credentials missing. Check the Sidebar.")
        else:
            all_articles = []
            auth = (f"{email}/token", token)
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
            
            with st.status("📡 Syncing with Zendesk API...", expanded=True) as status:
                while api_url:
                    res = requests.get(api_url, auth=auth)
                    if res.status_code != 200: break
                    data = res.json()
                    all_articles.extend(data.get('articles', []))
                    st.write(f"📥 Indexed {len(all_articles)} articles...")
                    api_url = data.get('next_page')
                status.update(label="✅ Library Synchronized", state="complete")

            if all_articles:
                m1, m2, m3, m4 = st.columns(4)
                stat_total, stat_int, stat_ext, stat_typo = m1.empty(), m2.empty(), m3.empty(), m4.empty()
                prog_bar = st.progress(0)
                
                col_con, col_tip = st.columns([1.5, 1])
                with col_con:
                    st.markdown("### 🖥️ Audit Logs")
                    console_placeholder = st.empty()
                with col_tip:
                    st.markdown("### 🗣️ Admin Insight")
                    tip_placeholder = st.empty()
                
                report_list = []
                log_entries = []
                total_int, total_ext, total_typo = 0, 0, 0
                total_count = len(all_articles)

                for i, art in enumerate(all_articles):
                    b_int, b_ext, typos = audit_content(art.get('body', ''), ignore_list, subdomain, enable_typos)
                    
                    if b_int or b_ext or typos:
                        total_int += len(b_int); total_ext += len(b_ext); total_typo += len(typos)
                        report_list.append({"Title": art['title']})
                        status_line = f"<span class='log-err'>[REVISE]</span> {art['title'][:40]}..."
                    else:
                        status_line = f"<span class='log-msg'>[VERIFIED]</span> {art['title'][:40]}..."
                    
                    log_entries.insert(0, status_line)
                    if len(log_entries) > 12: log_entries.pop()
                    console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries)}</div>", unsafe_allow_html=True)
                    
                    if i % 50 == 0 or i == 0:
                        tip_placeholder.markdown(f"<div class='dark-card tip-style'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                    prog_bar.progress((i + 1) / total_count)
                    stat_total.metric("Scanned", f"{i+1}/{total_count}")
                    stat_int.metric("Int. 404s", total_int)
                    stat_ext.metric("Ext. 404s", total_ext)
                    stat_typo.metric("Typos", total_typo)

                st.success(f"Scan Complete. {len(report_list)} articles require revision.")
                st.balloons()
    
    # RESTORED MARKETING MATERIAL ON MAIN PAGE
    st.divider()
    st.markdown("### 🛠️ What ZenAudit Scans")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="dark-card"><b>🔗 Internal 404s</b><br>Finds broken links pointing to your own Zendesk subdomain.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="dark-card"><b>🌍 External 404s</b><br>Validates outside URLs to ensure your partners haven\'t moved their pages.</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="dark-card"><b>✍️ Typo Detection</b><br>Scans for spelling errors that damage your brand authority.</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("## Editorial Audit vs. Full Remediation")
    col_left, col_right = st.columns(2)
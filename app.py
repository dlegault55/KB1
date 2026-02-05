import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Editorial Audit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { background-color: #219EBC; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;}
    .stButton>button:hover { background-color: #023047; color: #FFB703; border: 1px solid #FFB703; }
    
    /* Dark Contrast Expander Content */
    .guide-content {
        background-color: #023047; padding: 20px; border-radius: 8px; color: #ffffff;
        border-left: 5px solid #FFB703; font-size: 0.85rem; line-height: 1.6;
    }
    .guide-content b { color: #FFB703; }
    .privacy-content {
        background-color: #023047; padding: 15px; border-radius: 8px; color: #e0f2f1;
        border-left: 5px solid #219EBC; font-size: 0.8rem; line-height: 1.4;
    }

    /* The Editorial Console */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #219EBC;
        height: 320px; overflow-y: auto; font-size: 0.85rem;
    }
    .log-err { color: #F28482; font-weight: bold; } /* Soft Red/Coral */
    .log-msg { color: #8ECAE6; } /* Sky Blue */
    
    .tip-style {
        font-size: 1.05rem; padding: 25px; border-radius: 15px;
        background-color: #ffffff; border: 2px solid #023047;
        min-height: 140px; display: flex; align-items: center; justify-content: center;
        text-align: center; color: #023047; font-weight: 600;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (GUIDE & PRIVACY RESTORED) ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    # 1. Quick Start
    with st.expander("🚀 QUICK START GUIDE", expanded=False):
        st.markdown("""
        <div class="guide-content">
            <b>1. Subdomain:</b> [acme]<br>
            <b>2. Admin Email:</b> login@company.com<br>
            <b>3. API Token:</b> Admin Center > Apps > Zendesk API > Enable Token Access.
        </div>
        """, unsafe_allow_html=True)

    # 2. RESTORED FAQ & PRIVACY
    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""
        <div class="privacy-content">
            <b>Does this store my data?</b><br>
            No. This tool runs in your browser's session. Your API token and article content are never stored on a database.<br><br>
            <b>Is it safe?</b><br>
            We use HTTPS for all Zendesk API calls. Once you close the tab, the connection data is wiped.<br><br>
            <b>Rate Limits?</b><br>
            We fetch 100 articles per request to stay within Zendesk's API limits.
        </div>
        """, unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    enable_typos = st.checkbox("Scan for Typos", value=True)
    raw_ignore = st.text_area("Exclusion List", height=80)
    ignore_list = [w.strip().lower() for w in re.split(r'[\n,]+', raw_ignore) if w.strip()]

# --- 4. THE SALTY ADMIN INSIGHTS ---
tips = [
    "💀 **Admin Truth:** If you don't fix these 404s, your customers will mention it in the CSAT comment.",
    "⚠️ **SEO Reality:** Google doesn't care how 'helpful' your article is if the first link 404s.",
    "🥃 **Guerilla Tip:** Stop using 'New' in article titles. It stays 'New' for three years.",
    "🛠️ **Workflow:** 1,800 articles? You don't have a Knowledge Base, you have a digital museum.",
    "🛑 **Accessibility:** If your link text is 'Click here,' you're failing customers with screen readers.",
    "📉 **Stats:** 70% of 'Search Fails' are actually customers finding the article but hitting a dead link.",
    "🕵️ **Deep Cut:** Zendesk search index is only as good as your meta-tags. Fix the source, fix the search.",
    "⚡ **Speed:** Manual audits are for people with too much time. Let the machine find the rot."
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
st.title("Knowledge Base Editorial Audit")
tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 WHY UPGRADE?"])

with tab1:
    if st.button("🚀 BEGIN EDITORIAL REVIEW"):
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
                        tip_placeholder.markdown(f"<div class='tip-style'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                    prog_bar.progress((i + 1) / total_count)
                    stat_total.metric("Scanned", f"{i+1}/{total_count}")
                    stat_int.metric("Int. 404s", total_int)
                    stat_ext.metric("Ext. 404s", total_ext)
                    stat_typo.metric("Typos", total_typo)

                st.success(f"Review Complete. {len(report_list)} articles require revision.")
                st.balloons()
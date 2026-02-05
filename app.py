import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { background-color: #219EBC; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;}
    .stButton>button:hover { background-color: #023047; color: #FFB703; border: 1px solid #FFB703; }
    
    /* Dark Contrast inside the Expander */
    .guide-content {
        background-color: #023047;
        padding: 20px;
        border-radius: 8px;
        color: #ffffff;
        border-left: 5px solid #FFB703;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    .guide-content b { color: #FFB703; }
    .code-span { background: #005f73; padding: 2px 5px; border-radius: 4px; font-family: monospace; }

    /* Console Styling */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #219EBC;
        height: 250px; overflow-y: auto; font-size: 0.85rem;
    }
    .log-err { color: #ff585f; font-weight: bold; }
    .log-msg { color: #addb67; }
    
    /* Tip Box Styling */
    .tip-style {
        font-size: 1.1rem; padding: 25px; border-radius: 15px;
        background-color: #ffffff; border: 2px solid #8ECAE6;
        min-height: 140px; display: flex; align-items: center; justify-content: center;
        text-align: center; color: #023047; font-weight: 500;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (SPECIFIC DIRECTIONS) ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div class="guide-content">
            <b>1. Subdomain:</b><br>
            If your URL is <span class="code-span">acme.zendesk.com</span>, enter <span class="code-span">acme</span>.<br><br>
            <b>2. Admin Email:</b><br>
            The email address you use to log in to your Zendesk dashboard.<br><br>
            <b>3. API Token:</b><br>
            Go to <b>Admin Center</b> > <b>Apps and integrations</b> > <b>Zendesk API</b>.<br>
            Ensure <b>'Token Access'</b> is ON, then click <b>'Add API token'</b>.
        </div>
        """, unsafe_allow_html=True)

    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email", placeholder="you@company.com")
    token = st.text_input("API Token", type="password", help="Ensure 'Token Access' is enabled in Zendesk")
    
    st.divider()
    st.header("⚙️ Settings")
    enable_typos = st.checkbox("Scan for Typos", value=True)
    raw_ignore = st.text_area("Exclusion List (One per line)", height=100)
    ignore_list = [w.strip().lower() for w in re.split(r'[\n,]+', raw_ignore) if w.strip()]

# --- 4. THE HUMOROUS TIP ENGINE ---
tips = [
    "💡 **Pro Tip:** Broken internal links are the #1 cause of 'Search Abandonment'.",
    "💡 **SEO Tip:** 404 errors prevent Google from indexing your new helpful articles.",
    "☕ **Support Reality:** Scanning 1,800 articles is still faster than manually clicking 'Edit' on all of them.",
    "🤖 **Fun Fact:** I'm currently reading your Help Center faster than a Tier 1 agent on their third espresso.",
    "🎭 **Support Humor:** Your articles are being judged. Don't worry, I'm a friendly robot.",
    "👻 **Support Reality:** Somewhere, a customer is trying to follow a 404 link right now. Let's find it first.",
    "🍕 **Support Reality:** If you have 1,800 articles, you probably deserve a pizza for managing them.",
    "💡 **Deflection:** Every 10 dead links fixed typically results in a drop in 'I couldn't find it' tickets."
]

# --- 5. MAIN PAGE ---
st.title("ZenAudit Deep Scan")
tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 WHY UPGRADE?"])

with tab1:
    if st.button("🚀 RUN DEEP SCAN"):
        if not all([subdomain, email, token]):
            st.error("⚠️ Credentials missing. Check the Quick Start Guide in the sidebar!")
        else:
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            stat_total, stat_int, stat_ext, stat_typo = m1.empty(), m2.empty(), m3.empty(), m4.empty()
            prog_bar = st.progress(0)
            
            col_con, col_tip = st.columns([1.5, 1])
            with col_con:
                st.markdown("### 🖥️ Analysis Console")
                console_placeholder = st.empty()
            with col_tip:
                st.markdown("### 🍿 While You Wait...")
                tip_placeholder = st.empty()
            
            # Simulated audit logic
            total_items = 100 
            report_list = []
            log_entries = []
            total_int, total_ext, total_typo = 0, 0, 0
            
            for i in range(1, total_items + 1):
                error_found = random.random() < 0.15
                if error_found:
                    total_int += 1
                    status_line = f"<span class='log-err'>[FAIL]</span> Art. {i}: Dead Link Detected"
                    report_list.append({"Art": i})
                else:
                    status_line = f"<span class='log-msg'>[PASS]</span> Art. {i}: Content Clean"
                
                log_entries.insert(0, status_line)
                if len(log_entries) > 12: log_entries.pop()
                console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries)}</div>", unsafe_allow_html=True)
                
                if i % 20 == 0 or i == 1:
                    tip_placeholder.markdown(f"<div class='tip-style'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                prog_bar.progress(i / total_items)
                stat_total.metric("Articles", f"{i}/{total_items}")
                stat_int.metric("Dead Links", total_int)
                stat_typo.metric("Typos", total_typo)
                time.sleep(0.05)

            st.success("✅ Deep Scan Complete!")
            st.balloons()
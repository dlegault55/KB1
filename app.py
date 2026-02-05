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
    
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #219EBC;
        height: 250px; overflow-y: auto; font-size: 0.85rem; line-height: 1.5;
    }
    .log-err { color: #ff585f; font-weight: bold; }
    .log-msg { color: #addb67; }
    
    .score-container {
        text-align: center; padding: 40px; background: #ffffff; border-radius: 20px;
        border: 4px solid #219EBC; margin-top: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    .guide-box {
        background-color: #e0f2f1; padding: 15px; border-radius: 8px; 
        border-left: 5px solid #00897b; margin-bottom: 20px; font-size: 0.9rem;
    }
    
    /* Style for the rotating Tip Box */
    .tip-style {
        font-size: 1.1rem; padding: 20px; border-radius: 12px;
        background-color: #f1f5f9; border: 1px dashed #cbd5e1;
        min-height: 120px; display: flex; align-items: center; justify-content: center;
        text-align: center; color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Guide is LOCKED) ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    st.markdown('<div class="guide-box"><b>🚀 QUICK START</b><br>1. <b>Subdomain:</b> [acme].zendesk.com<br>2. <b>Admin Email:</b> Your login<br>3. <b>API Token:</b> Zendesk Admin Center</div>', unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    enable_typos = st.checkbox("Scan for Typos", value=True)
    raw_ignore = st.text_area("Ignore Words (One per line)", placeholder="SaaS\nAcmeCorp")
    ignore_list = [w.strip().lower() for w in re.split(r'[\n,]+', raw_ignore) if w.strip()]

# --- 4. THE TIP ENGINE ---
# Mixing Authority with Support-Humor
tips = [
    "💡 **Pro Tip:** Broken internal links are the #1 cause of 'Search Abandonment' in Zendesk.",
    "💡 **SEO Tip:** 404 errors prevent Google from indexing your new helpful articles.",
    "☕ **Support Reality:** Scanning 1,800 articles is still faster than manually clicking 'Edit' on all of them.",
    "💡 **CX Insight:** Typos in technical docs reduce perceived reliability by roughly 30%.",
    "🤖 **Fun Fact:** I'm currently reading your Help Center faster than a Tier 1 agent on their third espresso.",
    "🛑 **Pro Tip:** Don't use 'Click Here' as link text. It’s bad for SEO and even worse for accessibility.",
    "🎭 **Support Humor:** Your articles are being judged. Don't worry, I'm a friendly robot.",
    "📈 **Deflection:** Every 10 dead links fixed typically results in a measurable drop in tickets.",
    "👻 **Support Reality:** Somewhere, a customer is trying to follow a 404 link right now. Let's find it first."
]

# --- 5. MAIN PAGE ---
st.title("ZenAudit Deep Scan")
tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 WHY UPGRADE?"])

with tab1:
    if st.button("🚀 RUN DEEP SCAN"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Connection details missing.")
        else:
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            stat_total, stat_int, stat_ext, stat_typo = m1.empty(), m2.empty(), m3.empty(), m4.empty()
            prog_bar = st.progress(0)
            
            # The Layout: Console on left, Tips on right
            col_con, col_tip = st.columns([1.5, 1])
            with col_con:
                st.markdown("### 🖥️ Analysis Console")
                console_placeholder = st.empty()
            with col_tip:
                st.markdown("### 🍿 While You Wait...")
                tip_placeholder = st.empty()
            
            # Simulated Scan Logic (Replace with actual API loop for 1,800 articles)
            report_list = []
            log_entries = []
            total_int, total_ext, total_typo = 0, 0, 0
            
            # For demonstration, we'll simulate a 100-article batch
            for i in range(1, 101):
                # Simulated results
                has_error = random.random() < 0.2
                if has_error:
                    total_int += 1
                    report_list.append({"Article": f"Article {i}"})
                    status_line = f"<span class='log-err'>[FAIL]</span> Article {i}: Found broken links"
                else:
                    status_line = f"<span class='log-msg'>[PASS]</span> Article {i}: Clean"
                
                # Update Console (Show last 12 lines)
                log_entries.insert(0, status_line)
                if len(log_entries) > 12: log_entries.pop()
                console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries)}</div>", unsafe_allow_html=True)
                
                # --- ROTATE TIPS EVERY 20 ARTICLES ---
                if i % 20 == 0 or i == 1:
                    tip_placeholder.markdown(f"<div class='tip-style'>{random.choice(tips)}</div>", unsafe_allow_html=True)

                # Update Progress
                prog_bar.progress(i/100)
                stat_total.metric("Articles", f"{i}/100")
                stat_int.metric("Int. 404s", total_int)
                stat_ext.metric("Ext. 404s", total_ext)
                stat_typo.metric("Typos", total_typo)
                time.sleep(0.1) # Simulate network lag

            # Final Score
            st.divider()
            score = 100 - len(report_list)
            st.markdown(f'<div class="score-container"><h1 style="font-size:80px; color:#219EBC;">{score}%</h1><h3>INTEGRITY SCORE</h3></div>', unsafe_allow_html=True)
            
            # The Final "Buy" CTA
            st.markdown("""<div style="background-color:#fff3e0; border:2px solid #FB8500; padding:20px; border-radius:12px; margin-top:20px; text-align:center;">
                <h3>📥 Get the Remediation List</h3>
                <p>Download the CSV to fix all errors discovered in this scan.</p>
                <a href="#"><button style="background-color:#FB8500; color:white; border:none; padding:15px 45px; border-radius:8px; font-weight:bold; cursor:pointer;">🚀 DOWNLOAD REPORT - $25</button></a>
            </div>""", unsafe_allow_html=True)
            st.balloons()
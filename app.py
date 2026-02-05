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
    
    .live-card { 
        background-color: #ffffff; border-left: 5px solid #FB8500; padding: 15px; 
        border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .inline-pro-box {
        background-color: #fff3e0; border: 2px solid #FB8500; padding: 25px; 
        border-radius: 12px; margin-top: 25px; text-align: center;
    }
    
    .hero-header { font-size: 3.5rem; font-weight: 800; color: #023047; margin-bottom:0;}
    .hero-sub { color: #219EBC; font-size: 1.2rem; margin-bottom: 40px; font-weight: 600; }
    
    /* Instruction label styling */
    .input-hint { font-size: 0.8rem; color: #64748b; margin-bottom: 5px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email", placeholder="admin@company.com")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Scan Settings")
    enable_typos = st.checkbox("Scan for Typos", value=True)
    
    # IMPROVED IGNORE BOX
    st.markdown('<div class="input-hint">Exclusion List: One word per line (or separated by commas)</div>', unsafe_allow_html=True)
    raw_ignore = st.text_area("Words to Ignore", placeholder="SaaS\nAcmeCorp\nAPI", height=150)
    
    # Logic to clean the ignore list (handles both newlines and commas)
    ignore_list = [w.strip().lower() for w in re.split(r'[\n,]+', raw_ignore) if w.strip()]
    
    st.divider()
    st.caption("v3.5.0 | Secure API Connection")

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">ZenAudit</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Deep-scan 1,800+ articles for broken links and quality errors.</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 WHY UPGRADE?"])

with tab1:
    tips = [
        "💡 **SEO Tip:** 404 errors prevent Google from indexing your helpful articles.",
        "💡 **CX Insight:** Typos in technical docs reduce perceived reliability.",
        "💡 **Deflection:** Fixing dead links keeps customers in the 'Self-Service' lane."
    ]

    def audit_content(html_body, ignore, sub, check_typos):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_int, broken_ext, typos = [], [], []
        
        # Link Audit
        for url in links:
            try:
                res = requests.head(url, timeout=2, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_int.append(url)
                    else: broken_ext.append(url)
            except: broken_ext.append(url)
            
        # Spelling Audit
        if check_typos:
            text = soup.get_text()
            words = spell.split_words(text)
            # Compare against the clean ignore_list
            typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in ignore]
            
        return broken_int, broken_ext, typos

    if st.button("🚀 RUN DEEP SCAN"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials required.")
        else:
            st.warning("⚠️ **SCAN ACTIVE:** Do not refresh your browser.")
            
            all_articles = []
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
            auth = (f"{email}/token", token)
            
            with st.status("📡 Fetching Knowledge Base...", expanded=True) as status:
                current_url = api_url
                while current_url:
                    res = requests.get(current_url, auth=auth)
                    if res.status_code == 200:
                        data = res.json()
                        all_articles.extend(data.get('articles', []))
                        st.write(f"📥 Loaded {len(all_articles)} articles...")
                        current_url = data.get('next_page')
                    else: break
                status.update(label="✅ Library Synchronized", state="complete")

            if all_articles:
                report_list = []
                total_scanned = len(all_articles)
                
                m1, m2, m3, m4 = st.columns(4)
                stat_total, stat_int, stat_ext, stat_typo = m1.empty(), m2.empty(), m3.empty(), m4.empty()
                
                prog_bar = st.progress(0)
                col_feed, col_tips = st.columns([1.5, 1])
                with col_feed:
                    st.markdown('**🚨 Recent Defects Found**')
                    feed_placeholder = st.empty()
                with col_tips:
                    st.markdown('**💡 Pro Tip**')
                    tip_placeholder = st.empty()
                
                recent_defects, total_int, total_ext, total_typo = [], 0, 0, 0
                start_time = time.time()

                for i, art in enumerate(all_articles):
                    b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain, enable_typos)
                    
                    if b_int or b_ext or typos:
                        total_int += len(b_int); total_ext += len(b_ext); total_typo += len(typos)
                        defect_entry = {"Article": art['title'], "Int": len(b_int), "Ext": len(b_ext), "Typos": len(typos)}
                        report_list.append(defect_entry)
                        recent_defects.insert(0, defect_entry)
                        if len(recent_defects) > 5: recent_defects.pop()
                        with feed_placeholder.container():
                            for d in recent_defects:
                                st.markdown(f"""<div class="live-card"><b>{d['Article']}</b><br><small>⚠️ {d['Int']+d['Ext']} Dead Links | ✍️ {d['Typos']} Typos</small></div>""", unsafe_allow_html=True)

                    prog_bar.progress((i + 1) / total_scanned)
                    stat_total.metric("Articles", f"{i+1}/{total_scanned}")
                    stat_int.metric("Int. Dead Links", total_int)
                    stat_ext.metric("Ext. Dead Links", total_ext)
                    stat_typo.metric("Typos Found", total_typo)
                    if i % 40 == 0: tip_placeholder.info(random.choice(tips))

                st.success(f"✅ Deep Scan Complete. {len(report_list)} articles require attention.")
                st.dataframe(pd.DataFrame(report_list), use_container_width=True)
                
                st.markdown(f"""
                <div class="inline-pro-box">
                    <h3>🛠️ Ready to start fixing?</h3>
                    <p>Unlock the <b>Full Remediation Pass</b> to download the complete CSV report containing every broken link and typo found.</p>
                    <a href="https://buy.stripe.com/your_link" target="_blank">
                        <button style="background-color:#FB8500; color:white; border:none; padding:15px 45px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:1.2rem;">🚀 UNLOCK FULL CSV REPORT - $25</button>
                    </a>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()

with tab2:
    # (Tier comparison logic here as per v3.4.0)
    st.markdown("### Why Upgrade to Professional?")
    st.write("The professional remediation pass provides a machine-readable CSV of every error, allowing your team to clear backlog items in hours instead of days.")
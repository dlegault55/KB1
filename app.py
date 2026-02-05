import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { 
        background-color: #219EBC; color: white; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    .stButton>button:hover { background-color: #023047; color: #FFB703; border: 1px solid #FFB703; }
    
    .value-prop-box {
        background-color: #8ECAE6; padding: 25px; border-radius: 12px;
        border: 2px solid #219EBC; text-align: center; color: #023047; min-height: 200px;
    }
    
    .hero-header { font-size: 3.5rem; font-weight: 800; color: #023047; margin-bottom:0;}
    .hero-sub { color: #219EBC; font-size: 1.2rem; margin-bottom: 40px; font-weight: 600; }
    
    .score-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;
    }
    
    .score-circle {
        background-color: #023047; color: #FFB703; border-radius: 50%;
        width: 110px; height: 110px; line-height: 110px; font-size: 32px;
        font-weight: bold; text-align: center; border: 4px solid #FB8500;
        margin-bottom: 5px;
    }
    
    .pro-card {
        text-align: center; padding: 30px; border: 3px solid #FB8500;
        border-radius: 15px; background-color: #ffffff; box-shadow: 0 4px 15px rgba(251, 133, 0, 0.1);
    }
    
    .legal-footer { font-size: 0.7rem; color: #64748b; margin-top: 30px; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    st.caption("Content Integrity for Zendesk®")
    
    with st.expander("📖 QUICK START GUIDE", expanded=True):
        st.markdown("""
        1. **Subdomain:** The part before `.zendesk.com`.
        2. **Email:** Your admin login email.
        3. **API Token:** In **Admin Center > Apps & Integrations > Zendesk API**.
        """)

    st.header("🔑 Connection")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email", placeholder="admin@company.com")
    token = st.text_input("API Token", type="password")
    
    if st.button("🔌 Test Connection"):
        if subdomain and email and token:
            test_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/categories.json"
            try:
                res = requests.get(test_url, auth=(f"{email}/token", token))
                if res.status_code == 200: st.success("✅ Connection Verified!")
                else: st.error(f"❌ Failed: {res.status_code}")
            except: st.error("❌ Connection Timeout")
        else: st.warning("Fill credentials first")

    st.divider()
    st.header("⚙️ Audit Scope")
    enable_typos = st.checkbox("Include Spellcheck (QA)", value=True)
    ignore_list = st.text_area("Exclusion List", placeholder="BrandNames\nJargon").split('\n')
    
    st.divider()
    st.markdown('<div class="legal-footer">Zendesk® is a trademark of Zendesk, Inc. ZenAudit is not affiliated with Zendesk, Inc.</div>', unsafe_allow_html=True)

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">ZenAudit</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">The High-Performance Content Integrity Suite for Zendesk® Guide</div>', unsafe_allow_html=True)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown('<div class="value-prop-box"><h1>📉</h1><h3>Slash Tickets</h3><p>Stop "silent friction" by fixing the self-service journey.</p></div>', unsafe_allow_html=True)
with col_v2:
    st.markdown('<div class="value-prop-box"><h1>💎</h1><h3>Protect Brand</h3><p>Maintain flawless CX by eliminating typos and 404s at scale.</p></div>', unsafe_allow_html=True)
with col_v3:
    st.markdown('<div class="value-prop-box"><h1>🔍</h1><h3>Uncover Dark Content</h3><p>Ensure search engines can index 100% of your knowledge base.</p></div>', unsafe_allow_html=True)

st.divider()

# --- 5. TABS ---
tab1, tab2 = st.tabs(["🚀 EXECUTE AUDIT", "💎 PROFESSIONAL ACCESS"])

with tab1:
    def audit_content(html_body, ignore, sub, check_typos):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_int, broken_ext = [], []
        for url in links:
            try:
                res = requests.head(url, timeout=2, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_int.append(url)
                    else: broken_ext.append(url)
            except: broken_ext.append(url)
        typos = []
        if check_typos:
            text = soup.get_text()
            words = spell.split_words(text)
            typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in [i.lower() for i in ignore]]
        return broken_int, broken_ext, typos

    if st.button("🚀 INITIALIZE SYSTEM-WIDE CONTENT AUDIT"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials Required in Sidebar.")
        else:
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
            auth = (f"{email}/token", token)
            try:
                response = requests.get(api_url, auth=auth)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    report_list = []
                    progress_bar = st.progress(0)
                    for i, art in enumerate(articles):
                        progress_bar.progress((i + 1) / len(articles))
                        b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain, enable_typos)
                        if b_int or b_ext or typos:
                            report_list.append({
                                "Article": art['title'], "Int Failures": len(b_int), 
                                "Ext Failures": len(b_ext), "Typos": len(typos), "Link": art['html_url']
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        total_scanned = len(articles)
                        defective_articles = len(df)
                        integrity_score = int(((total_scanned - defective_articles) / total_scanned) * 100)
                        
                        st.subheader("📊 Executive Audit Summary")
                        
                        # Added Total Scanned and Alignement Fix
                        sc0, sc1, sc2, sc3, sc4 = st.columns([1,1,1,1,1.5])
                        sc0.metric("Total Articles", total_scanned)
                        sc1.metric("Internal Failures", df['Int Failures'].sum())
                        sc2.metric("External Failures", df['Ext Failures'].sum())
                        sc3.metric("QA Typos", df['Typos'].sum())
                        
                        with sc4:
                            st.markdown(f"""
                            <div class="score-container">
                                <div class="score-circle">{integrity_score}%</div>
                                <div style="font-size: 0.8rem; color: #64748b; font-weight:bold;">INTEGRITY SCORE</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.divider()
                        c_left, c_right = st.columns([2, 1])
                        with c_left:
                            st.markdown(f"### How your score is generated")
                            st.write(f"Your score is based on **defect density**. Out of every 100 articles scanned, **{100 - integrity_score}** contain at least one broken link or spelling error.")
                            
                            if integrity_score < 70:
                                st.error(f"🚨 **Critical Level:** A defect rate of {100-integrity_score}% indicates severe 'Support Debt'. Fixing these issues is the fastest way to reduce inbound tickets.")
                            elif integrity_score < 90:
                                st.warning(f"⚠️ **Maintenance Warning:** A defect rate of {100-integrity_score}% shows content drift. Aim for under 10 defects per 100 articles.")
                            else:
                                st.success(f"🌟 **Elite Level:** Your defect rate is impressively low. Your content is a reliable self-service engine.")
                        
                        with c_right:
                            st.markdown("""
                            **Benchmark Scale:**
                            * **95%+** : 🏆 Elite (Defects < 5)
                            * **85-94%** : ✅ Healthy (Defects < 15)
                            * **70-84%** : ⚠️ Warning (Defects < 30)
                            * **<70%** : 🚨 Critical (Defects 30+)
                            """, unsafe_allow_html=True)

                        st.divider()
                        search = st.text_input("🔍 Search results by article title...")
                        if search:
                            df = df[df['Article'].str.contains(search, case=False)]
                        
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 DOWNLOAD AUDIT REPORT ($25)", data=df.to_csv(index=False).encode('utf-8'), file_name=f"ZenAudit_{subdomain}.csv", mime="text/csv")
                    else:
                        st.success(f"🌟 100% Content Integrity across {len(articles)} articles!")
                else: st.error(f"❌ Connection Error {response.status_code}.")
            except Exception as e: st.error(f"❌ Failure: {e}")

with tab2:
    st.markdown('<h2 style="text-align:center; color:#023047;">Strategic Content Governance</h2>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:30px; border:2px solid #023047; border-radius:12px; height:100%;"><h3>Starter</h3><h2>FREE</h2><p>Unlimited system scans<br>Live Integrity Scoring<br>Article-level error search</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""<div class="pro-card"><h3 style="color:#FB8500;">Professional</h3><h2 style="color:#023047;">$25</h2><p><b>Full CSV Export Unlocked</b><br>Bulk Remediation Data<br>Team Distribution Ready</p><a href="https://buy.stripe.com/your_link" target="_blank"><button style="background-color:#FB8500; color:white; border:none; padding:15px 30px; border-radius:8px; font-weight:bold; cursor:pointer; width:100%;">🚀 UNLOCK FULL REPORT</button></a></div>""", unsafe_allow_html=True)
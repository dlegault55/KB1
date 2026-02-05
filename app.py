import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling (Cleaned up - removed circle CSS)
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
        1. **Subdomain:** Part before `.zendesk.com`.
        2. **Email:** Admin login email.
        3. **API Token:** Generate in **Zendesk Admin Center > Apps & Integrations > Zendesk API**.
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
            st.warning("⚠️ Credentials Required.")
        else:
            all_articles = []
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
            auth = (f"{email}/token", token)
            
            with st.status("📡 Connecting to Zendesk...", expanded=True) as status:
                current_url = api_url
                while current_url:
                    res = requests.get(current_url, auth=auth)
                    if res.status_code == 200:
                        data = res.json()
                        all_articles.extend(data.get('articles', []))
                        st.write(f"📥 Synced {len(all_articles)} articles...")
                        current_url = data.get('next_page')
                    else:
                        st.error(f"Error: {res.status_code}")
                        break
                status.update(label="✅ Library Synced", state="complete", expanded=False)

            if all_articles:
                report_list = []
                total_scanned = len(all_articles)
                prog_text = st.empty()
                prog_bar = st.progress(0)
                start_time = time.time()

                for i, art in enumerate(all_articles):
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (i + 1)
                    rem_time = avg_time * (total_scanned - (i + 1))
                    
                    prog_text.markdown(f"**Scanning:** {i+1}/{total_scanned} | Est. remaining: **{int(rem_time // 60)}m {int(rem_time % 60)}s**")
                    prog_bar.progress((i + 1) / total_scanned)
                    
                    b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain, enable_typos)
                    if b_int or b_ext or typos:
                        report_list.append({
                            "Article": art['title'], "Int Failures": len(b_int), 
                            "Ext Failures": len(b_ext), "Typos": len(typos), "Link": art['html_url']
                        })
                
                prog_text.empty()
                prog_bar.empty()

                if report_list:
                    df = pd.DataFrame(report_list)
                    defective_count = len(df)
                    integrity_score = int(((total_scanned - defective_count) / total_scanned) * 100)
                    
                    st.subheader("📊 Executive Audit Summary")
                    # ALLIGNMENT FIX: Using native Streamlit metrics for everything
                    sc0, sc1, sc2, sc3, sc4 = st.columns(5)
                    sc0.metric("Total Scanned", total_scanned)
                    sc1.metric("Internal 404s", df['Int Failures'].sum())
                    sc2.metric("External 404s", df['Ext Failures'].sum())
                    sc3.metric("QA Typos", df['Typos'].sum())
                    sc4.metric("Integrity Score", f"{integrity_score}%")
                    
                    st.divider()
                    c_left, c_right = st.columns([2, 1])
                    with c_left:
                        st.markdown(f"### Score Logic: Defect Density")
                        st.info(f"Your score indicates that **{100 - integrity_score} out of every 100 articles** contain at least one defect. High performing teams aim for **95%+**.")
                        if integrity_score < 70:
                            st.error("🚨 **Critical:** High Support Debt detected. Broken links drive tickets.")
                        elif integrity_score < 90:
                            st.warning("⚠️ **Maintenance:** Content drift detected. Triage suggested.")
                        else:
                            st.success("🌟 **Elite:** Your content is a reliable deflection engine.")
                    
                    with c_right:
                        st.markdown("""
                        **Benchmark Scale:**
                        - **95%+** : 🏆 Elite
                        - **85-94%** : ✅ Healthy
                        - **70-84%** : ⚠️ Warning
                        - **<70%** : 🚨 Critical
                        """)

                    st.divider()
                    search = st.text_input("🔍 Search article failures...")
                    if search:
                        df = df[df['Article'].str.contains(search, case=False)]
                    
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 DOWNLOAD AUDIT REPORT ($25)", data=df.to_csv(index=False).encode('utf-8'), file_name=f"ZenAudit_Report.csv", mime="text/csv")
                else:
                    st.success(f"🌟 100% Content Integrity across {total_scanned} articles!")

with tab2:
    st.markdown('<h2 style="text-align:center; color:#023047;">Strategic Content Governance</h2>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:30px; border:2px solid #023047; border-radius:12px; height:100%;"><h3>Starter</h3><h2>FREE</h2><p>Unlimited system scans<br>Live Integrity Scoring<br>Searchable defect table</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""<div class="pro-card"><h3 style="color:#FB8500;">Professional</h3><h2 style="color:#023047;">$25</h2><p><b>Full CSV Export Unlocked</b><br>Bulk Remediation Data<br>Team Distribution Ready</p><a href="https://buy.stripe.com/your_link" target="_blank"><button style="background-color:#FB8500; color:white; border:none; padding:15px 30px; border-radius:8px; font-weight:bold; cursor:pointer; width:100%;">🚀 UNLOCK FULL REPORT</button></a></div>""", unsafe_allow_html=True)
import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling with High-Contrast Palette
st.markdown("""
    <style>
    .stButton>button { 
        background-color: #219EBC; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        width: 100%;
        height: 3.5em;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none;
    }
    .stButton>button:hover { background-color: #023047; color: #FFB703; border: 1px solid #FFB703; }
    
    .value-prop-box {
        background-color: #8ECAE6;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #219EBC;
        text-align: center;
        color: #023047;
        min-height: 220px;
    }
    
    .hero-header { font-size: 3.5rem; font-weight: 800; color: #023047; margin-bottom:0;}
    .hero-sub { color: #219EBC; font-size: 1.2rem; margin-bottom: 40px; font-weight: 600; }
    
    .pro-card {
        text-align: center;
        padding: 30px;
        border: 3px solid #FB8500;
        border-radius: 15px;
        background-color: #ffffff;
        box-shadow: 0 4px 15px rgba(251, 133, 0, 0.1);
    }
    
    .legal-footer {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 50px;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    st.caption("Content Integrity for Zendesk®")
    
    st.divider()
    st.header("🔑 Connection")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email", placeholder="admin@company.com")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Scope")
    enable_typos = st.checkbox("Include Spellcheck (QA)", value=True)
    ignore_list = st.text_area("Exclusion List", placeholder="BrandNames\nJargon").split('\n')
    
    st.divider()
    st.markdown("""
    <div class="legal-footer">
        <b>Disclaimer:</b> Zendesk® is a trademark of Zendesk, Inc. <br>
        ZenAudit is an independent tool and is not affiliated with or endorsed by Zendesk, Inc.
    </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">ZenAudit</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">The High-Performance Content Integrity Suite for Zendesk® Guide</div>', unsafe_allow_html=True)

# THE NEW & IMPROVED MARKETING PILLARS

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    st.markdown("""
    <div class="value-prop-box">
        <h1 style='margin-bottom:10px;'>📉</h1>
        <h3 style='margin-top:0;'>Slash Ticket Volume</h3>
        <p>Broken links are the #1 cause of "silent" friction. Fix the self-service journey and stop avoidable tickets before they reach your agents.</p>
    </div>
    """, unsafe_allow_html=True)

with col_v2:
    st.markdown("""
    <div class="value-prop-box">
        <h1 style='margin-bottom:10px;'>💎</h1>
        <h3 style='margin-top:0;'>Protect Brand Authority</h3>
        <p>Your Help Center is your digital storefront. Don't let 404 errors and typos signal a neglected product. Maintain a flawless CX at scale.</p>
    </div>
    """, unsafe_allow_html=True)

with col_v3:
    st.markdown("""
    <div class="value-prop-box">
        <h1 style='margin-bottom:10px;'>🔍</h1>
        <h3 style='margin-top:0;'>Uncover Dark Content</h3>
        <p>Ensure 100% of your articles are discoverable. Our deep-link validation helps search engines index your content correctly for maximum ROI.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- 5. TABS ---
tab1, tab2 = st.tabs(["🚀 EXECUTE AUDIT", "💎 PROFESSIONAL ACCESS"])

with tab1:
    # (Audit logic remains the same as v2.6)
    def audit_content(html_body, ignore, sub, check_typos):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_int, broken_ext = [], []
        for url in links:
            try:
                res = requests.head(url, timeout=3, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_int.append(url)
                    else: broken_ext.append(url)
            except:
                broken_ext.append(url)
        typos = []
        if check_typos:
            text = soup.get_text()
            words = spell.split_words(text)
            typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in [i.lower() for i in ignore]]
        return broken_int, broken_ext, typos

    if st.button("🚀 INITIALIZE SYSTEM-WIDE CONTENT AUDIT"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials Required: Please configure the sidebar settings.")
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
                                "Article": art['title'], 
                                "Internal Failures": len(b_int), 
                                "External Failures": len(b_ext), 
                                "Typos": len(typos),
                                "Article Link": art['html_url']
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Executive Results Summary")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Broken Internal Links", df['Internal Failures'].sum())
                        c2.metric("Broken External Links", df['External Failures'].sum())
                        c3.metric("Spelling/QA Risks", df['Typos'].sum() if enable_typos else "N/A")
                        
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 DOWNLOAD AUDIT REPORT ($25)", data=df.to_csv(index=False).encode('utf-8'), file_name=f"ZenAudit_{subdomain}.csv", mime="text/csv")
                    else:
                        st.success("🌟 100% Content Integrity! No errors detected.")
                else:
                    st.error(f"❌ Connection Error {response.status_code}.")
            except Exception as e:
                st.error(f"❌ System Failure: {e}")

with tab2:
    st.markdown("""
    <h2 style="text-align:center; color:#023047;">Scale Your Quality Control</h2>
    <p style="text-align:center; font-size:1.1rem;">Trusted by meticulous Documentation Managers to maintain enterprise standards.</p>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:30px; border:2px solid #023047; border-radius:12px; height:100%;"><h3>Starter Engine</h3><h2 style="color:#666;">FREE</h2><p>Unlimited on-screen article scans<br>Real-time integrity metrics</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="pro-card">
            <h3 style="color:#FB8500;">Professional Pass</h3>
            <h2 style="color:#023047;">$25</h2>
            <p><b>Full CSV Export Unlocked</b><br>Complete Remediation Data<br>Bulk Article URLs</p>
            <a href="https://buy.stripe.com/your_link" target="_blank">
                <button style="background-color:#FB8500; color:white; border:none; padding:15px 30px; border-radius:8px; font-weight:bold; cursor:pointer; width:100%; font-size:1.1rem;">🚀 UNLOCK FULL REPORT</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
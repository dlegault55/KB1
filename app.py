import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling with Custom Palette
st.markdown("""
    <style>
    /* Main Action Button - #219EBC */
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
    .stButton>button:hover { background-color: #023047; color: #FFB703; }
    
    /* Value Props - #8ECAE6 Sky Blue */
    .value-prop-box {
        background-color: #8ECAE6;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #219EBC;
        text-align: center;
        color: #023047;
    }
    
    /* Hero Header - #023047 Deep Navy */
    .hero-header { font-size: 3.2rem; font-weight: 800; color: #023047; margin-bottom:0;}
    
    /* Pro Card - #FB8500 Orange Focus */
    .pro-card {
        text-align: center;
        padding: 30px;
        border: 3px solid #FB8500;
        border-radius: 15px;
        background-color: #fcfcfc;
    }
    
    /* Disclaimer Text */
    .legal-footer {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 50px;
        line-height: 1.2;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    
    with st.expander("📖 Connection Help", expanded=False):
        st.write("""
        - **Subdomain:** The name before '.zendesk.com'.
        - **Email:** Your admin login email.
        - **Token:** Found in Zendesk Admin Center > Apps & Integrations > Zendesk API.
        """)

    st.header("🔑 Connection")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email", placeholder="admin@acme.com")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Scope")
    enable_typos = st.checkbox("Enable QA Spellcheck", value=True)
    ignore_list = st.text_area("Exclusion List", placeholder="Jargon\nBrandNames").split('\n')
    
    # --- MANDATORY TRADEMARK DISCLAIMER ---
    st.markdown("""
    <div class="legal-footer">
        Zendesk® is a trademark of Zendesk, Inc. <br>
        ZenAudit is not affiliated with or endorsed by Zendesk, Inc.
    </div>
    """, unsafe_allow_html=True)

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">🛡️ ZenAudit</div>', unsafe_allow_html=True)
st.markdown("<h4 style='color:#219EBC; margin-bottom:30px;'>Integrity Tools for the Zendesk® Ecosystem</h4>", unsafe_allow_html=True)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("""<div class="value-prop-box"><h3>📉</h3><b>Deflect Tickets</b><br>Fix the self-service path.</div>""", unsafe_allow_html=True)
with col_v2:
    st.markdown("""<div class="value-prop-box"><h3>🤝</h3><b>Build Trust</b><br>Zero typos. Zero 404s.</div>""", unsafe_allow_html=True)
with col_v3:
    st.markdown("""<div class="value-prop-box"><h3>🚀</h3><b>SEO Health</b><br>Rank higher with clean links.</div>""", unsafe_allow_html=True)

st.divider()

# --- 5. TABS ---
tab1, tab2 = st.tabs(["🚀 RUN AUDIT", "💎 PRO ACCESS"])

with tab1:
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

    if st.button("🚀 START FULL CONTENT AUDIT"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Please provide connection details in the sidebar.")
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
                                "Internal 404s": len(b_int), 
                                "External 404s": len(b_ext), 
                                "Typos": len(typos),
                                "Link": art['html_url']
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Audit Results")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Internal Failures", df['Internal 404s'].sum())
                        c2.metric("External Failures", df['External 404s'].sum())
                        c3.metric("QA Typos", df['Typos'].sum() if enable_typos else "N/A")
                        
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 DOWNLOAD AUDIT REPORT ($25)", data=csv, file_name=f"ZenAudit_{subdomain}.csv", mime="text/csv")
                    else:
                        st.success("🌟 100% Integrity Score! No issues found.")
                else:
                    st.error(f"❌ Connection Failed ({response.status_code}).")
            except Exception as e:
                st.error(f"❌ System Error: {e}")

with tab2:
    st.markdown("""
    <h3 style="text-align:center; color:#023047;">Why Professional Teams use ZenAudit</h3>
    <p style="text-align:center;">Stop manual link checking. Scale your Knowledge Base with confidence.</p>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:20px; border:2px solid #023047; border-radius:10px;"><h3>Basic Engine</h3><h2>FREE</h2><p>Unlimited on-screen reports<br>Zendesk native logic</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="pro-card">
            <h3 style="color:#FB8500;">Professional Pass</h3>
            <h2 style="color:#023047;">$25</h2>
            <p><b>CSV Export Functionality</b><br>Full Remediation Data</p>
            <a href="https://buy.stripe.com/your_link" target="_blank">
                <button style="background-color:#FB8500; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">🚀 UNLOCK EXPORT</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
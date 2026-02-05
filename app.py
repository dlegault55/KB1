import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling with Custom Palette
st.markdown("""
    <style>
    /* Main Background & Text */
    .main {
        background-color: #ffffff;
    }
    
    /* Audit Button - Blue-Green */
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
    .stButton>button:hover {
        background-color: #023047;
        color: #FFB703;
    }

    /* Value Props - Sky Blue Background */
    .value-prop-box {
        background-color: #8ECAE6;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #219EBC;
        text-align: center;
        color: #023047;
    }
    
    /* Hero Header - Deep Navy */
    .hero-header {
        font-size: 3rem;
        font-weight: 800;
        color: #023047;
    }

    /* Pricing Card - Orange Focus */
    .pro-card {
        text-align: center;
        padding: 30px;
        border: 3px solid #FB8500;
        border-radius: 15px;
        background-color: #fcfcfc;
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        color: #023047;
        font-weight: bold;
    }

    /* Comparison Table */
    .comp-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    .comp-table th {
        background-color: #023047;
        color: #8ECAE6;
        padding: 12px;
    }
    .comp-table td {
        border: 1px solid #8ECAE6;
        padding: 10px;
        text-align: center;
    }
    .highlight-cell {
        background-color: #FFB703;
        color: #023047;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC;">🛡️ Settings</h1>', unsafe_allow_html=True)
    st.info("🎯 **Target:** Zendesk Guide")
    subdomain = st.text_input("Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Configuration")
    ignore_list = st.text_area("Exclusion List", placeholder="Zendesk\nSaaS").split('\n')
    
    st.divider()
    st.caption("Link Warden Pro v2.4")

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">🛡️ Link Warden Pro</div>', unsafe_allow_html=True)
st.markdown("<h4 style='color:#219EBC;'>Zendesk Content Integrity Suite</h4>", unsafe_allow_html=True)

# Value Props Section
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("""<div class="value-prop-box"><h2 style='margin:0;'>📉</h2><b>Deflect Tickets</b><br>Fix the self-service path.</div>""", unsafe_allow_html=True)
with col_v2:
    st.markdown("""<div class="value-prop-box"><h2 style='margin:0;'>🤝</h2><b>Build Trust</b><br>Zero typos. Zero 404s.</div>""", unsafe_allow_html=True)
with col_v3:
    st.markdown("""<div class="value-prop-box"><h2 style='margin:0;'>🚀</h2><b>SEO Health</b><br>Rank higher with clean links.</div>""", unsafe_allow_html=True)

st.divider()

# --- 5. TABS ---
tab1, tab2 = st.tabs(["🚀 AUDIT ENGINE", "💎 PRICING & COMPARISON"])

with tab1:
    def audit_content(html_body, ignore, sub):
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
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in [i.lower() for i in ignore]]
        return broken_int, broken_ext, typos

    if st.button("🚀 INITIALIZE AUDIT"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials Required in Sidebar")
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
                        b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain)
                        if b_int or b_ext or typos:
                            report_list.append({
                                "Title": art['title'], "Internal 404s": len(b_int), 
                                "External 404s": len(b_ext), "Typos": len(typos),
                                "Details": f"Links: {len(b_int)+len(b_ext)}, Typos: {', '.join(typos[:5])}"
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Audit Summary")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Internal Failures", df['Internal 404s'].sum())
                        c2.metric("External Failures", df['External 404s'].sum())
                        c3.metric("QA Typo Risks", df['Typos'].sum())
                        
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 DOWNLOAD CSV REPORT", data=csv, file_name="audit.csv", mime="text/csv")
                    else:
                        st.success("Perfect Integrity!")
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.markdown("""
    <table class="comp-table">
        <tr><th>Metric</th><th>Manual Audit</th><th class="highlight-cell">Link Warden Pro</th></tr>
        <tr><td>Cost</td><td>$25/hr Labor</td><td class="highlight-cell">$25 One-Time</td></tr>
        <tr><td>Speed</td><td>Days</td><td class="highlight-cell">Seconds</td></tr>
        <tr><td>Zendesk Native</td><td>No</td><td class="highlight-cell">Yes</td></tr>
    </table>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:20px; border:2px solid #023047; border-radius:10px;"><h3>Basic</h3><h2>FREE</h2><p>On-screen results</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="pro-card">
            <h3 style="color:#FB8500;">Professional</h3>
            <h2 style="color:#023047;">$25</h2>
            <p><b>Unlock CSV Exports</b><br>Full Remediation Logs</p>
            <a href="https://buy.stripe.com/your_link" target="_blank">
                <button style="background-color:#FB8500; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">🚀 UPGRADE NOW</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
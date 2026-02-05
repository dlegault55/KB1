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
    .value-prop-box {
        background-color: #8ECAE6;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #219EBC;
        text-align: center;
        color: #023047;
    }
    .hero-header { font-size: 3rem; font-weight: 800; color: #023047; }
    .pro-card {
        text-align: center;
        padding: 30px;
        border: 3px solid #FB8500;
        border-radius: 15px;
        background-color: #fcfcfc;
    }
    .comp-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .comp-table th { background-color: #023047; color: #8ECAE6; padding: 12px; }
    .comp-table td { border: 1px solid #8ECAE6; padding: 10px; text-align: center; }
    .highlight-cell { background-color: #FFB703; color: #023047; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (With Instructions & Toggle) ---
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC;">🛡️ Link Warden</h1>', unsafe_allow_html=True)
    
    with st.expander("📖 Quick Start Guide", expanded=False):
        st.write("""
        1. **Subdomain:** The part before '.zendesk.com' in your URL.
        2. **Email:** Your Zendesk admin login email.
        3. **API Token:** Go to **Zendesk Admin Center > Apps & Integrations > Zendesk API**. Enable Token Access and create a new secret.
        """)

    st.header("🔑 Connection")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support", help="If your URL is acme-support.zendesk.com, enter 'acme-support'")
    email = st.text_input("Admin Email", placeholder="admin@acme.com", help="The email you use to log into your Zendesk dashboard.")
    token = st.text_input("API Token", type="password", help="Ensure 'Token Access' is enabled in your Zendesk API settings.")
    
    st.divider()
    st.header("⚙️ Audit Scope")
    # THE TYPO TOGGLE
    enable_typos = st.checkbox("Enable Spellcheck (Beta)", value=True, help="Uncheck this to speed up the scan if you only care about broken links.")
    ignore_list = st.text_area("Exclusion List", placeholder="Zendesk\nSaaS", help="Words to ignore during spellcheck.").split('\n')
    
    st.divider()
    st.caption("Link Warden Pro v2.5")

# --- 4. MAIN PAGE ---
st.markdown('<div class="hero-header">🛡️ Link Warden Pro</div>', unsafe_allow_html=True)
st.markdown("<h4 style='color:#219EBC;'>Zendesk Content Integrity Suite</h4>", unsafe_allow_html=True)

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
    def audit_content(html_body, ignore, sub, check_typos):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_int, broken_ext = [], []
        
        # Link Audit Logic
        for url in links:
            try:
                res = requests.head(url, timeout=3, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_int.append(url)
                    else: broken_ext.append(url)
            except:
                broken_ext.append(url)
        
        # Optional Typo Logic
        typos = []
        if check_typos:
            text = soup.get_text()
            words = spell.split_words(text)
            typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in [i.lower() for i in ignore]]
            
        return broken_int, broken_ext, typos

    if st.button("🚀 INITIALIZE SYSTEM AUDIT"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials Required: Please fill out the connection settings in the sidebar.")
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
                                "Title": art['title'], "Internal 404s": len(b_int), 
                                "External 404s": len(b_ext), "Typos Found": len(typos),
                                "Article Link": art['html_url']
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Executive Results")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Internal Failures", df['Internal 404s'].sum())
                        c2.metric("External Failures", df['External 404s'].sum())
                        c3.metric("QA Typo Risks", df['Typos Found'].sum() if enable_typos else "N/A")
                        
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 DOWNLOAD CSV REPORT ($25)", data=csv, file_name=f"audit_{subdomain}.csv", mime="text/csv")
                    else:
                        st.success("🌟 Perfect Integrity! No issues detected.")
                else:
                    st.error(f"❌ Connection Error {response.status_code}. Check your API credentials.")
            except Exception as e:
                st.error(f"❌ System Failure: {e}")

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
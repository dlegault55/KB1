import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { 
        background-color: #007bff; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        width: 100%;
        height: 3.5em;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none;
    }
    .value-prop-box {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #d0e3ff;
        text-align: center;
        margin-bottom: 10px;
    }
    .hero-header {
        font-size: 2.8rem;
        font-weight: 800;
        color: #1e293b;
    }
    .comp-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 0.95rem;
    }
    .comp-table th, .comp-table td {
        padding: 12px;
        border: 1px solid #eee;
        text-align: center;
    }
    .highlight { background-color: #e7f3ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("🔑 Connection Settings")
    st.info("🎯 **Target Platform:** Zendesk Guide")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Configuration")
    ignore_list = st.text_area("Exclusion List", placeholder="Zendesk\nSaaS").split('\n')
    
    st.divider()
    st.write("🛰️ **Integration Roadmap**")
    st.caption("✅ Zendesk Guide")
    st.caption("⏳ Salesforce (Planned)")
    st.caption("⏳ HubSpot (Planned)")
    
    st.divider()
    st.caption("Link Warden Pro v2.3")

# --- 4. MAIN PAGE CONTENT ---
st.markdown('<div class="hero-header">🛡️ Link Warden Pro</div>', unsafe_allow_html=True)
st.markdown("### The High-Efficiency Integrity Suite for Zendesk Admins")

# Professional Value Props using Emojis (No broken image links)
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown("""<div class="value-prop-box"><h3>📉</h3><b>Deflect Tickets</b><br>Fix the journeys that force customers to contact support.</div>""", unsafe_allow_html=True)
with col_v2:
    st.markdown("""<div class="value-prop-box"><h3>🤝</h3><b>Build Trust</b><br>Eliminate typos and 404s to maintain brand authority.</div>""", unsafe_allow_html=True)
with col_v3:
    st.markdown("""<div class="value-prop-box"><h3>🚀</h3><b>SEO Health</b><br>Keep your Help Center discoverable and healthy.</div>""", unsafe_allow_html=True)

st.divider()

# --- 5. TABS ---
tab1, tab2 = st.tabs(["🚀 Audit Engine", "💎 Licensing & Comparison"])

with tab1:
    def audit_content(html_body, ignore, sub):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_internal, broken_external = [], []
        for url in links:
            try:
                res = requests.head(url, timeout=3, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_internal.append(f"{url} ({res.status_code})")
                    else: broken_external.append(f"{url} ({res.status_code})")
            except:
                if f"{sub}.zendesk.com" in url: broken_internal.append(f"{url} (Timeout)")
                else: broken_external.append(f"{url} (Timeout)")
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [word for word in spell.unknown(words) if not word.istitle() and len(word) > 2 and word.lower() not in [i.lower() for i in ignore]]
        return broken_internal, broken_external, typos

    if st.button("🚀 Initialize System-Wide Audit"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Connection Required: Provide your credentials in the sidebar.")
        else:
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
            auth = (f"{email}/token", token)
            start_time = time.time()
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
                                "Article Title": art['title'], "Zendesk URL": art['html_url'],
                                "Internal Failures": len(b_int), "External Failures": len(b_ext), "QA Typos": len(typos),
                                "Internal Details": ", ".join(b_int), "External Details": ", ".join(b_ext), "Typo Details": ", ".join(typos)
                            })
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Executive Audit Summary")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Scanned", len(articles))
                        c2.metric("Internal 🔗", df['Internal Failures'].sum())
                        c3.metric("External 🌐", df['External Failures'].sum())
                        c4.metric("Typos ✍️", df['QA Typos'].sum())
                        
                        st.info(f"⏱️ **Efficiency Gain:** Automated scan saved ~{round((len(articles)*5)/60, 1)} hours of manual review.")
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 DOWNLOAD DETAILED REPORT (CSV)", data=csv, file_name=f"LinkWarden_Audit.csv", mime="text/csv")
                    else:
                        st.success("🌟 Perfect Integrity! No issues found.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

with tab2:
    st.title("Strategic Value & Comparison")
    
    # Clean CSS Table (No images needed)
    st.markdown("""
    <table class="comp-table">
        <tr style="background-color:#f8f9fa;">
            <th>Metric</th>
            <th>Manual Audit</th>
            <th>SaaS Tools</th>
            <th class="highlight">Link Warden Pro</th>
        </tr>
        <tr>
            <td><b>Setup</b></td>
            <td>Hours</td>
            <td>15-30 Min</td>
            <td class="highlight">Instant</td>
        </tr>
        <tr>
            <td><b>Cost</b></td>
            <td>High Labor</td>
            <td>$300+/Year</td>
            <td class="highlight">$25 (Once)</td>
        </tr>
        <tr>
            <td><b>Privacy</b></td>
            <td>Manual</td>
            <td>Cloud Stored</td>
            <td class="highlight">Stateless</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div style="text-align:center; padding:20px; border:1px solid #ddd; border-radius:10px;"><h3>Standard</h3><h2>FREE</h2><p>Unlimited audits</p></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown('<div style="text-align:center; padding:20px; border:1px solid #007bff; border-radius:10px; background-color:#f0f7ff;"><h3>Professional</h3><h2>$25</h2><p><b>CSV Export Unlocked</b></p></div>', unsafe_allow_html=True)
        st.link_button("🚀 UPGRADE FOR EXPORT ACCESS", "https://buy.stripe.com/your_link")
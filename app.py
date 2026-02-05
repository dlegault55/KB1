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
    /* Main Action Button */
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
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    /* Value Props */
    .value-prop-box {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #d0e3ff;
        height: 100%;
    }
    /* Hero Section */
    .hero-header {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 5px;
        color: #1e293b;
    }
    /* Platform Badge */
    .platform-badge {
        display: inline-block;
        background-color: #e2e8f0;
        color: #475569;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 20px;
    }
    /* Comparison Table Styling */
    .comp-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.95rem;
        background-color: white;
    }
    .comp-table th, .comp-table td {
        padding: 15px;
        border: 1px solid #eee;
        text-align: center;
    }
    .comp-table th { background-color: #f8f9fa; color: #444; }
    .highlight { background-color: #e7f3ff; font-weight: bold; border: 2px solid #007bff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Persistent Controls) ---
with st.sidebar:
    st.header("🔑 Connection Settings")
    st.info("🎯 **Target Platform:** Zendesk Guide")
    
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Configuration")
    ignore_list = st.text_area("Exclusion List", 
                               help="Add brand names, product codes, or jargon to skip.",
                               placeholder="Zendesk\nSaaS").split('\n')
    
    st.divider()
    st.write("🛰️ **Integration Roadmap**")
    st.caption("✅ Zendesk Guide (Active)")
    st.caption("⏳ Salesforce Service Cloud (Planned)")
    st.caption("⏳ HubSpot Knowledge Base (Planned)")
    
    st.divider()
    st.caption("Link Warden Pro v2.2")
    st.info("🛡️ **Enterprise Security:** Stateless processing ensures your credentials and data are never stored.")

# --- 4. HERO & ROI SECTION ---
st.markdown('<div class="hero-header">🛡️ Link Warden Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="platform-badge">🧩 NATIVE ZENDESK INTEGRATION</div>', unsafe_allow_html=True)
st.markdown("### The High-Efficiency Integrity Suite for Zendesk Content Teams")

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    st.markdown('<div class="value-prop-box"><b>📉 Deflect Tickets</b><br>Broken links frustrate users and drive avoidable tickets. Fix the journey, lower the volume.</div>', unsafe_allow_html=True)
with col_v2:
    st.markdown('<div class="value-prop-box"><b>🤝 Build Authority</b><br>Typos and 404s signal neglected documentation. Maintain a world-class brand image.</div>', unsafe_allow_html=True)
with col_v3:
    st.markdown('<div class="value-prop-box"><b>🚀 SEO Health</b><br>Google penalizes dead internal structures. Keep your Help Center discoverable and healthy.</div>', unsafe_allow_html=True)

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
                    if f"{sub}.zendesk.com" in url:
                        broken_internal.append(f"{url} ({res.status_code})")
                    else:
                        broken_external.append(f"{url} ({res.status_code})")
            except:
                if f"{sub}.zendesk.com" in url:
                    broken_internal.append(f"{url} (Timeout)")
                else:
                    broken_external.append(f"{url} (Timeout)")
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [word for word in spell.unknown(words) 
                 if not word.istitle() and len(word) > 2 and word.lower() not in [i.lower() for i in ignore]]
        
        return broken_internal, broken_external, typos

    if st.button("🚀 Initialize System-Wide Audit"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Connection Required: Provide your Zendesk API credentials in the sidebar to begin.")
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
                    status_text = st.empty()

                    for i, art in enumerate(articles):
                        progress_bar.progress((i + 1) / len(articles))
                        status_text.text(f"Auditing Article {i+1} of {len(articles)}: {art['title']}")
                        
                        b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain)
                        
                        if b_int or b_ext or typos:
                            report_list.append({
                                "Article Title": art['title'],
                                "Zendesk URL": art['html_url'],
                                "Internal Failures": len(b_int),
                                "External Failures": len(b_ext),
                                "QA Typo Risks": len(typos),
                                "Broken Internal Details": ", ".join(b_int),
                                "Broken External Details": ", ".join(b_ext),
                                "Typo Details": ", ".join(typos)
                            })
                    
                    status_text.empty()
                    duration = round(time.time() - start_time, 1)
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Executive Audit Summary")
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Scanned", len(articles))
                        c2.metric("Internal Failures", df['Internal Failures'].sum())
                        c3.metric("External Failures", df['External Failures'].sum())
                        c4.metric("QA Typo Risks", df['QA Typo Risks'].sum())
                        
                        st.success(f"✅ Audit Complete in {duration}s. {len(report_list)} articles require integrity updates.")
                        
                        hours_saved = round((len(articles)*5)/60, 1)
                        st.info(f"⏱️ **Efficiency Gain:** This automated audit saved approximately **{hours_saved} hours** of manual review.")

                        st.divider()
                        st.write("### 📝 Full Diagnostic Log")
                        st.dataframe(df, use_container_width=True)

                        st.divider()
                        st.subheader("📥 Export Remediation Data")
                        st.write("Download the comprehensive CSV to distribute to your content team.")
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 DOWNLOAD DETAILED REPORT (CSV)",
                            data=csv,
                            file_name=f"LinkWarden_Audit_{subdomain}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success(f"🌟 Perfect Integrity! All {len(articles)} articles passed the diagnostic.")
                else:
                    st.error(f"❌ API Error {response.status_code}. Verify your Zendesk subdomain and token permissions.")
            except Exception as e:
                st.error(f"❌ Diagnostic Failure: {e}")

with tab2:
    st.title("Strategic Value & Licensing")
    
    st.markdown("""
    <table class="comp-table">
        <thead>
            <tr>
                <th>Audit Metric</th>
                <th>Manual Content Audit</th>
                <th>SaaS Subscription Tools</th>
                <th class="highlight">Link Warden Pro</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>Setup Time</b></td>
                <td>Days/Weeks</td>
                <td>15-30 Minutes</td>
                <td class="highlight">Instant</td>
            </tr>
            <tr>
                <td><b>Cost Structure</b></td>
                <td>High Labor Cost</td>
                <td>$300 - $1,200 / Year</td>
                <td class="highlight">$25 (One-Time)</td>
            </tr>
            <tr>
                <td><b>Platform Focus</b></td>
                <td>General</td>
                <td>General Website</td>
                <td class="highlight">Zendesk Specialized</td>
            </tr>
            <tr>
                <td><b>Data Privacy</b></td>
                <td>Manual Handling</td>
                <td>Stored Externally</td>
                <td class="highlight">Stateless / Secure</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div style="text-align:center; padding:30px; border:1px solid #ddd; border-radius:12px; height:100%;">
            <h3>Standard Engine</h3>
            <h2 style="color:#666;">FREE</h2>
            <p>Unlimited on-screen audits<br>Zendesk native diagnostic</p>
            <p style="font-size:0.8rem; color:#999;">No export functionality</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown("""
        <div style="text-align:center; padding:30px; border:1px solid #007bff; border-radius:12px; background-color:#f0f7ff; height:100%;">
            <h3>Professional Pass</h3>
            <h2 style="color:#007bff;">$25</h2>
            <p><b>Full CSV Export Unlocked</b><br>Internal vs External Failures<br>Full Typo Log</p>
            <p style="font-size:0.8rem; color:#007bff;">Instant download access</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("🚀 GET PROFESSIONAL EXPORT ACCESS", "https://buy.stripe.com/your_link")
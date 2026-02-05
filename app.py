import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro | Zendesk Integrity Tool", page_icon="🛡️", layout="wide")
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
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        color: #007bff;
    }
    .hero-text {
        font-size: 1.2rem;
        color: #444;
        background: #f0f7ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("🔑 Secure Connection")
    subdomain = st.text_input("Zendesk Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Intelligence")
    ignore_list = st.text_area("Brand Keywords to Ignore", 
                               help="Add names, acronyms, or jargon unique to your brand.",
                               placeholder="Zendesk\nSaaS\nOmnichannel").split('\n')
    
    st.divider()
    st.info("🛡️ **Enterprise Security:** We use HTTPS encryption and zero-data retention. Your credentials are never stored.")

# --- 4. NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🚀 Launch Audit", "🛡️ Why Integrity Matters", "💎 Pro Features"])

# --- TAB 1: THE AUDIT TOOL ---
with tab1:
    st.title("🛡️ Link Warden Pro")
    
    st.markdown("""
    <div class="hero-text">
    <b>Stop losing customers to 404s.</b> Broken links and typos signal a lack of attention to detail. 
    Link Warden Pro performs a deep-tissue scan of your Zendesk Help Center to ensure your 
    Knowledge Base remains a reliable, world-class resource.
    </div>
    """, unsafe_allow_html=True)
    
    def audit_content(html_body, ignore, sub):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        
        broken_internal = []
        broken_external = []
        
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
                    broken_internal.append(f"{url} (Offline)")
                else:
                    broken_external.append(f"{url} (Offline)")
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [word for word in spell.unknown(words) 
                 if not word.istitle() and len(word) > 2 and word.lower() not in [i.lower() for i in ignore]]
        
        return broken_internal, broken_external, typos

    if st.button("🚀 Start Deep Tissue Scan"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Action Required: Please provide your Zendesk credentials in the sidebar to initiate the audit.")
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
                        percent_complete = (i + 1) / len(articles)
                        progress_bar.progress(percent_complete)
                        status_text.text(f"🔍 Analyzing: {art['title']}")
                        
                        b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain)
                        
                        if b_int or b_ext or typos:
                            report_list.append({
                                "Article Title": art['title'],
                                "Zendesk URL": art['html_url'],
                                "Internal 404s": len(b_int),
                                "External 404s": len(b_ext),
                                "Spelling Errors": len(typos),
                                "Dead Internal Links": ", ".join(b_int),
                                "Dead External Links": ", ".join(b_ext),
                                "Misspelled Words": ", ".join(typos)
                            })
                    
                    status_text.empty()
                    duration = round(time.time() - start_time, 1)
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader("📊 Audit Performance Summary")
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Articles Audited", len(articles))
                        c2.metric("Internal Failures", df['Internal 404s'].sum(), delta_color="inverse")
                        c3.metric("External Failures", df['External 404s'].sum(), delta_color="inverse")
                        c4.metric("Typo Risks", df['Spelling Errors'].sum(), delta_color="inverse")
                        
                        st.success(f"✅ Audit completed in {duration}s. We found {len(report_list)} articles that require immediate attention.")
                        
                        # --- THE VALUE DRIVE ---
                        st.info(f"💡 **Time Saved:** Manually checking these {len(articles)} articles would have taken roughly **{round((len(articles)*5)/60, 1)} hours**. Link Warden Pro finished it in seconds.")

                        st.divider()
                        st.write("### 📝 Detailed Findings")
                        st.dataframe(df, use_container_width=True)

                        st.divider()
                        st.subheader("📥 Export Your Professional Report")
                        st.write("Generate a comprehensive CSV to share with your content team or developers.")
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 DOWNLOAD AUDIT REPORT (CSV)",
                            data=csv,
                            file_name=f"LinkWarden_Audit_{subdomain}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success(f"🌟 Perfect Integrity! All {len(articles)} articles are healthy.")
                else:
                    st.error(f"❌ Connection Failed: Zendesk returned a {response.status_code} error. Please check your API token permissions.")
            except Exception as e:
                st.error(f"❌ System Error: {e}")

# --- TAB 2: MARKETING / VALUE PROPOSITION ---
with tab2:
    st.title("Why Knowledge Base Integrity Matters")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📉 Reduce Ticket Deflection")
        st.write("""
        When a customer clicks a broken link in your Help Center, they don't keep searching—they open a ticket. 
        Maintaining 100% link integrity is the fastest way to reduce support overhead.
        """)
        
        st.subheader("🤝 Build Brand Authority")
        st.write("""
        Typos and 'Page Not Found' errors erode trust. A polished Knowledge Base signals to 
        customers that your product is reliable and your documentation is current.
        """)

    with col2:
        st.subheader("🔍 Improve SEO Ranking")
        st.write("""
        Search engines penalize sites with high bounce rates caused by broken links. 
        Link Warden helps keep your Help Center at the top of Google results.
        """)

# --- TAB 3: PRO PRICING ---
with tab3:
    st.title("Professional Audit Passes")
    st.write("Expert-grade auditing without the enterprise price tag.")
    
    # Marketing-heavy pricing cards
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="pricing-card">
        <h3>Standard Scan</h3>
        <p>Perfect for small teams.</p>
        <h2 style="color:#007bff;">FREE</h2>
        <ul style="text-align:left;">
            <li>Full Article Scan</li>
            <li>On-screen results</li>
            <li>Classified failures</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        st.button("Current Version", disabled=True)

    with col_b:
        st.markdown("""
        <div class="pricing-card">
        <h3>Pro Report Access</h3>
        <p>The standard for Zendesk Admins.</p>
        <h2 style="color:#007bff;">$19 <span style="font-size:12px; color:#666;">/ one-time</span></h2>
        <ul style="text-align:left;">
            <li><b>Downloadable CSV Report</b></li>
            <li>Internal vs External classification</li>
            <li>Time-saving 'Value Summary'</li>
            <li>Typo suggestion engine</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("🚀 GET PRO ACCESS", "https://buy.stripe.com/your_link")
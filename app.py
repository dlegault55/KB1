import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro", page_icon="🛡️", layout="wide")
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
        height: 3em;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        color: #007bff;
    }
    .pricing-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Global Controls) ---
with st.sidebar:
    st.header("🔑 Zendesk Access")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme-help")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🔓 Unlock Report")
    # This is the secret key that unlocks the CSV download
    val_key = st.text_input("Validation Key", type="password", help="Enter the key sent to your email after purchase.")
    
    st.divider()
    st.header("⚙️ Audit Settings")
    ignore_list = st.text_area("Keywords to Ignore", 
                               help="Brand names or technical terms to skip (one per line).",
                               placeholder="Zendesk\nSaaS").split('\n')
    
    st.divider()
    st.caption("Link Warden Pro v1.6")
    st.info("🔒 Secure: Credentials are wiped on browser refresh.")

# --- 4. NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🚀 Audit Tool", "📄 Privacy & FAQ", "💎 Pricing & Access"])

# --- TAB 1: THE AUDIT TOOL ---
with tab1:
    st.title("🛡️ Knowledge Base Audit Pro")
    st.write("Scan your help center for errors. Preview results for free; pay only to export the full report.")

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
                    broken_internal.append(f"{url} (Timeout)")
                else:
                    broken_external.append(f"{url} (Timeout)")
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [word for word in spell.unknown(words) 
                 if not word.istitle() and len(word) > 2 and word.lower() not in [i.lower() for i in ignore]]
        
        return broken_internal, broken_external, typos

    if st.button("🚀 Run Full Audit"):
        if not all([subdomain, email, token]):
            st.error("Please enter your Zendesk credentials in the sidebar.")
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
                        status_text.text(f"Scanning Article {i+1} of {len(articles)}...")
                        
                        b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain)
                        
                        if b_int or b_ext or typos:
                            report_list.append({
                                "Article Title": art['title'],
                                "Zendesk URL": art['html_url'],
                                "Broken Internal": len(b_int),
                                "Broken External": len(b_ext),
                                "Typos Found": len(typos),
                                "Internal Link Details": ", ".join(b_int),
                                "External Link Details": ", ".join(b_ext),
                                "Typo Details": ", ".join(typos)
                            })
                    
                    status_text.empty()
                    duration = round(time.time() - start_time, 1)
                    
                    if report_list:
                        df = pd.DataFrame(report_list)
                        st.subheader(f"Summary Results ({duration}s)")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Internal Issues 🔗", df['Broken Internal'].sum())
                        c2.metric("External Issues 🌐", df['Broken External'].sum())
                        c3.metric("Typos Found ✍️", df['Typos Found'].sum())
                        
                        st.divider()
                        st.write("### Issue Preview")
                        st.dataframe(df, use_container_width=True)

                        # --- THE PAYWALL GATE ---
                        st.divider()
                        if val_key == "WARDEN2024":  # Change this to your secret key
                            st.success("✅ Validation Key Accepted! You can now download the full report.")
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Full Audit Report (CSV)",
                                data=csv,
                                file_name=f"{subdomain}_detailed_audit.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("🔒 **Export Locked:** Purchase a Single Audit Pass to download the full detailed report (CSV).")
                            st.info("Once you have your key, enter it in the sidebar to unlock the download button.")
                    else:
                        st.success(f"No issues found! Your Knowledge Base is perfectly clean.")
                else:
                    st.error(f"Zendesk API Error {response.status_code}: Check your subdomain and credentials.")
            except Exception as e:
                st.error(f"Error connecting to Zendesk: {e}")

# --- TAB 2: PRIVACY & FAQ ---
with tab2:
    st.title("Privacy & Security")
    with st.expander("🕵️ Is my data stored?", expanded=True):
        st.write("No. We use a 'Zero-Retention' model. Your API token and article content are held in temporary memory for the duration of the scan and deleted the moment you refresh the page.")
    with st.expander("🔐 How does the Validation Key work?"):
        st.write("After purchasing a pass, you'll receive a key. Entering this key in the sidebar unlocks the CSV export functionality for your current session.")

# --- TAB 3: PRICING & ACCESS ---
with tab3:
    st.title("Pricing")
    st.write("Scan for free. Pay only if you need the report.")
    
    col_free, col_paid = st.columns(2)
    
    with col_free:
        st.markdown('<div class="pricing-card">', unsafe_allow_html=True)
        st.subheader("Free Scan")
        st.write("✅ On-screen summary")
        st.write("✅ Article-by-article preview")
        st.write("❌ No CSV Export")
        st.write("❌ No bulk fix suggestions")
        st.button("Active", disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_paid:
        st.markdown('<div class="pricing-card">', unsafe_allow_html=True)
        st.subheader("Single Audit Pass")
        st.write("✅ **Unlimited** scans for 24 hours")
        st.write("✅ **Full CSV Export** unlocked")
        st.write("✅ Internal vs External classification")
        st.write("✅ Instant Key delivery")
        st.link_button("🚀 Get Key - $19", "https://buy.stripe.com/your_link_here")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("Need a custom enterprise solution? Contact support@yourdomain.com")
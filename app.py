import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro (TESTING)", page_icon="🛡️", layout="wide")
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
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("🔑 Zendesk Access")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme-help")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("⚙️ Audit Settings")
    ignore_list = st.text_area("Keywords to Ignore", 
                               placeholder="Zendesk\nSaaS").split('\n')
    
    st.divider()
    st.info("🧪 **TESTING MODE:** Download gate is currently DISABLED.")

# --- 4. NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(["🚀 Audit Tool", "📄 Privacy & FAQ", "💎 Pricing & Access"])

# --- TAB 1: THE AUDIT TOOL ---
with tab1:
    st.title("🛡️ Knowledge Base Audit Pro")
    
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
            st.error("Please enter credentials in the sidebar.")
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
                        st.subheader(f"Audit Summary")
                        
                        # Added a 4th metric for total articles scanned
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Scanned 📄", len(articles))
                        c2.metric("Internal 🔗", df['Broken Internal'].sum())
                        c3.metric("External 🌐", df['Broken External'].sum())
                        c4.metric("Typos ✍️", df['Typos Found'].sum())
                        
                        st.divider()
                        st.dataframe(df, use_container_width=True)

                        # --- DOWNLOAD IS NOW OPEN FOR TESTING ---
                        st.success("🧪 Testing Mode: CSV Download is enabled.")
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Audit Report (CSV)",
                            data=csv,
                            file_name=f"{subdomain}_audit_test.csv",
                            mime="text/csv"
                        )
                    else:
                        st.success(f"No issues found in {len(articles)} articles!")
                else:
                    st.error(f"Zendesk Error {response.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")

# (Tabs 2 and 3 remain same for structural consistency)
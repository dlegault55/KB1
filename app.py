import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro", page_icon="🛡️", layout="wide")

# Initialize Spellchecker
spell = SpellChecker()

# 2. UI Styling
st.markdown("""
    <style>
    .stButton>button { background-color: #007bff; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3em; }
    [data-testid="stMetricValue"] { font-size: 2.2rem; color: #007bff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Defined outside tabs so it's always there) ---
with st.sidebar:
    st.header("🔑 Zendesk Access")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme-help")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    st.divider()
    st.caption("v1.2 - Secure Session Mode")
    st.info("Credentials are wiped when you close the browser.")

# --- 4. CREATE TABS ---
tab1, tab2 = st.tabs(["🚀 Audit Tool", "📄 Privacy & FAQ"])

# --- TAB 1: THE AUDIT TOOL ---
with tab1:
    st.title("🛡️ Knowledge Base Audit Pro")
    
    def audit_content(html_body):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken = []
        for url in links:
            try:
                res = requests.head(url, timeout=3, allow_redirects=True)
                if res.status_code >= 400:
                    broken.append(f"{url} ({res.status_code})")
            except:
                broken.append(f"{url} (Failed)")
        
        text = soup.get_text()
        words = spell.split_words(text)
        typos = [word for word in spell.unknown(words) if not word.istitle() and len(word) > 2]
        return broken, typos

    if st.button("🚀 Run Full Audit"):
        if not all([subdomain, email, token]):
            st.error("Missing credentials in the sidebar!")
        else:
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
            auth = (f"{email}/token", token)
            
            with st.spinner("Scanning articles..."):
                try:
                    response = requests.get(api_url, auth=auth)
                    if response.status_code == 200:
                        articles = response.json().get('articles', [])
                        report_list = []

                        for art in articles:
                            dead_links, typos = audit_content(art['body'])
                            if dead_links or typos:
                                report_list.append({
                                    "Article Title": art['title'],
                                    "Zendesk URL": art['html_url'],
                                    "Broken Links Found": int(len(dead_links)),
                                    "Typos Found": int(len(typos)),
                                    "Link Details": ", ".join(dead_links),
                                    "Typo Details": ", ".join(typos)
                                })
                        
                        if report_list:
                            df = pd.DataFrame(report_list)
                            st.subheader("Executive Summary")
                            c1, c2 = st.columns(2)
                            c1.metric("Articles with Issues", len(report_list))
                            c2.metric("Total Errors Found", int(df['Broken Links Found'].sum() + df['Typos Found'].sum()))
                            
                            st.divider()
                            st.dataframe(df, use_container_width=True)

                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button("📥 Download Audit Report (CSV)", data=csv, file_name=f"{subdomain}_audit.csv", mime="text/csv")
                        else:
                            st.success("Everything looks clean!")
                    else:
                        st.error(f"Error {response.status_code}: Verify credentials.")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

# --- TAB 2: PRIVACY & FAQ ---
with tab2:
    st.title("Privacy & Security FAQ")
    
    with st.expander("🔐 Why do I need to provide an API Token?", expanded=True):
        st.write("The API Token allows the app to fetch all articles securely and quickly via the Zendesk backend rather than scraping the public site.")

    with st.expander("🕵️ Is my data being stored?"):
        st.write("No. Your token and email stay in your browser's RAM. We do not have a database. Once you refresh the page, the data is gone.")

    with st.expander("🛠️ How do I create a Zendesk API Token?"):
        st.markdown("Go to **Zendesk Admin Center** > **Apps and Integrations** > **APIs** > **Zendesk API**. Enable 'Token Access' and create a new token.")
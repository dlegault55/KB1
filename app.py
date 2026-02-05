import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Configuration
st.set_page_config(page_title="Link Warden Pro", page_icon="🛡️", layout="wide")

# Initialize Spellchecker
spell = SpellChecker()

# 2. UI Styling (Fixed the error here)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { background-color: #007bff; color: white; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Header
st.title("🛡️ Knowledge Base Audit Pro")
st.write("Detect broken links and spelling errors in your Zendesk Help Center.")

# 4. Sidebar for Credentials
with st.sidebar:
    st.header("Zendesk Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme-help")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    st.divider()
    st.info("The report will include article titles, URLs, and specific issues found.")

# 5. The Audit Engine
def audit_content(html_body):
    soup = BeautifulSoup(html_body, 'html.parser')
    
    # Check Links
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    broken = []
    for url in links:
        try:
            # Using a quick HEAD request to check link health
            res = requests.head(url, timeout=3, allow_redirects=True)
            if res.status_code >= 400:
                broken.append(f"{url} ({res.status_code})")
        except:
            broken.append(f"{url} (Timeout/Failed)")

    # Check Typos
    text = soup.get_text()
    words = spell.split_words(text)
    # Ignore brand names (Capitalized) and short strings
    typos = [word for word in spell.unknown(words) if not word.istitle() and len(word) > 2]
    
    return broken, typos

# 6. Execution & Results
if st.button("🚀 Run Full Audit"):
    if not all([subdomain, email, token]):
        st.error("Please provide all connection details in the sidebar.")
    else:
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
        auth = (f"{email}/token", token)
        
        with st.spinner("Analyzing Knowledge Base..."):
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
                                "Broken Links Found": len(dead_links),
                                "Typos Found": len(typos),
                                "Link Details": ", ".join(dead_links),
                                "Typo Details": ", ".join(typos)
                            })
                    
                    if report_list:
                        # Display Summary Metrics
                        df = pd.DataFrame(report_list)
                        col1, col2 = st.columns(2)
                        col1.metric("Articles with Issues", len(report_list))
                        col2.metric("Total Issues", df['Broken Links Found'].sum() + df['Typos Found'].sum())

                        # Display Data Table
                        st.subheader("Detailed Audit Log")
                        st.dataframe(df, use_container_width=True)

                        # Download Button
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Audit Report (CSV)",
                            data=csv,
                            file_name=f"{subdomain}_kb_audit.csv",
                            mime="text/csv",
                        )
                    else:
                        st.success("No issues found! Your Knowledge Base is clean.")
                else:
                    st.error(f"Zendesk API Error: {response.status_code}. Verify your credentials.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
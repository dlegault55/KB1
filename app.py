import streamlit as st
import requests
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# 1. Page Config & Setup
st.set_page_config(page_title="Link Warden", page_icon="🛡️")
spell = SpellChecker()

st.title("🛡️ Link Warden & Typo Guard")
st.markdown("Scan your Zendesk Knowledge Base for broken links and spelling errors.")

# 2. Sidebar for Credentials
with st.sidebar:
    st.header("Zendesk Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. 'companyhelp'")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    st.info("Your token is processed securely via HTTPS and is not stored.")

# 3. Core Logic Functions
def audit_content(html_body):
    soup = BeautifulSoup(html_body, 'html.parser')
    
    # Check Links
    links = [a.get('href') for a in soup.find_all('a') if a.get('href')]
    broken = []
    for url in links:
        try:
            res = requests.head(url, timeout=3, allow_redirects=True)
            if res.status_code >= 400:
                broken.append(f"{url} (Status: {res.status_code})")
        except:
            broken.append(f"{url} (Failed to connect)")

    # Check Typos
    text = soup.get_text()
    words = spell.split_words(text)
    # Ignore capitalized words to avoid flagging brand names/proper nouns
    typos = [word for word in spell.unknown(words) if not word.istitle()]
    
    return broken, typos

# 4. The Action Button
if st.button("🚀 Run Full Audit"):
    if not all([subdomain, email, token]):
        st.error("Missing credentials! Check the sidebar.")
    else:
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
        auth = (f"{email}/token", token)
        
        with st.spinner("Scanning articles... this may take a minute..."):
            try:
                response = requests.get(api_url, auth=auth)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    
                    # Create Summary Metrics
                    total_links = 0
                    total_typos = 0
                    
                    for art in articles:
                        dead_links, typos = audit_content(art['body'])
                        if dead_links or typos:
                            with st.expander(f"📄 {art['title']}"):
                                if dead_links:
                                    st.error("Broken Links found:")
                                    for link in dead_links:
                                        st.write(f"- {link}")
                                    total_links += len(dead_links)
                                if typos:
                                    st.warning(f"Potential Typos: {', '.join(typos)}")
                                    total_typos += len(typos)
                    
                    st.divider()
                    st.success("Audit Complete!")
                    st.metric("Total Issues Found", total_links + total_typos)
                else:
                    st.error(f"Zendesk API Error: {response.status_code}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
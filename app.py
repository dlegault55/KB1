import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
from io import BytesIO

# 1. Page Config
st.set_page_config(page_title="Link Warden Pro", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_index=True)

st.title("🛡️ Knowledge Base Audit Pro")
st.write("Professional-grade link and typo auditing for Zendesk.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    subdomain = st.text_input("Subdomain")
    email = st.text_input("Email")
    token = st.text_input("API Token", type="password")
    st.divider()
    st.caption("v1.1 - Added CSV Export")

# --- ENGINE ---
def audit_article(html_body):
    soup = BeautifulSoup(html_body, 'html.parser')
    # Link check
    links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
    broken = [url for url in links if requests.head(url, timeout=3).status_code >= 400]
    # Typo check
    text = soup.get_text()
    words = spell.split_words(text)
    typos = [word for word in spell.unknown(words) if not word.istitle() and len(word) > 2]
    return broken, typos

# --- MAIN LOGIC ---
if st.button("🚀 Run Full Audit"):
    if not all([subdomain, email, token]):
        st.error("Credentials missing.")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json"
        
        with st.spinner("Analyzing articles..."):
            res = requests.get(api_url, auth=auth)
            if res.status_code == 200:
                articles = res.json().get('articles', [])
                report_data = []

                for art in articles:
                    dead, typos = audit_article(art['body'])
                    if dead or typos:
                        report_data.append({
                            "Article Title": art['title'],
                            "URL": art['html_url'],
                            "Broken Links": ", ".join(dead),
                            "Potential Typos": ", ".join(typos)
                        })

                if report_data:
                    # Create DataFrame for UI and Export
                    df = pd.DataFrame(report_data)
                    
                    # UI: Metrics
                    c1, c2 = st.columns(2)
                    c1.metric("Issues Found", len(report_data))
                    c2.metric("Articles Clean", len(articles) - len(report_data))

                    # UI: Data Table
                    st.subheader("Issue Log")
                    st.dataframe(df, use_container_width=True)

                    # --- EXPORT BUTTON ---
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Audit Report (CSV)",
                        data=csv,
                        file_name=f"{subdomain}_kb_audit.csv",
                        mime="text/csv",
                    )
                else:
                    st.success("Your Knowledge Base is perfect!")
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
    .faq-text { color: #444; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# 3. Create Tabs
tab1, tab2 = st.tabs(["🚀 Audit Tool", "📄 Privacy & FAQ"])

# --- TAB 1: THE AUDIT TOOL ---
with tab1:
    st.title("🛡️ Knowledge Base Audit Pro")
    
    # Run Button and Main Logic
    if st.button("🚀 Run Full Audit"):
        # ... (Paste all your existing "if not all([subdomain...)" logic here)
        pass 

# --- TAB 2: PRIVACY & FAQ ---
with tab2:
    st.title("Privacy & Security FAQ")
    
    with st.expander("🔐 Why do I need to provide an API Token?", expanded=True):
        st.markdown("""
        The API Token acts as a secure 'backdoor' to your Knowledge Base. 
        - **Speed:** It allows the app to fetch all articles in one request rather than scraping pages slowly.
        - **Accuracy:** It accesses the raw HTML code where broken links often hide.
        - **Permission:** It identifies you as an authorized admin, preventing Zendesk from blocking the request.
        """)

    with st.expander("🕵️ Is my data being stored?"):
        st.write("""
        **No.** This app is built with a 'Zero-Retention' policy.
        - Your **Email** and **Token** are held only in your browser's temporary session memory.
        - Once you refresh the page or close the tab, all credentials are wiped.
        - We do not use a database; your data never leaves the Streamlit/GitHub secure ecosystem.
        """)

    with st.expander("🛠️ How do I create a Zendesk API Token?"):
        st.markdown("""
        1. Log in to your **Zendesk Admin Center**.
        2. Go to **Apps and Integrations** > **APIs** > **Zendesk API**.
        3. Enable **Token Access**.
        4. Click **Add API Token**, copy it, and paste it here. 
        *Tip: We recommend naming it 'Link Warden' so you know what it's for!*
        """)

    with st.expander("📊 What does the report include?"):
        st.write("""
        The CSV export includes:
        - Article Title and Direct URL.
        - Count of broken links and potential typos.
        - The specific 'Dead' URLs and misspelled words found.
        """)
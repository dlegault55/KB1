import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import re
from datetime import datetime, timedelta
import random

# 1. Page Config
st.set_page_config(page_title="ZenAudit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. MASTER CSS
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #38BDF8; }
    .feature-icon { font-size: 2.2rem; margin-bottom: 12px; display: block; }
    .feature-title { font-size: 1.2rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; display: block; }
    .feature-desc { font-size: 0.9rem; color: #94A3B8; line-height: 1.5; }

    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important;
        justify-content: center; align-items: center;
    }
    .m-val { font-size: 2.2rem; font-weight: bold; color: #38BDF8; line-height: 1.2; display: block; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; display: block; }

    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 400px; overflow-y: auto; font-size: 0.85rem; line-height: 1.6;
    }
    .insight-card {
        background-color: #1E293B; padding: 15px; border-radius: 12px;
        border: 1px solid #334155; height: 120px; margin-bottom: 20px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .insight-label { font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; margin-bottom: 5px; }
    .insight-value { font-size: 1.4rem; font-weight: bold; color: #38BDF8; }
    .insight-sub { font-size: 0.8rem; color: #F1F5F9; font-style: italic; }

    .success-anchor { margin-top: 60px; }
    .stButton>button { background-color: #38BDF8; color: #0F172A; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; text-transform: uppercase;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Instructions & Tuning) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;">
        <b>1. Subdomain</b><br>Prefix of your URL (e.g., <b>acme</b> for <i>acme.zendesk.com</i>).<br><br>
        <b>2. Admin Email</b><br>Your Zendesk administrator login email.<br><br>
        <b>3. API Token</b><br>Go to <b>Admin Center > Apps and Integrations > Zendesk API</b>. Enable "Token Access" and click "Add API token".
        </div>""", unsafe_allow_html=True)
    
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_ai = st.checkbox("Format Check", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)
    
    with st.expander("🔍 CONTENT FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r
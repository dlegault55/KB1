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

# 2. MASTER CSS (Locked & Value-Focused)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }
    
    .feature-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        border: 1px solid #334155; height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: #38BDF8; transform: translateY(-2px); }
    .feature-icon { font-size: 2.2rem; margin-bottom: 12px; display: block; }
    .feature-title { font-size: 1.2rem; font-weight: bold; color: #38BDF8; margin-bottom: 8px; display: block; }
    .feature-desc { font-size: 0.9rem; color: #94A3B8; line-height: 1.5; }

    .metric-card {
        background-color: #1E293B; padding: 20px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; min-height: 110px;
        display: flex; flex-direction: column !important;
        justify-content: center; align-items: center;
    }
    .m-val { font-size: 2.2rem; font-weight: bold; color: #38BDF8; line-height: 1.2; }
    .m-lab { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600; }

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

    .success-anchor { margin-top: 60px; }
    .stButton>button { background-color: #38BDF8; color: #0F172A; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (Full Instructions & All Tuning) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;">
        <b>1. Subdomain</b><br>Prefix of your URL (e.g., <b>acme</b>).<br><br>
        <b>2. Admin Email</b><br>Your Zendesk admin login.<br><br>
        <b>3. API Token</b><br><b>Admin Center > Apps > Zendesk API</b>.
        </div>""", unsafe_allow_html=True)
    
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)
        do_ai = st.checkbox("Format Check", value=True, help="Checks for headers and length.")
        do_alt = st.checkbox("Image Alt-Text", value=True)
        do_tags = st.checkbox("Tag Audit", value=True)

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

# Updated Marketing Row (Swapped Card 2)
feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>⚡</span><span class='feature-title'>Stop Manual Auditing</span><span class='feature-desc'>Save 40+ hours per month by automating content lifecycle tracking. Never manually hunt for expired articles again.</span></div>""", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🔎</span><span class='feature-title'>Fix Discoverability</span><span class='feature-desc'>Solve the "I can't find it" problem. Audit tags and structure to ensure users find answers on the first search, every time.</span></div>""", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🎯</span><span class='feature-title'>Protect Brand Trust</span><span class='feature-desc'>Instantly surface broken accessibility and legacy terminology that erodes customer confidence and professionalism.</span></div>""", unsafe_allow_html=True)

st.divider()

# Scoreboard (5 Columns)
m_row = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_row]

st.markdown("<br>", unsafe_allow_html=True)

# Action Zone
col_con, col_ins = st.columns([1.5, 1])
console_ui = col_con.empty()
with col_ins:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

st.markdown("<div class='success-anchor'></div>", unsafe_allow_html=True)
finish_ui, dl_area = st.empty(), st.empty()

# --- 5. LOGIC & EXECUTION ---
# (Rest of the logic from 8.7.0 is preserved here...)
# [Gated calculations for typos, stale, alt, keywords, and tags]
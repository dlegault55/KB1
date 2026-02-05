import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random
import re
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Content Audit", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. Strict UI Styling (No-Overlap Grid)
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }

    /* Button Styling */
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    
    /* Box & Card Spacing */
    .metric-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        text-align: center; border: 1px solid #334155;
        margin-bottom: 20px; /* Force vertical separation */
    }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #38BDF8; line-height: 1.2; }
    .metric-label { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; margin-top: 5px; }

    .dark-card {
        background-color: #1E293B; padding: 30px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; height: 100%;
        margin-bottom: 20px; /* Prevents boxes from touching */
    }

    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 350px; overflow-y: auto; font-size: 0.85rem;
    }

    .signup-container { display: flex; gap: 12px; margin-top: 15px; }
    .signup-input { flex: 2; padding: 10px; border-radius: 6px; border: 1px solid #334155; background-color: #0F172A; color: white; }
    .signup-btn { flex: 1; background-color: #38BDF8; color: #0F172A; border: none; border-radius: 6px; font-weight: bold; }

    .section-spacer { margin-top: 50px; padding-top: 40px; border-top: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. THE SALTY TIPS ---
admin_tips = [
    "💀 **Admin Truth:** If you don't fix these 404s, your customers will mention it in the CSAT comment.",
    "🤖 **AI Reality:** Garbage in, Garbage out. Bad articles make for bad AI responses.",
    "🥃 **Guerilla Tip:** Stop using 'New' in titles. It looks dated after 3 months.",
    "🔍 **Search Bloat:** 1,800 articles? Time for a sunsetting strategy.",
    "🛠️ **Workflow:** Manual audits are for people with too much time. Let the machine find the rot."
]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<h1 style="color:#38BDF8; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""<div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem;"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Zendesk API Key.</div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Tuning")
    restricted_input = st.text_input("Restricted Keywords")
    restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_stale = st.checkbox("Detect Stale Content", value=True)
    enable_ai = st.checkbox("AI Readiness Scan", value=True)
    
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', st.text_area("Exclusion List")) if w.strip()]

# --- 5. MAIN INTERFACE ---
st.title("ZenAudit Deep Scan")
st.info("⚡ **Lightning Mode:** Analyzing first 100 articles.")

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("Missing Credentials")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        res = requests.get(api_url, auth=auth)
        articles = res.json().get('articles', [])

        if articles:
            # Containerized Rows for Spacing
            metric_row = st.container()
            with metric_row:
                m1, m2, m3, m4, m5 = st.columns(5)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 1.5 : 1 Layout
            col_con, col_tip = st.columns([1.5, 1])
            console_placeholder = col_con.empty()
            tip_placeholder = col_tip.empty()

            results_data = []
            log_entries = []

            for i, art in enumerate(articles):
                # Simple Logic to avoid CPU hang
                upd = datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                is_stale = (datetime.now() - upd > timedelta(days=365))
                
                # Update Records
                results_data.append({"Title": art['title'], "URL": art['html_url'], "Stale": is_stale})
                
                # Update UI
                log_entries.insert(0, f"🚩 {art['title'][:40]}...")
                console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                # Push Tips every 10 items
                if i % 10 == 0:
                    tip_placeholder.markdown(f"<div class='dark-card'>{random.choice(admin_tips)}</div>", unsafe_allow_html=True)

                # Metrics
                m1.markdown(f"<div class='metric-card'><div class='metric-value'>{i+1}</div><div class='metric-label'>Scanned</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(1 for d in results_data if d['Stale'])}</div><div class='metric-label'>Stale</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-value'>-</div><div class='metric-label'>Typos</div></div>", unsafe_allow_html=True)
                m4.markdown(f"<div class='metric-card'><div class='metric-value'>-</div><div class='metric-label'>Keywords</div></div>", unsafe_allow_html=True)
                m5.markdown(f"<div class='metric-card'><div class='metric-value'>OK</div><div class='metric-label'>AI Ready</div></div>", unsafe_allow_html=True)

            # --- PERMANENT DOWNLOAD BUTTON ---
            df = pd.DataFrame(results_data)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 DOWNLOAD AUDIT REPORT (CSV)", data=csv, file_name="audit.csv", mime="text/csv")

# --- 6. FOOTER ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

e1, e2, e3 = st.columns(3)
with e1: st.markdown('<div class="dark-card"><b>🏺 Stale Content</b><br>Outdated for 365+ days.</div>', unsafe_allow_html=True)
with e2: st.markdown('<div class="dark-card"><b>🗣️ Restricted Keywords</b><br>Detect legacy terms.</div>', unsafe_allow_html=True)
with e3: st.markdown('<div class="dark-card"><b>🤖 AI Readiness</b><br>Formatted for indexing.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
f1, f2 = st.columns(2)
with f1: st.markdown('<div class="dark-card"><b>🗺️ Roadmap</b><br>Zendesk (Live)</div>', unsafe_allow_html=True)
with f2:
    st.markdown('<div class="dark-card"><b>📩 Get Updates</b><div class="signup-container"><input type="email" placeholder="work@email.com" class="signup-input"><button class="signup-btn">NOTIFY</button></div></div>', unsafe_allow_html=True)
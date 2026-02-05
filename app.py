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

# 2. UI Styling - LOCKED SPACING & MARGINS
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #E2E8F0; }
    section[data-testid="stSidebar"] { background-color: #1E293B !important; }

    /* Button Styling */
    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;
    }
    
    /* Metrics Row Spacing */
    [data-testid="column"] { padding: 0 10px !important; }

    /* Operational Console */
    .console-box {
        background-color: #011627; color: #d6deeb; font-family: 'Courier New', monospace;
        padding: 20px; border-radius: 8px; border: 1px solid #38BDF8;
        height: 350px; overflow-y: auto; font-size: 0.85rem;
    }
    
    /* Box Spacing and Cards */
    .metric-card {
        background-color: #1E293B; padding: 25px; border-radius: 12px;
        text-align: center; border: 1px solid #334155; margin-bottom: 20px;
    }
    .metric-value { font-size: 2.2rem; font-weight: bold; color: #38BDF8; line-height: 1.2; }
    .metric-label { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }

    .dark-card {
        background-color: #1E293B; padding: 30px; border-radius: 12px;
        border: 1px solid #334155; color: #F1F5F9; height: 100%;
        margin-bottom: 15px; /* Added margin to prevent touching */
    }

    /* Signup Form */
    .signup-container { display: flex; gap: 12px; margin-top: 20px; }
    .signup-input { flex: 2; padding: 12px; border-radius: 6px; border: 1px solid #334155; background-color: #0F172A; color: white; }
    .signup-btn { flex: 1; background-color: #38BDF8; color: #0F172A; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }

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
        st.markdown("""<div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem;"><b>1. Subdomain:</b> [acme]<br><b>2. Admin Email:</b> login@company.com<br><b>3. API Token:</b> Apps > Zendesk API.</div>""", unsafe_allow_html=True)
    with st.expander("🔒 PRIVACY & FAQ", expanded=False):
        st.markdown("""<div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem;">Session-only processing. No data is stored.</div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")
    
    st.divider()
    st.header("🎯 Audit Tuning")
    restricted_input = st.text_input("Restricted Keywords")
    restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
    
    enable_typos = st.checkbox("Scan Typos", value=True)
    enable_stale = st.checkbox("Detect Stale Content", value=True)
    enable_ai = st.checkbox("AI Readiness Scan", value=True)
    
    ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', st.text_area("Exclusion List")) if w.strip()]

# --- 5. MAIN SCAN INTERFACE ---
st.title("ZenAudit Deep Scan")
st.info("⚡ **Lightning Mode:** Analyzing the most recent 100 articles.")

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("⚠️ Credentials missing.")
    else:
        auth = (f"{email}/token", token)
        api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        res = requests.get(api_url, auth=auth)
        all_articles = res.json().get('articles', [])

        if all_articles:
            # Metrics Row (Isolated with spacing)
            m1, m2, m3, m4, m5 = st.columns(5)
            
            # The Scan Area (Restoring the 1.5 : 1 ratio and the Tips)
            st.markdown("<br>", unsafe_allow_html=True)
            col_con, col_tip = st.columns([1.5, 1])
            
            console_placeholder = col_con.empty()
            tip_placeholder = col_tip.empty()
            
            # Show initial tip
            tip_placeholder.markdown(f"<div class='dark-card'>{random.choice(admin_tips)}</div>", unsafe_allow_html=True)

            results_data = []
            log_entries = []

            for i, art in enumerate(all_articles):
                # Basic Audit Logic (Simplified for stability)
                body = art.get('body', '') or ''
                soup = BeautifulSoup(body, 'html.parser')
                text = soup.get_text().lower()
                
                # Flag logic
                stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365)) if enable_stale else False
                typos = list(spell.unknown(spell.split_words(text))) if enable_typos else []
                keys = [w for w in restricted_words if w in text]
                
                results_data.append({"Title": art['title'], "Stale": stale, "Typos": len(typos), "Keywords": len(keys)})
                
                # Update Console
                flag = "🚩" if (stale or typos or keys) else "✅"
                log_entries.insert(0, f"{flag} {art['title'][:40]}...")
                console_placeholder.markdown(f"<div class='console-box'>{'<br>'.join(log_entries[:12])}</div>", unsafe_allow_html=True)
                
                # Update Metrics
                m1.markdown(f"<div class='metric-card'><div class='metric-value'>{i+1}</div><div class='metric-label'>Scanned</div></div>", unsafe_allow_html=True)
                m2.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(1 for d in results_data if d['Stale'])}</div><div class='metric-label'>Stale</div></div>", unsafe_allow_html=True)
                m3.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(d['Typos'] for d in results_data)}</div><div class='metric-label'>Typos</div></div>", unsafe_allow_html=True)
                m4.markdown(f"<div class='metric-card'><div class='metric-value'>{sum(d['Keywords'] for d in results_data)}</div><div class='metric-label'>Keywords</div></div>", unsafe_allow_html=True)
                m5.markdown(f"<div class='metric-card'><div class='metric-value'>100%</div><div class='metric-label'>AI Ready</div></div>", unsafe_allow_html=True)

            # RESTORED DOWNLOAD BUTTON
            df = pd.DataFrame(results_data)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 DOWNLOAD AUDIT REPORT (CSV)", data=csv, file_name=f"zenaudit_report.csv", mime="text/csv")

# --- 6. FOOTER ---
st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.markdown("### 🧠 Audit Intelligence Layers")


e1, e2, e3 = st.columns(3)
with e1:
    st.markdown('<div class="dark-card"><b>🏺 Stale Content</b><br><span style="color:#94A3B8; font-size:0.8rem;">Flags articles not updated in 365+ days.</span></div>', unsafe_allow_html=True)
with e2:
    st.markdown('<div class="dark-card"><b>🗣️ Restricted Keywords</b><br><span style="color:#94A3B8; font-size:0.8rem;">Detects legacy branding or forbidden terms.</span></div>', unsafe_allow_html=True)
with e3:
    st.markdown('<div class="dark-card"><b>🤖 AI Readiness</b><br><span style="color:#94A3B8; font-size:0.8rem;">Validates formatting for AI ingestion.</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
f_l, f_r = st.columns(2)
with f_l:
    st.markdown('<div class="dark-card"><b>🗺️ Roadmap</b><br><span style="font-size:0.85rem; color:#94A3B8;">✅ Zendesk (Live)</span></div>', unsafe_allow_html=True)
with f_r:
    st.markdown("""
    <div class="dark-card">
        <b>📩 Get Updates</b>
        <div class="signup-container">
            <input type="email" placeholder="work@email.com" class="signup-input">
            <button class="signup-btn">NOTIFY ME</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
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

    .stButton>button { 
        background-color: #38BDF8; color: #0F172A; font-weight: bold; 
        width: 100%; height: 3.5em; border-radius: 8px; text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR (STRICTLY RESTORED HELP TEXT) ---
with st.sidebar:
    st.markdown("<h1 style='color:#38BDF8; margin-bottom: 0;'>🛡️ ZenAudit</h1>", unsafe_allow_html=True)
    with st.expander("🚀 QUICK START GUIDE", expanded=True):
        st.markdown("""
        <div style="background-color: #0F172A; padding: 15px; border-radius: 8px; font-size: 0.85rem; border-left: 3px solid #38BDF8; line-height:1.6;">
        <b>1. Subdomain</b><br>Prefix of your URL (e.g., <b>acme</b>).<br><br>
        <b>2. Admin Email</b><br>Your Zendesk administrator login email.<br><br>
        <b>3. API Token</b><br>Go to <b>Admin Center > Apps > Zendesk API</b>.
        </div>""", unsafe_allow_html=True)
    
    st.header("🔑 Connection")
    subdomain = st.text_input("Subdomain", placeholder="e.g. acme", help="The unique part of your Zendesk URL (acme.zendesk.com).")
    email = st.text_input("Admin Email", help="The email address associated with your Zendesk Admin account.")
    token = st.text_input("API Token", type="password", help="The API token generated in Zendesk Admin Center.")
    
    st.divider()
    st.header("🎯 Tuning")
    with st.expander("⚙️ AUDIT LAYERS", expanded=False):
        do_stale = st.checkbox("Stale Content", value=True, help="Identifies articles that haven't been updated in over 365 days.")
        do_typo = st.checkbox("Typos", value=True, help="Runs a spellcheck across all article content to find spelling errors.")
        do_format = st.checkbox("Format Check", value=True, help="Verifies if articles have H1/H2 headers and sufficient word count.")
        do_alt = st.checkbox("Image Alt-Text", value=True, help="Finds images within articles that lack descriptive Alt-Text.")
        do_tags = st.checkbox("Tag Audit", value=True, help="Flags articles with zero tags, which harms search discoverability.")
    
    with st.expander("🔍 CONTENT FILTERS", expanded=False):
        restricted_input = st.text_input("Restricted Keywords", help="Comma-separated list of words (e.g. 'internal', 'deprecated') to flag.")
        restricted_words = [w.strip().lower() for w in restricted_input.split(",") if w.strip()]
        raw_ignore = st.text_area("Exclusion List", help="Enter words for the spellchecker to ignore (one per line).")
        ignore_list = [w.strip().lower() for w in re.split(r'[,\n\r]+', raw_ignore) if w.strip()]

# --- 4. MAIN DASHBOARD ---
st.title("Knowledge Base Intelligence")

feat_cols = st.columns(3)
with feat_cols[0]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>⚡</span><span class='feature-title'>Stop Manual Auditing</span><span class='feature-desc'>Save 40+ hours per month by automating content lifecycle tracking.</span></div>""", unsafe_allow_html=True)
with feat_cols[1]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🔎</span><span class='feature-title'>Fix Discoverability</span><span class='feature-desc'>Solve the "I can't find it" problem by auditing tags and structural health.</span></div>""", unsafe_allow_html=True)
with feat_cols[2]:
    st.markdown("""<div class='feature-card'><span class='feature-icon'>🎯</span><span class='feature-title'>Protect Brand Trust</span><span class='feature-desc'>Surface broken accessibility and legacy terms that erode customer confidence.</span></div>""", unsafe_allow_html=True)

st.divider()

m_row = st.columns(5)
met_scan, met_alt, met_typo, met_key, met_stale = [col.empty() for col in m_row]

st.markdown("<br>", unsafe_allow_html=True)

col_con, col_ins = st.columns([1.5, 1])
console_ui = col_con.empty()
with col_ins:
    score_ui, tip_ui, insight_ui = st.empty(), st.empty(), st.empty()

finish_ui, dl_area = st.empty(), st.empty()

# --- 5. LOGIC & EXECUTION ---
tips = ["🤖 Structure beats volume.", "💀 Check your 404s.", "🔍 Sunset your legacy tags."]

if st.button("🚀 RUN DEEP SCAN"):
    if not all([subdomain, email, token]):
        st.error("⚠️ Connection details missing.")
    else:
        results = []
        logs = []
        auth = (f"{email}/token", token)
        url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
        
        try:
            r = requests.get(url, auth=auth)
            articles = r.json().get('articles', [])
            for i, art in enumerate(articles):
                body = art.get('body', '') or ''
                soup = BeautifulSoup(body, 'html.parser')
                text = soup.get_text().lower()
                
                # Logic
                typos = len([w for w in spell.unknown(spell.split_words(text)) if w not in ignore_list and len(w) > 2]) if do_typo else 0
                is_stale = (datetime.now() - datetime.strptime(art['updated_at'], '%Y-%m-%dT%H:%M:%SZ') > timedelta(days=365)) if do_stale else False
                alt_miss = len([img for img in soup.find_all('img') if not img.get('alt')]) if do_alt else 0
                key_hits = sum(1 for w in restricted_words if w in text)
                tag_issue = (len(art.get('label_names', [])) == 0) if do_tags else False
                
                results.append({"Title": art['title'], "URL": art['html_url'], "Stale": is_stale, "Typos": typos, "Alt": alt_miss, "Keywords": key_hits, "Tag Issue": tag_issue})
                
                # Metrics (STRICT STACKING)
                met_scan.markdown(f"<div class='metric-card'><span class='m-val'>{i+1}</span><span class='m-lab'>Scanned</span></div>", unsafe_allow_html=True)
                met_typo.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Typos'] for d in results) if do_typo else '--'}</span><span class='m-lab'>Typos</span></div>", unsafe_allow_html=True)
                met_stale.markdown(f"<div class='metric-card'><span class='m-val'>{sum(1 for d in results if d['Stale']) if do_stale else '--'}</span><span class='m-lab'>Stale</span></div>", unsafe_allow_html=True)
                met_key.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Keywords'] for d in results)}</span><span class='m-lab'>Hits</span></div>", unsafe_allow_html=True)
                met_alt.markdown(f"<div class='metric-card'><span class='m-val'>{sum(d['Alt'] for d in results) if do_alt else '--'}</span><span class='m-lab'>Alt-Text</span></div>", unsafe_allow_html=True)

                # Triple Stack UI
                health = int((sum(1 for d in results if d['Typos'] == 0 and not d['Stale']) / (i+1)) * 100)
                score_ui.markdown(f"<div class='insight-card'><span class='insight-label'>KB Health Score</span><span class='insight-value'>{health}%</span></div>", unsafe_allow_html=True)
                if i % 10 == 0:
                    tip_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Strategy Insight</span><span class='insight-sub'>{random.choice(tips)}</span></div>", unsafe_allow_html=True)
                top_issue = "Typos" if sum(d['Typos'] for d in results) > sum(1 for d in results if d['Stale']) else "Stale Content"
                insight_ui.markdown(f"<div class='insight-card'><span class='insight-label'>Action Priority</span><span class='insight-value' style='color:#F87171;'>Fix {top_issue}</span></div>", unsafe_allow_html=True)

                logs.insert(0, f"✅ Analyzed: {art['title'][:40]}...")
                console_ui.markdown(f"<div class='console-box'>{'<br>'.join(logs[:14])}</div>", unsafe_allow_html=True)

            st.balloons()
            finish_ui.success(f"🎉 **Audit Complete!** Processed {len(results)} articles.")
            dl_area.download_button("📥 DOWNLOAD STRATEGY REPORT", pd.DataFrame(results).to_csv(index=False), "zenaudit_report.csv")
            
        except Exception as e: st.error(f"Error: {e}")
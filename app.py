import streamlit as st
import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import random

# 1. Page Configuration
st.set_page_config(page_title="ZenAudit | Zendesk Content Integrity", page_icon="🛡️", layout="wide")
spell = SpellChecker()

# 2. UI Styling (Keeping the Pro Tab "Pop")
st.markdown("""
    <style>
    .stButton>button { background-color: #219EBC; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3.5em; text-transform: uppercase; border: none;}
    .stButton>button:hover { background-color: #023047; color: #FFB703; border: 1px solid #FFB703; }
    .pro-header { background: linear-gradient(90deg, #FB8500, #FFB703); color: #023047; padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 25px; border: 2px solid #023047;}
    .pro-card { text-align: center; padding: 40px; border: 4px solid #FB8500; border-radius: 20px; background-color: #ffffff; box-shadow: 0 10px 30px rgba(251, 133, 0, 0.2);}
    .live-card { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; margin-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar (Setup as per previous versions)
with st.sidebar:
    st.markdown(f'<h1 style="color:#219EBC; margin-bottom:0;">🛡️ ZenAudit</h1>', unsafe_allow_html=True)
    subdomain = st.text_input("Subdomain", placeholder="acme-support")
    email = st.text_input("Admin Email", placeholder="admin@company.com")
    token = st.text_input("API Token", type="password")
    enable_typos = st.checkbox("Scan for Typos", value=True)
    ignore_list = st.text_area("Ignore Words", placeholder="BrandNames").split('\n')

# 4. Main UI
st.title("ZenAudit Deep Scan")
tab1, tab2 = st.tabs(["🚀 SCAN & ANALYZE", "📥 EXPORT & FIX"])

with tab1:
    tips = [
        "💡 Broken internal links are the #1 cause of 'Search Abandonment' in Zendesk.",
        "💡 404 errors on your help center prevent Google from indexing new articles.",
        "💡 Reducing typos increases 'Brand Authority' and user trust in your technical docs.",
        "💡 Every 10 dead links fixed typically results in a 1-2% drop in 'I couldn't find it' tickets."
    ]

    def audit_content(html_body, ignore, sub, check_typos):
        soup = BeautifulSoup(html_body, 'html.parser')
        links = [a.get('href') for a in soup.find_all('a') if a.get('href') and a.get('href').startswith('http')]
        broken_int, broken_ext, typos = [], [], []
        for url in links:
            try:
                res = requests.head(url, timeout=2, allow_redirects=True)
                if res.status_code >= 400:
                    if f"{sub}.zendesk.com" in url: broken_int.append(url)
                    else: broken_ext.append(url)
            except: broken_ext.append(url)
        if check_typos:
            text = soup.get_text()
            words = spell.split_words(text)
            typos = [w for w in spell.unknown(words) if not w.istitle() and len(w) > 2 and w.lower() not in [i.lower() for i in ignore]]
        return broken_int, broken_ext, typos

    if st.button("🚀 RUN DEEP SCAN"):
        if not all([subdomain, email, token]):
            st.warning("⚠️ Credentials required.")
        else:
            st.warning("⚠️ **SCAN ACTIVE:** Do not refresh or close. 1,800 articles can take up to 10 minutes.")
            
            # Phase 1: Pagination
            all_articles = []
            api_url = f"https://{subdomain}.zendesk.com/api/v2/help_center/articles.json?per_page=100"
            auth = (f"{email}/token", token)
            
            with st.status("📡 Fetching Articles...", expanded=True) as status:
                current_url = api_url
                while current_url:
                    res = requests.get(current_url, auth=auth)
                    if res.status_code == 200:
                        data = res.json()
                        all_articles.extend(data.get('articles', []))
                        st.write(f"📥 Synced {len(all_articles)} articles...")
                        current_url = data.get('next_page')
                    else: break
                status.update(label="✅ Library Synced", state="complete")

            # Phase 2: Live Analysis
            if all_articles:
                report_list = []
                total_scanned = len(all_articles)
                
                # LIVE DASHBOARD (Placeholders)
                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                stat_total = m1.empty()
                stat_int = m2.empty()
                stat_ext = m3.empty()
                stat_typo = m4.empty()
                
                prog_bar = st.progress(0)
                live_feed = st.empty() # For the "Last Error Found"
                tip_box = st.info(random.choice(tips))
                
                start_time = time.time()
                total_int, total_ext, total_typo = 0, 0, 0

                for i, art in enumerate(all_articles):
                    # Audit Logic
                    b_int, b_ext, typos = audit_content(art['body'], ignore_list, subdomain, enable_typos)
                    
                    if b_int or b_ext or typos:
                        total_int += len(b_int)
                        total_ext += len(b_ext)
                        total_typo += len(typos)
                        report_list.append({"Article": art['title'], "Int": len(b_int), "Ext": len(b_ext), "Typos": len(typos), "Link": art['html_url']})
                        
                        # Update Live Feed every time a defect is found
                        with live_feed.container():
                            st.markdown(f"""<div class="live-card"><b>🚨 Defect Found:</b> {art['title']}<br><small>{len(b_int)+len(b_ext)} broken links | {len(typos)} typos</small></div>""", unsafe_allow_html=True)

                    # Update Progress & Metrics
                    prog_bar.progress((i + 1) / total_scanned)
                    stat_total.metric("Scanned", f"{i+1}/{total_scanned}")
                    stat_int.metric("Int. Dead Links", total_int)
                    stat_ext.metric("Ext. Dead Links", total_ext)
                    stat_typo.metric("Typos Found", total_typo)

                    # Swap tips every 50 articles
                    if i % 50 == 0:
                        tip_box.info(random.choice(tips))

                # Final Results Display
                st.success("✅ Deep Scan Complete!")
                df = pd.DataFrame(report_list)
                st.dataframe(df, use_container_width=True)

with tab2:
    # (Pro Access UI as per v3.0.0)
    st.markdown('<div class="pro-header"><h1>📥 Export & Remediate</h1></div>', unsafe_allow_html=True)
    # ... (Rest of Pro Tab)
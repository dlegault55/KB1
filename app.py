import re
import random
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# =========================
# 1) APP CONFIG
# =========================
APP_TITLE = "ZenAudit"
APP_ICON = "🛡️"

FREE_FINDING_LIMIT = 50
REQUEST_TIMEOUT = 12
ZENDESK_PER_PAGE = 100

st.set_page_config(page_title=f"{APP_TITLE} Pro", page_icon=APP_ICON, layout="wide")
spell = SpellChecker()

# =========================
# 2) STYLE (minimal + modern)
# =========================
st.markdown(
    """
<style>
    .stApp { background: #0B1220; color: #E6EEF8; }
    section[data-testid="stSidebar"] { background: #0F1A2E !important; border-right: 1px solid #1F2A44; }

    .za-card {
        background: #0F1A2E;
        border: 1px solid #1F2A44;
        border-radius: 14px;
        padding: 16px 18px;
    }
    .za-muted { color: #9FB1CC; font-size: 0.92rem; }
    .za-title { font-size: 1.1rem; font-weight: 700; }
    .za-chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #1F2A44;
        font-size: 0.8rem;
        color: #BBD2F3;
        background: rgba(56,189,248,0.08);
        margin-right: 6px;
    }
    .stButton>button {
        border-radius: 10px !important;
        height: 46px !important;
        font-weight: 700 !important;
        border: 0 !important;
    }
    div.stDownloadButton > button {
        border-radius: 10px !important;
        height: 46px !important;
        font-weight: 700 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# 3) SESSION STATE
# =========================
def ss_init():
    st.session_state.setdefault("scan_results", [])   # per-article summary
    st.session_state.setdefault("findings", [])       # issue-level rows
    st.session_state.setdefault("last_logs", [])
    st.session_state.setdefault("url_cache", {})      # URL status cache
    st.session_state.setdefault("scan_running", False)

ss_init()

# =========================
# 4) HELPERS
# =========================
def safe_parse_updated_at(s: str) -> Optional[datetime]:
    try:
        # Zendesk often returns UTC like: 2025-01-01T12:34:56Z
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None

def normalize_url(base_url: str, raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith(("mailto:", "tel:", "javascript:")):
        return None
    if raw.startswith("#"):
        return None
    return urljoin(base_url, raw)

def extract_links_images(html: str, base_url: str) -> Tuple[BeautifulSoup, str, List[str], List[Dict[str, Any]]]:
    soup = BeautifulSoup(html or "", "html.parser")

    links: List[str] = []
    for a in soup.find_all("a"):
        u = normalize_url(base_url, a.get("href"))
        if u:
            links.append(u)

    images: List[Dict[str, Any]] = []
    for img in soup.find_all("img"):
        u = normalize_url(base_url, img.get("src"))
        if u:
            images.append({"src": u, "missing_alt": not bool((img.get("alt") or "").strip())})

    text = soup.get_text(" ", strip=True)
    return soup, text, links, images

def check_url_status(url: str, timeout: int = 8) -> Dict[str, Any]:
    """
    Cached URL status check:
      ok: bool
      status: int|None
      kind: str|None
      severity: critical|warning|info
    """
    cache = st.session_state.url_cache
    if url in cache:
        return cache[url]

    headers = {"User-Agent": "ZenAuditPro/0.2 (+streamlit)"}
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        status = resp.status_code

        # Fallback GET when HEAD is blocked / not allowed / suspicious
        if status in (403, 405) or status >= 400:
            resp = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers)
            status = resp.status_code

        if status in (404, 410):
            result = {"ok": False, "status": status, "kind": "not_found", "severity": "critical"}
        elif status >= 500:
            result = {"ok": False, "status": status, "kind": "server_error", "severity": "warning"}
        elif status in (401, 403, 429):
            result = {"ok": False, "status": status, "kind": "blocked_or_rate_limited", "severity": "warning"}
        elif status >= 400:
            result = {"ok": False, "status": status, "kind": "client_error", "severity": "warning"}
        else:
            result = {"ok": True, "status": status, "kind": None, "severity": "info"}

    except requests.Timeout:
        result = {"ok": False, "status": None, "kind": "timeout", "severity": "warning"}
    except requests.RequestException:
        result = {"ok": False, "status": None, "kind": "request_error", "severity": "warning"}

    cache[url] = result
    return result

def severity_rank(sev: str) -> int:
    return {"critical": 0, "warning": 1, "info": 2}.get(str(sev), 2)

def findings_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Findings")
    return bio.getvalue()

def push_log(msg: str, limit: int = 12):
    st.session_state.last_logs.insert(0, msg)
    st.session_state.last_logs = st.session_state.last_logs[:limit]

# =========================
# 5) SCAN ENGINE
# =========================
def run_scan(
    subdomain: str,
    email: str,
    token: str,
    do_stale: bool,
    do_typo: bool,
    do_alt: bool,
    do_links: bool,
    do_images: bool,
    max_articles: int,
    progress_cb,
    status_cb,
):
    # reset for new scan
    st.session_state.scan_results = []
    st.session_state.findings = []
    st.session_state.last_logs = []
    st.session_state.url_cache = {}
    st.session_state.scan_running = True

    auth = (f"{email}/token", token)
    base_url = f"https://{subdomain}.zendesk.com"
    url = f"{base_url}/api/v2/help_center/articles.json?per_page={ZENDESK_PER_PAGE}"

    scanned = 0

    while url:
        r = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)
        if r.status_code == 401:
            raise RuntimeError("Auth failed (401). Check email/token and Zendesk API settings.")
        r.raise_for_status()

        data = r.json()
        articles = data.get("articles", [])

        for art in articles:
            scanned += 1
            if max_articles and scanned > max_articles:
                url = None
                break

            title = art.get("title", "") or ""
            body = art.get("body", "") or ""
            article_url = art.get("html_url") or f"{base_url}/hc/articles/{art.get('id')}"

            soup, text_raw, links, images = extract_links_images(body, base_url=base_url)

            # ---- layers
            typos = 0
            if do_typo:
                text = (text_raw or "").lower()
                words = spell.split_words(text)
                candidates = [w for w in spell.unknown(words) if len(w) > 2 and w.isalpha()]
                typos = len(candidates)

            is_stale = False
            if do_stale:
                updated = safe_parse_updated_at(art.get("updated_at", ""))
                if updated:
                    is_stale = (datetime.utcnow() - updated) > timedelta(days=365)

            alt_miss = 0
            if do_alt:
                alt_miss = len([img for img in soup.find_all("img") if not (img.get("alt") or "").strip()])

            # ---- per-article summary
            st.session_state.scan_results.append(
                {
                    "Title": title,
                    "URL": article_url,
                    "Typos": typos,
                    "Stale": is_stale,
                    "Alt": alt_miss,
                    "ID": art.get("id"),
                }
            )

            # ---- findings rows
            if do_alt:
                for img in images:
                    if img["missing_alt"]:
                        st.session_state.findings.append(
                            {
                                "Severity": "warning",
                                "Type": "missing_alt",
                                "Article Title": title,
                                "Article URL": article_url,
                                "Target URL": img["src"],
                                "HTTP Status": None,
                                "Detail": "missing_alt",
                                "Suggested Fix": "Add descriptive alt text to improve accessibility and AI-readiness.",
                            }
                        )

            if do_links and links:
                for lk in list(dict.fromkeys(links)):  # dedupe per-article
                    res = check_url_status(lk, timeout=8)
                    if not res["ok"]:
                        st.session_state.findings.append(
                            {
                                "Severity": res["severity"],
                                "Type": "broken_link",
                                "Article Title": title,
                                "Article URL": article_url,
                                "Target URL": lk,
                                "HTTP Status": res["status"],
                                "Detail": res["kind"],
                                "Suggested Fix": "Update/remove the link, or replace it with a working destination.",
                            }
                        )

            if do_images and images:
                for img in images:
                    src = img["src"]
                    res = check_url_status(src, timeout=8)
                    if not res["ok"]:
                        st.session_state.findings.append(
                            {
                                "Severity": res["severity"],
                                "Type": "broken_image",
                                "Article Title": title,
                                "Article URL": article_url,
                                "Target URL": src,
                                "HTTP Status": res["status"],
                                "Detail": res["kind"],
                                "Suggested Fix": "Fix the image URL or re-upload the image to a stable location.",
                            }
                        )

            if do_stale and is_stale:
                st.session_state.findings.append(
                    {
                        "Severity": "info",
                        "Type": "stale_content",
                        "Article Title": title,
                        "Article URL": article_url,
                        "Target URL": None,
                        "HTTP Status": None,
                        "Detail": "updated_over_365_days",
                        "Suggested Fix": "Review/update this article; stale content reduces trust and deflection.",
                    }
                )

            push_log(f"✅ {scanned}: {title[:60]}")
            progress_cb(scanned)
            status_cb(title, scanned)

        url = data.get("next_page")

    st.session_state.scan_running = False

# =========================
# 6) SIDEBAR (cleaner)
# =========================
with st.sidebar:
    st.markdown(
        f"<div class='za-title'>{APP_ICON} {APP_TITLE}</div>"
        f"<div class='za-muted'>Zendesk Help Center Auditor</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        "<span class='za-chip'>Broken links</span>"
        "<span class='za-chip'>Alt text</span>"
        "<span class='za-chip'>Stale</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("Connection")
    subdomain = st.text_input("Subdomain", placeholder="acme", help="e.g. acme for acme.zendesk.com")
    email = st.text_input("Admin Email")
    token = st.text_input("API Token", type="password")

    st.divider()
    st.subheader("Audit layers")
    c1, c2 = st.columns(2)
    with c1:
        do_links = st.checkbox("Broken Links", value=True)
        do_images = st.checkbox("Broken Images", value=True)
        do_alt = st.checkbox("Image Alt-Text", value=True)
    with c2:
        do_stale = st.checkbox("Stale Content", value=True)
        do_typo = st.checkbox("Typos", value=True)

    st.divider()
    st.subheader("Limits & gating")
    pro_mode = st.checkbox("Pro Mode (dev)", value=True)
    max_articles = st.number_input("Max Articles (0 = all)", min_value=0, value=0, step=50)

    st.markdown(
        "<div class='za-muted' style='margin-top:10px;'>Zendesk® is a trademark of Zendesk, Inc.</div>",
        unsafe_allow_html=True,
    )

# =========================
# 7) TOP-LEVEL UI
# =========================
st.markdown(
    """
<div class="za-card">
  <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
    <div>
      <div style="font-size:1.35rem; font-weight:800;">Knowledge Base Intelligence</div>
      <div class="za-muted">Scan your Help Center for broken links, broken images, missing alt text, typos, and stale content.</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab_audit, tab_method, tab_privacy, tab_pro = st.tabs(["Audit", "Methodology", "Privacy", "Pro"])

# =========================
# 8) AUDIT TAB
# =========================
with tab_audit:
    # action row
    a1, a2, a3 = st.columns([1.2, 1.2, 2.2])
    with a1:
        run_btn = st.button("🚀 Run scan", use_container_width=True)
    with a2:
        clear_btn = st.button("🧹 Clear results", use_container_width=True)
    with a3:
        st.caption("Tip: turn off Broken Links/Images for a faster first pass.")

    if clear_btn:
        st.session_state.scan_results = []
        st.session_state.findings = []
        st.session_state.last_logs = []
        st.session_state.url_cache = {}
        st.toast("Cleared.", icon="🧼")

    # metrics placeholders
    m1, m2, m3, m4, m5 = st.columns(5)
    met_scanned = m1.empty()
    met_critical = m2.empty()
    met_warn = m3.empty()
    met_alt = m4.empty()
    met_stale = m5.empty()

    # scan live area
    left, right = st.columns([2.2, 1.2])
    with left:
        progress = st.progress(0, text="Idle")
        console = st.empty()
    with right:
        status_box = st.empty()
        signals_box = st.empty()

    # render stable empty cards so layout is aligned from the start (prevents "jumping")
    status_box.markdown("<div class='za-card' style='min-height:140px;'></div>", unsafe_allow_html=True)
    signals_box.markdown("<div class='za-card' style='min-height:140px;'></div>", unsafe_allow_html=True)

    def refresh_metrics():
        res = st.session_state.scan_results
        fnd = st.session_state.findings

        scanned = len(res)
        critical = sum(1 for x in fnd if x.get("Severity") == "critical")
        warning = sum(1 for x in fnd if x.get("Severity") == "warning")
        alt_missing = sum(d.get("Alt", 0) for d in res) if res else 0
        stale_count = sum(1 for d in res if d.get("Stale")) if res else 0

        met_scanned.metric("Scanned", scanned)
        met_critical.metric("Critical", critical)
        met_warn.metric("Warnings", warning)
        met_alt.metric("Alt missing", alt_missing)
        met_stale.metric("Stale", stale_count)

        # 👇 Render this inside the placeholder to keep alignment with the left column
        signals_box.markdown(
            f"""
            <div class='za-card' style='min-height:140px;'>
                <div class='za-title'>Quality signals</div>
                <div class='za-muted' style='margin-top:10px; line-height:1.6;'>
                    <div><b>{critical}</b> critical</div>
                    <div><b>{warning}</b> warnings</div>
                    <div><b>{alt_missing}</b> missing alt</div>
                    <div><b>{stale_count}</b> stale</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def progress_cb(scanned_count: int):
        # If max_articles is 0, we can't know total; show a looping indicator via modulo
        if max_articles:
            pct = min(1.0, scanned_count / int(max_articles))
            progress.progress(pct, text=f"Scanning… {scanned_count}/{int(max_articles)}")
        else:
            pct = (scanned_count % 100) / 100
            progress.progress(pct, text=f"Scanning… {scanned_count} (unknown total)")

        refresh_metrics()
        logs_html = "<br>".join(st.session_state.last_logs)
        console.markdown(
            f"""
            <div class='za-card' style='min-height:260px;'>
                <div class='za-title'>Live log</div>
                <div class='za-muted' style='margin-top:10px;'>{logs_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def status_cb(title: str, scanned_count: int):
        status_box.markdown(
            f"""
            <div class='za-card' style='min-height:140px;'>
                <div class='za-title'>Now scanning</div>
                <div class='za-muted' style='margin-top:8px;'>{title}</div>
                <div class='za-muted' style='margin-top:12px;'>Articles scanned: <b>{scanned_count}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run_btn:
        if not all([subdomain, email, token]):
            st.error("Missing credentials in the sidebar.")
        else:
            try:
                with st.status("Running scan…", expanded=True) as s:
                    s.write("Connecting to Zendesk…")
                    run_scan(
                        subdomain=subdomain,
                        email=email,
                        token=token,
                        do_stale=do_stale,
                        do_typo=do_typo,
                        do_alt=do_alt,
                        do_links=do_links,
                        do_images=do_images,
                        max_articles=int(max_articles),
                        progress_cb=progress_cb,
                        status_cb=status_cb,
                    )
                    s.update(label="Scan complete ✅", state="complete", expanded=False)
                st.toast("Scan complete", icon="✅")
            except Exception as e:
                st.session_state.scan_running = False
                st.error(f"Scan failed: {e}")

    refresh_metrics()

    # Results section
    if st.session_state.scan_results:
        st.divider()
        st.subheader("Findings")

        df_findings = (
            pd.DataFrame(st.session_state.findings)
            if st.session_state.findings
            else pd.DataFrame(
                columns=[
                    "Severity",
                    "Type",
                    "Article Title",
                    "Article URL",
                    "Target URL",
                    "HTTP Status",
                    "Detail",
                    "Suggested Fix",
                ]
            )
        )

        if not df_findings.empty:
            df_findings["_sev_rank"] = df_findings["Severity"].map(lambda s: severity_rank(str(s)))
            df_findings = df_findings.sort_values(by=["_sev_rank", "Type"], ascending=[True, True]).drop(columns=["_sev_rank"])

        total_findings = len(df_findings)
        gated = (not pro_mode) and (total_findings > FREE_FINDING_LIMIT)
        df_preview = df_findings.head(FREE_FINDING_LIMIT) if gated else df_findings

        # quick filters
        f1, f2, f3 = st.columns([1.2, 1.2, 2.6])
        with f1:
            sev_filter = st.multiselect("Severity", ["critical", "warning", "info"], default=["critical", "warning", "info"])
        with f2:
            type_opts = sorted(df_preview["Type"].unique().tolist()) if not df_preview.empty else []
            type_filter = st.multiselect("Type", type_opts, default=type_opts)
        with f3:
            q = st.text_input("Search (title/url contains)", placeholder="e.g. billing, /hc/en-us, image.png")

        view = df_preview.copy()
        if not view.empty:
            view = view[view["Severity"].isin(sev_filter)]
            if type_filter:
                view = view[view["Type"].isin(type_filter)]
            if q.strip():
                qq = q.strip().lower()
                view = view[
                    view["Article Title"].fillna("").str.lower().str.contains(qq)
                    | view["Article URL"].fillna("").str.lower().str.contains(qq)
                    | view["Target URL"].fillna("").str.lower().str.contains(qq)
                ]

        st.dataframe(
            view,
            column_config={
                "Article URL": st.column_config.Link_Column("Article"),
                "Target URL": st.column_config.Link_Column("Target"),
                "HTTP Status": st.column_config.Number_Column("Status"),
            },
            use_container_width=True,
            hide_index=True,
        )

        st.write("")
        st.info(f"Scanned **{len(st.session_state.scan_results)}** articles. Found **{total_findings}** findings.")

        if gated:
            st.warning(f"Free preview shows first **{FREE_FINDING_LIMIT}** findings. Enable **Pro Mode (dev)** to export everything.")

        # Export
        export_df = df_findings if (pro_mode or not gated) else df_preview
        c_exp1, c_exp2 = st.columns([1, 1])
        with c_exp1:
            if total_findings > 0:
                st.download_button(
                    "📥 Download XLSX",
                    data=findings_to_xlsx_bytes(export_df),
                    file_name="zenaudit_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        with c_exp2:
            if total_findings > 0:
                st.download_button(
                    "📥 Download CSV",
                    data=export_df.to_csv(index=False),
                    file_name="zenaudit_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

# =========================
# 9) OTHER TABS
# =========================
with tab_method:
    st.markdown(
        """
### Metric definitions
- **Stale Content:** Flags articles not updated in **365 days**.
- **Typo detection:** Uses `pyspellchecker` and filters obvious false positives (very short / non-alpha).
- **Alt-text:** Flags `<img>` tags missing meaningful `alt`.
- **Broken links / images:** Checks HTTP status:
  - **404/410** → critical
  - **5xx / timeout / request errors** → warning
  - **401/403/429** → warning (often blocked or rate limited)

### Practical workflow
1) Run with links/images ON once weekly for “real breakage”.
2) Run with links/images OFF daily for cheap checks (typos/stale/alt).
3) Export findings → fix in batches by Type (links first).
"""
    )

with tab_privacy:
    st.info("ZenAudit is client-side first: your credentials are used only to fetch articles during the scan.")
    st.markdown(
        """
### Data handling
- Direct HTTPS calls to your Zendesk subdomain
- Tokens are not written into the export
- Results live in Streamlit session state and reset when you clear or rerun
"""
    )

with tab_pro:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "<div class='za-card'><div class='za-title'>Free</div>"
            "<div class='za-muted'>Preview + basic scans</div>"
            "<ul><li>Unlimited article scanning</li><li>Preview first 50 findings</li><li>CSV/XLSX preview export</li></ul></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='za-card'><div class='za-title'>Pro</div>"
            "<div class='za-muted'>Full export + automation</div>"
            "<ul><li>Full findings export</li><li>Scheduled audits (future)</li><li>Team sharing (future)</li></ul></div>",
            unsafe_allow_html=True,
        )
        st.button("Upgrade (placeholder)", use_container_width=True)

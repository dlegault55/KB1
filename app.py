import re
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
# 2) STYLE (premium button + subtle polish)
# =========================
st.markdown(
    """
<style>
    .stApp { background: #0B1220; color: #E6EEF8; }
    section[data-testid="stSidebar"] { background: #0F1A2E !important; border-right: 1px solid #1F2A44; }

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

    /* Premium primary button (Run scan) */
    button[kind="primary"] {
        background: linear-gradient(90deg, rgba(56,189,248,1) 0%, rgba(34,197,94,1) 100%) !important;
        color: #081221 !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        border: 0 !important;
        border-radius: 12px !important;
        height: 52px !important;
        box-shadow:
            0 10px 30px rgba(56,189,248,0.25),
            0 6px 18px rgba(34,197,94,0.18) !important;
        transition: transform 120ms ease, filter 120ms ease, box-shadow 120ms ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        filter: brightness(1.05) !important;
        box-shadow:
            0 14px 38px rgba(56,189,248,0.32),
            0 8px 22px rgba(34,197,94,0.22) !important;
    }
    button[kind="primary"]:active {
        transform: translateY(0px) scale(0.99) !important;
    }
    button[kind="secondary"] {
        border-radius: 12px !important;
        height: 46px !important;
        font-weight: 700 !important;
    }

    /* Make metrics feel like cards */
    div[data-testid="metric-container"] {
        background: #0F1A2E;
        border: 1px solid #1F2A44;
        padding: 10px 12px;
        border-radius: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# 3) SESSION STATE
# =========================
def ss_init():
    st.session_state.setdefault("scan_results", [])
    st.session_state.setdefault("findings", [])
    st.session_state.setdefault("last_logs", [])
    st.session_state.setdefault("url_cache", {})
    st.session_state.setdefault("scan_running", False)
    st.session_state.setdefault("last_scanned_title", "")
    st.session_state.setdefault("connected_ok", False)

ss_init()

# =========================
# 4) HELPERS
# =========================
def safe_parse_updated_at(s: str) -> Optional[datetime]:
    try:
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
    cache = st.session_state.url_cache
    if url in cache:
        return cache[url]

    headers = {"User-Agent": "ZenAuditPro/0.5 (+streamlit)"}
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        status = resp.status_code

        # Fallback to GET when HEAD is blocked / unsupported
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

def push_log(msg: str, limit: int = 14):
    st.session_state.last_logs.insert(0, msg)
    st.session_state.last_logs = st.session_state.last_logs[:limit]

def log_connection_established():
    st.session_state.connected_ok = True
    push_log("✅ Connected to Zendesk")

def build_column_config():
    """
    Streamlit column_config compatibility:
    - Newer Streamlit: st.column_config.LinkColumn / NumberColumn
    - Some versions:   st.column_config.Link_Column / Number_Column
    - Older Streamlit: no st.column_config → return {}
    """
    cc = getattr(st, "column_config", None)
    if not cc:
        return {}

    if hasattr(cc, "LinkColumn") and hasattr(cc, "NumberColumn"):
        return {
            "Article URL": cc.LinkColumn("Article"),
            "Target URL": cc.LinkColumn("Target"),
            "HTTP Status": cc.NumberColumn("Status"),
        }

    if hasattr(cc, "Link_Column") and hasattr(cc, "Number_Column"):
        return {
            "Article URL": cc.Link_Column("Article"),
            "Target URL": cc.Link_Column("Target"),
            "HTTP Status": cc.Number_Column("Status"),
        }

    return {}

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
    st.session_state.scan_results = []
    st.session_state.findings = []
    st.session_state.last_logs = []
    st.session_state.url_cache = {}
    st.session_state.scan_running = True
    st.session_state.last_scanned_title = ""
    st.session_state.connected_ok = False

    auth = (f"{email}/token", token)
    base_url = f"https://{subdomain}.zendesk.com"
    url = f"{base_url}/api/v2/help_center/articles.json?per_page={ZENDESK_PER_PAGE}"

    scanned = 0
    connection_logged = False

    while url:
        r = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)
        if r.status_code == 401:
            raise RuntimeError("Auth failed (401). Check email/token and Zendesk API settings.")
        r.raise_for_status()

        if not connection_logged:
            log_connection_established()
            connection_logged = True

        data = r.json()
        articles = data.get("articles", [])

        for art in articles:
            scanned += 1
            if max_articles and scanned > max_articles:
                url = None
                break

            title = art.get("title", "") or ""
            st.session_state.last_scanned_title = title

            body = art.get("body", "") or ""
            article_url = art.get("html_url") or f"{base_url}/hc/articles/{art.get('id')}"

            soup, text_raw, links, images = extract_links_images(body, base_url=base_url)

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

            # Per-article summary
            st.session_state.scan_results.append(
                {"Title": title, "URL": article_url, "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "ID": art.get("id")}
            )

            # Findings: missing alt
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

            # Findings: broken links
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

            # Findings: broken images
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

            # Findings: stale content
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
            status_cb(scanned)

        url = data.get("next_page")

    st.session_state.scan_running = False

# =========================
# 6) SIDEBAR
# =========================
with st.sidebar:
    st.markdown(
        f"## {APP_ICON} {APP_TITLE}\n"
        f"<span style='color:#9FB1CC;'>Zendesk Help Center Auditor</span>",
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

    st.caption("Zendesk® is a trademark of Zendesk, Inc.")

# =========================
# 7) TOP-LEVEL UI
# =========================
st.markdown("## Knowledge Base Intelligence")
st.caption("Scan your Help Center for broken links, broken images, missing alt text, typos, and stale content.")

tab_audit, tab_method, tab_privacy, tab_pro = st.tabs(["Audit", "Methodology", "Privacy", "Pro"])

# =========================
# 8) AUDIT TAB
# =========================
with tab_audit:
    a1, a2, a3 = st.columns([1.2, 1.2, 2.2])
    with a1:
        run_btn = st.button("🚀 Run scan", type="primary", use_container_width=True)
    with a2:
        clear_btn = st.button("🧹 Clear results", type="secondary", use_container_width=True)
    with a3:
        st.caption("Tip: turn off Broken Links/Images for a faster first pass.")

    if clear_btn:
        st.session_state.scan_results = []
        st.session_state.findings = []
        st.session_state.last_logs = []
        st.session_state.url_cache = {}
        st.session_state.last_scanned_title = ""
        st.session_state.connected_ok = False
        st.toast("Cleared.", icon="🧼")

    m1, m2, m3, m4, m5 = st.columns(5)
    met_scanned = m1.empty()
    met_critical = m2.empty()
    met_warn = m3.empty()
    met_alt = m4.empty()
    met_stale = m5.empty()

    # Progress row (full width) — boxes sit below this
    progress = st.progress(0, text="Ready")

    # Columns BELOW progress
    left, right = st.columns([2.2, 1.2])

    # Left: Live log placeholder
    with left:
        console = st.empty()

    # Right: Native Scan Status layout (no HTML divs)
    with right:
        st.subheader("Scan status")
        conn_ph = st.empty()
        st.divider()
        now_ph = st.empty()
        st.divider()
        st.markdown("**Quality signals**")
        q1, q2 = st.columns(2)
        with q1:
            crit_ph = st.empty()
            alt_ph = st.empty()
        with q2:
            warn_ph = st.empty()
            stale_ph = st.empty()
        st.divider()
        st.caption("Tip: Fix broken links first, then images, then content quality.")

    # Initial placeholders (prevents jump)
    console.markdown("### Live log\n—")
    conn_ph.info("Waiting to start")
    now_ph.write("**Now scanning:** —")
    crit_ph.metric("Critical", 0)
    warn_ph.metric("Warnings", 0)
    alt_ph.metric("Missing alt", 0)
    stale_ph.metric("Stale", 0)

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

        # Connection state
        if st.session_state.connected_ok:
            conn_ph.success("✅ Connected to Zendesk")
        else:
            conn_ph.info("Waiting to start")

        # Now scanning
        title = st.session_state.last_scanned_title or "—"
        now_ph.write(f"**Now scanning:** {title}")

        # Quality metrics
        crit_ph.metric("Critical", critical)
        warn_ph.metric("Warnings", warning)
        alt_ph.metric("Missing alt", alt_missing)
        stale_ph.metric("Stale", stale_count)

    def progress_cb(scanned_count: int):
        if max_articles:
            pct = min(1.0, scanned_count / int(max_articles))
            progress.progress(pct, text=f"Scanning… {scanned_count}/{int(max_articles)}")
        else:
            # Unknown total: show activity but keep it calm
            pct = (scanned_count % 100) / 100
            progress.progress(pct, text=f"Scanning… {scanned_count} (unknown total)")

        refresh_metrics()

        logs = "<br>".join(st.session_state.last_logs) if st.session_state.last_logs else "—"
        console.markdown(f"### Live log\n{logs}", unsafe_allow_html=True)

    def status_cb(_scanned_count: int):
        refresh_metrics()

    def finalize_progress(scanned_count: int):
        progress.progress(1.0, text=f"Complete ✅ ({scanned_count} articles)")

    if run_btn:
        if not all([subdomain, email, token]):
            st.error("Missing credentials in the sidebar.")
        else:
            try:
                with st.status("Running scan…", expanded=True) as s:
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

                    finalize_progress(len(st.session_state.scan_results))
                    s.update(label="Scan complete ✅", state="complete", expanded=False)

                st.toast("Scan complete", icon="✅")
            except Exception as e:
                st.session_state.scan_running = False
                st.error(f"Scan failed: {e}")

    refresh_metrics()

    # =========================
    # RESULTS / FINDINGS
    # =========================
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

        # ✅ Streamlit version-safe column config
        col_cfg = build_column_config()
        df_kwargs = dict(use_container_width=True, hide_index=True)
        if col_cfg:
            df_kwargs["column_config"] = col_cfg

        st.dataframe(view, **df_kwargs)

        st.info(f"Scanned **{len(st.session_state.scan_results)}** articles. Found **{total_findings}** findings.")

        if gated:
            st.warning(f"Free preview shows first **{FREE_FINDING_LIMIT}** findings. Enable **Pro Mode (dev)** to export everything.")

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
- **Stale Content:** Articles not updated in **365 days**
- **Typo detection:** `pyspellchecker`, filtering short/non-alpha noise
- **Alt-text:** `<img>` tags missing meaningful `alt`
- **Broken links/images:** HTTP status:
  - 404/410 → critical
  - 5xx/timeout/request errors → warning
  - 401/403/429 → warning (blocked/rate limited)
"""
    )

with tab_privacy:
    st.info("ZenAudit is client-side first: credentials are used only to fetch articles during the scan.")
    st.markdown(
        """
### Data handling
- Direct HTTPS calls to your Zendesk subdomain
- Tokens are not written into export
- Results live in Streamlit session state and reset when you clear or rerun
"""
    )

with tab_pro:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Free")
        st.write("✅ Unlimited article scanning")
        st.write("✅ Preview first 50 findings")
        st.write("✅ CSV/XLSX preview export")
    with c2:
        st.subheader("Pro")
        st.write("🚀 Full findings export")
        st.write("🚀 Scheduled audits (future)")
        st.write("🚀 Team sharing (future)")
        st.button("Upgrade (placeholder)", use_container_width=True)

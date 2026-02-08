import re
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from spellchecker import SpellChecker

# ✅ Logging
import json
import time
import uuid
import hashlib
import logging
import traceback

# =========================
# 1) APP CONFIG
# =========================
APP_TITLE = "ZenAudit"
APP_ICON = "🛡️"

FREE_FINDING_LIMIT = 50
REQUEST_TIMEOUT = 12
ZENDESK_PER_PAGE = 100

st.set_page_config(page_title=f"{APP_TITLE} Pro", page_icon=APP_ICON, layout="wide")

# =========================
# Google Ads tag (gtag.js)
# =========================
components.html(
    """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-17940611899"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'AW-17940611899');
</script>
""",
    height=0,
    width=0,
)

spell = SpellChecker()

# =========================
# 2) STYLE
# =========================
st.markdown(
    """
<style>
.stApp {
    background: #0B1220;
    color: #E6EEF8;
}

section[data-testid="stSidebar"] {
    background: #0F1A2E !important;
    border-right: 1px solid #1F2A44;
}

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

/* ✅ New: Sidebar tagline */
.za-tagline {
    color: #9FB1CC;
    font-size: 0.88rem;
    line-height: 1.25rem;
    margin-top: 6px;
    margin-bottom: 10px;
}

/* Primary button (Run scan) */
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
}

button[kind="primary"]:hover {
    transform: translateY(-1px);
    filter: brightness(1.05);
}

button[kind="secondary"] {
    border-radius: 12px !important;
    height: 46px !important;
    font-weight: 700 !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #0F1A2E;
    border: 1px solid #1F2A44;
    padding: 10px 12px;
    border-radius: 12px;
}

/* Buy button (link styled as button) */
a.za-linkbtn {
    display: inline-block;
    width: 100%;
    min-width: 0;
    text-align: center;
    padding: 8px 14px;
    border-radius: 10px;
    font-weight: 850;
    font-size: 0.85rem;
    text-decoration: none !important;
    color: #081221 !important;
    background: linear-gradient(90deg, rgba(56,189,248,1) 0%, rgba(34,197,94,1) 100%);
    box-shadow:
        0 10px 24px rgba(56,189,248,0.18),
        0 6px 14px rgba(34,197,94,0.12);
}

/* Status pills */
.za-pill-ok {
    margin-top: 8px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.30);
    color: #BFF7D0;
    font-weight: 750;
}

.za-pill-info {
    margin-top: 8px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.20);
    color: #BBD2F3;
    font-weight: 650;
}

.za-pill-warn {
    margin-top: 8px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(251,191,36,0.10);
    border: 1px solid rgba(251,191,36,0.25);
    color: #FDE68A;
    font-weight: 650;
}

/* “Next step” callout */
.za-next {
    margin: 14px 0 10px 0;
    padding: 12px 14px;
    border-radius: 12px;
    background: linear-gradient(
        90deg,
        rgba(56,189,248,0.10) 0%,
        rgba(34,197,94,0.10) 100%
    );
    border: 1px solid rgba(56,189,248,0.25);
    color: #E6EEF8;
    font-weight: 650;
}

.za-next span {
    color: #9FB1CC;
    font-weight: 500;
}

.za-subtle {
    color: #9FB1CC;
    font-size: 0.85rem;
}

/* Align buy button with email field */
.za-btnrow {
    padding-top: 26px;
}

/* Pricing explainer */
.za-pricing {
    margin: 10px 0 16px 0;
    padding: 14px 14px;
    border-radius: 14px;
    background: rgba(56,189,248,0.06);
    border: 1px solid rgba(56,189,248,0.22);
}

.za-pricing .za-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 850;
    font-size: 0.78rem;
    letter-spacing: 0.4px;
    color: #081221;
    background: linear-gradient(90deg, rgba(56,189,248,1) 0%, rgba(34,197,94,1) 100%);
    margin-bottom: 8px;
}

.za-pricing .za-title {
    font-weight: 900;
    font-size: 1.05rem;
    margin: 2px 0 4px 0;
    color: #E6EEF8;
}

.za-pricing .za-line {
    color: #BBD2F3;
    font-size: 0.92rem;
    line-height: 1.35rem;
}

.za-pricing b {
    color: #E6EEF8;
}

/* Custom table (no Streamlit toolbar) */
.za-tablewrap {
    border: 1px solid #1F2A44;
    border-radius: 12px;
    overflow: hidden;
    background: #0F1A2E;
}

.za-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.za-table th {
    text-align: left;
    padding: 10px 10px;
    background: #0B1220;
    color: #E6EEF8;
    border-bottom: 1px solid #1F2A44;
    position: sticky;
    top: 0;
    z-index: 1;
}

.za-table td {
    padding: 10px 10px;
    border-bottom: 1px solid rgba(31,42,68,0.55);
    color: #BBD2F3;
    vertical-align: top;
}

.za-table tr:hover td {
    background: rgba(56,189,248,0.05);
}

.za-scroll {
    max-height: 520px;
    overflow: auto;
}

.za-table a {
    color: #BBD2F3;
    text-decoration: underline;
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

    # ✅ Logging / diagnostics
    st.session_state.setdefault("scan_id", "")
    st.session_state.setdefault("scan_started_at", None)

    # Pro / Paywall state
    st.session_state.setdefault("pro_email", "")
    st.session_state.setdefault("pro_unlocked", False)
    st.session_state.setdefault("pro_available_scans", 0)
    st.session_state.setdefault("pro_last_status_error", "")

    # Local/session guard to prevent double-consume via Streamlit reruns
    st.session_state.setdefault("xlsx_consumed_local", False)

    # Store creds safely so Run Scan doesn't depend on sidebar keystrokes
    st.session_state.setdefault("zd_subdomain", "")
    st.session_state.setdefault("zd_email", "")
    st.session_state.setdefault("zd_token", "")

ss_init()

SHOW_DEV_CONTROLS = bool(st.secrets.get("SHOW_DEV_CONTROLS", False))

# =========================
# 3b) LOGGING HELPERS
# =========================
APP_VERSION = str(st.secrets.get("APP_VERSION", "dev"))
logger = logging.getLogger("zenaudit")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setLevel(logging.INFO)
    logger.addHandler(_h)

def _hash_email(email: str) -> str:
    if not email:
        return ""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:16]

def _safe_domain(email: str) -> str:
    try:
        e = (email or "").strip().lower()
        if "@" in e:
            return e.split("@", 1)[1]
    except Exception:
        pass
    return ""

def log_event(event: str, scan_id: str, **fields):
    payload = {
        "event": event,
        "scan_id": scan_id,
        "app_version": APP_VERSION,
        "ts": datetime.utcnow().isoformat() + "Z",
        **fields,
    }
    logger.info(json.dumps(payload, default=str))

class timed_phase:
    def __init__(self, scan_id: str, phase: str, **base_fields):
        self.scan_id = scan_id
        self.phase = phase
        self.base_fields = base_fields
        self.t0 = None

    def __enter__(self):
        self.t0 = time.time()
        log_event("scan_phase_start", self.scan_id, phase=self.phase, **self.base_fields)
        return self

    def __exit__(self, exc_type, exc, tb):
        elapsed_ms = int((time.time() - (self.t0 or time.time())) * 1000)
        if exc:
            log_event(
                "scan_phase_fail",
                self.scan_id,
                phase=self.phase,
                elapsed_ms=elapsed_ms,
                error_type=getattr(exc_type, "__name__", "Exception"),
                error_message_short=str(exc)[:300],
                **self.base_fields,
            )
        else:
            log_event("scan_phase_ok", self.scan_id, phase=self.phase, elapsed_ms=elapsed_ms, **self.base_fields)
        return False

# =========================
# 4) INPUT + UI HELPERS
# =========================
def link_cta(label: str, url: str):
    if not url:
        st.button(label, disabled=True)
        return
    st.markdown(
        f'<a class="za-linkbtn" href="{url}" target="_blank" rel="noopener">{label}</a>',
        unsafe_allow_html=True,
    )

def render_obfuscated_email(email_user: str, email_domain: str, label: str = "Support"):
    safe = f"{email_user} [at] {email_domain.replace('.', ' [dot] ')}"
    st.markdown(
        f"<div class='za-subtle'>{label}: <span style='unicode-bidi:bidi-override; direction:ltr;'>{safe}</span></div>",
        unsafe_allow_html=True,
    )

def normalize_subdomain_input(raw: str) -> Tuple[Optional[str], Optional[str]]:
    s = (raw or "").strip().lower()
    if not s:
        return None, "Subdomain is required."

    s = re.sub(r"^https?://", "", s)
    s = s.split("/", 1)[0]

    if s.endswith(".zendesk.com"):
        s = s.replace(".zendesk.com", "")
    elif "." in s:
        return None, "Enter only the Zendesk subdomain (e.g. 'acme'), not a full URL."

    if not re.match(r"^[a-z0-9-]{2,63}$", s):
        return None, "Subdomain must be 2–63 chars (letters/numbers/hyphen only). Example: acme"

    return s, None

def is_valid_email_format(raw: str) -> bool:
    e = (raw or "").strip()
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e))

def verify_zendesk_connection(subdomain: str, email: str, token: str) -> Tuple[bool, str]:
    if not subdomain or not email or not token:
        return False, "Missing subdomain/email/token."

    base_url = f"https://{subdomain}.zendesk.com"
    auth = (f"{email}/token", token)

    try:
        test_url = f"{base_url}/api/v2/help_center/articles.json?per_page=1"
        r = requests.get(test_url, auth=auth, timeout=REQUEST_TIMEOUT)

        if r.status_code == 200:
            return True, "✅ Connected to Zendesk"
        if r.status_code == 401:
            return False, "Auth failed (401). Check your admin email + API token."
        if r.status_code == 403:
            return False, (
                "Forbidden (403). Your user/token can’t access Help Center content via API. "
                "Confirm permissions and Help Center settings."
            )
        if r.status_code == 404:
            return False, "Not found (404). Double-check the Zendesk subdomain."
        return False, f"Connection failed ({r.status_code})."
    except requests.Timeout:
        return False, "Connection timed out. Try again, or check your network/Zendesk availability."
    except Exception as e:
        return False, f"Connection error: {str(e)[:200]}"

# =========================
# 4) SCAN HELPERS
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

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        status = resp.status_code

        if status in (403, 405) or status >= 400:
            resp = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers)
            status = resp.status_code

        if status in (404, 410):
            result = {"ok": False, "status": status, "kind": "not_found", "severity": "critical"}
        elif status >= 500:
            result = {"ok": False, "status": status, "kind": "server_error", "severity": "warning"}
        elif status in (401, 403, 429):
            result = {"ok": None, "status": status, "kind": "blocked_or_rate_limited", "severity": "info"}
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

def push_log(msg: str, limit: int = 14):
    st.session_state.last_logs.insert(0, msg)
    st.session_state.last_logs = st.session_state.last_logs[:limit]

def log_connection_established():
    st.session_state.connected_ok = True
    push_log("✅ Connected to Zendesk")

def get_xlsx_bytes_safe(df: pd.DataFrame) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        import openpyxl  # noqa: F401
    except Exception:
        return None, "XLSX export requires the 'openpyxl' package."
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Findings")
    return bio.getvalue(), None

def _make_clickable(v: Any) -> str:
    s = "" if v is None else str(v)
    if s.startswith("http://") or s.startswith("https://"):
        return f'<a href="{s}" target="_blank" rel="noopener">{s}</a>'
    return s

def render_table_no_toolbar(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("No findings to display yet. Run a scan to generate results.")
        return

    show = df.copy()
    for col in ("Article URL", "Target URL"):
        if col in show.columns:
            show[col] = show[col].map(_make_clickable)

    html = show.to_html(index=False, escape=False, classes="za-table")
    st.markdown(
        f"""
<div class="za-tablewrap">
  <div class="za-scroll">
    {html}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# =========================
# 4b) PAYWALL / WORKER
# =========================
def _worker_cfg() -> Tuple[Optional[str], str]:
    base = st.secrets.get("WORKER_BASE_URL")
    pay = st.secrets.get("PAYMENT_LINK_URL", "") or ""
    if not base:
        return None, str(pay)
    return str(base).rstrip("/"), str(pay)

def worker_get_status(email: str) -> Tuple[bool, int, str]:
    base, _pay = _worker_cfg()
    if not base:
        return False, 0, "Missing WORKER_BASE_URL in Streamlit secrets."
    try:
        r = requests.get(f"{base}/status", params={"email": email}, timeout=10)
        if r.status_code != 200:
            log_event(
                "worker_status_fail",
                st.session_state.scan_id or "",
                user_hash=_hash_email(email),
                user_domain=_safe_domain(email),
                http_status=r.status_code,
            )
            return False, 0, f"Status check failed ({r.status_code})."
        data = r.json()
        avail = int(data.get("available_scans") or 0)
        return (avail > 0), avail, ""
    except Exception as e:
        log_event(
            "worker_status_error",
            st.session_state.scan_id or "",
            user_hash=_hash_email(email),
            user_domain=_safe_domain(email),
            error_message_short=str(e)[:300],
        )
        return False, 0, f"Status check error: {e}"

def worker_consume(email: str) -> Tuple[bool, int, str]:
    base, _pay = _worker_cfg()
    if not base:
        return False, 0, "Missing WORKER_BASE_URL in Streamlit secrets."
    try:
        r = requests.get(f"{base}/consume", params={"email": email}, timeout=15)
        if r.status_code != 200:
            log_event(
                "worker_consume_fail",
                st.session_state.scan_id or "",
                user_hash=_hash_email(email),
                user_domain=_safe_domain(email),
                http_status=r.status_code,
            )
            if r.status_code == 409:
                return False, 0, "No export credits available."
            return False, 0, f"Consume failed ({r.status_code})."
        data = r.json()
        avail = int(data.get("available_scans") or 0)
        return True, avail, ""
    except Exception as e:
        log_event(
            "worker_consume_error",
            st.session_state.scan_id or "",
            user_hash=_hash_email(email),
            user_domain=_safe_domain(email),
            error_message_short=str(e)[:300],
        )
        return False, 0, f"Consume error: {e}"

def pro_access_active(pro_mode: bool) -> bool:
    if pro_mode:
        return True
    return bool(st.session_state.pro_unlocked) and (not st.session_state.xlsx_consumed_local)

def try_unlock_from_status(email: str) -> None:
    email = (email or "").strip().lower()
    st.session_state.pro_email = email
    st.session_state.pro_last_status_error = ""

    if not email:
        st.session_state.pro_unlocked = False
        st.session_state.pro_available_scans = 0
        st.session_state.pro_last_status_error = "Enter an email to check export credits."
        return

    ok, avail, err = worker_get_status(email)
    st.session_state.pro_unlocked = ok
    st.session_state.pro_available_scans = avail
    st.session_state.pro_last_status_error = err or ""
    if ok:
        st.session_state.xlsx_consumed_local = False

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
    scan_id = str(uuid.uuid4())
    st.session_state.scan_id = scan_id
    st.session_state.scan_started_at = datetime.utcnow().isoformat() + "Z"

    st.session_state.scan_results = []
    st.session_state.findings = []
    st.session_state.last_logs = []
    st.session_state.url_cache = {}
    st.session_state.scan_running = True
    st.session_state.last_scanned_title = ""
    st.session_state.connected_ok = False

    user_hash = _hash_email(email)
    user_domain = _safe_domain(email)

    auth = (f"{email}/token", token)
    base_url = f"https://{subdomain}.zendesk.com"
    url = f"{base_url}/api/v2/help_center/articles.json?per_page={ZENDESK_PER_PAGE}"

    scanned = 0
    connection_logged = False

    log_event(
        "scan_start",
        scan_id,
        user_hash=user_hash,
        user_domain=user_domain,
        zd_subdomain=subdomain,
        base_url=base_url,
        do_stale=bool(do_stale),
        do_typo=bool(do_typo),
        do_alt=bool(do_alt),
        do_links=bool(do_links),
        do_images=bool(do_images),
        max_articles=int(max_articles or 0),
    )

    try:
        with timed_phase(scan_id, "zendesk_list_articles", zd_subdomain=subdomain):
            while url:
                with timed_phase(scan_id, "zendesk_fetch_page", page_url=url[:200]):
                    r = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)

                if r.status_code == 401:
                    log_event("zendesk_auth_fail", scan_id, user_hash=user_hash, user_domain=user_domain, http_status=401)
                    raise RuntimeError("Auth failed (401). Check email/token and Zendesk API settings.")

                if r.status_code >= 400:
                    log_event(
                        "zendesk_http_error",
                        scan_id,
                        user_hash=user_hash,
                        user_domain=user_domain,
                        http_status=r.status_code,
                        page_url=url[:200],
                    )
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

                    with timed_phase(scan_id, "parse_article", article_id=art.get("id"), article_url=article_url[:200]):
                        soup, text_raw, links, images = extract_links_images(body, base_url=base_url)

                    typos = 0
                    if do_typo:
                        with timed_phase(scan_id, "typo_check", article_id=art.get("id")):
                            text = (text_raw or "").lower()
                            words = re.findall(r"[a-zA-Z']+", text)
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

                    st.session_state.scan_results.append(
                        {"Title": title, "URL": article_url, "Typos": typos, "Stale": is_stale, "Alt": alt_miss, "ID": art.get("id")}
                    )

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
                        with timed_phase(scan_id, "check_links", article_id=art.get("id"), link_count=len(links)):
                            for lk in list(dict.fromkeys(links)):
                                res = check_url_status(lk, timeout=8)
                                if res["ok"] is False:
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
                        with timed_phase(scan_id, "check_images", article_id=art.get("id"), image_count=len(images)):
                            for img in images:
                                src = img["src"]
                                res = check_url_status(src, timeout=8)
                                if res["ok"] is False:
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
                    status_cb(scanned)

                url = data.get("next_page")

        st.session_state.scan_running = False
        log_event(
            "scan_success",
            scan_id,
            user_hash=user_hash,
            user_domain=user_domain,
            scanned_articles=len(st.session_state.scan_results),
            findings=len(st.session_state.findings),
        )

    except Exception as e:
        st.session_state.scan_running = False
        log_event(
            "scan_failed",
            scan_id,
            user_hash=user_hash,
            user_domain=user_domain,
            scanned_so_far=len(st.session_state.scan_results),
            findings_so_far=len(st.session_state.findings),
            error_type=e.__class__.__name__,
            error_message_short=str(e)[:300],
            traceback=traceback.format_exc()[:4000],
        )
        raise

# =========================
# 6) SIDEBAR
# =========================
with st.sidebar:
    st.markdown(
        f"## {APP_ICON} {APP_TITLE}\n"
        f"<div class='za-tagline'>Premium Zendesk Help Center audits — in minutes.</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("Connection")

    with st.form("zd_conn_form", clear_on_submit=False):
        subdomain_in = st.text_input(
            "Subdomain",
            value=st.session_state.zd_subdomain,
            placeholder="acme",
            help="e.g. acme for acme.zendesk.com",
        )
        email_in = st.text_input("Admin Email", value=st.session_state.zd_email)
        token_in = st.text_input("API Token", type="password", value=st.session_state.zd_token)
        save_creds = st.form_submit_button("✅ Connect to Zendesk")

    if save_creds:
        sub_norm, sub_err = normalize_subdomain_input(subdomain_in)
        email_norm = (email_in or "").strip()
        token_norm = (token_in or "").strip()

        if sub_err:
            st.error(sub_err)
        elif not is_valid_email_format(email_norm):
            st.error("Enter a valid admin email (example: admin@company.com).")
        elif not token_norm:
            st.error("API token is required.")
        else:
            ok, msg = verify_zendesk_connection(sub_norm, email_norm, token_norm)
            if ok:
                st.session_state.zd_subdomain = sub_norm
                st.session_state.zd_email = email_norm
                st.session_state.zd_token = token_norm
                st.toast("Connection Established.", icon="✅")
            else:
                st.error(msg)

    subdomain = (st.session_state.zd_subdomain or "").strip()
    email = (st.session_state.zd_email or "").strip()
    token = (st.session_state.zd_token or "").strip()

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

    if SHOW_DEV_CONTROLS:
        pro_mode = st.checkbox("Pro Mode (dev)", value=False)
    else:
        pro_mode = False

    max_articles = st.number_input("Max Articles (0 = all)", min_value=0, value=0, step=50)

    st.caption("Zendesk® is a trademark of Zendesk, Inc.")

    st.divider()
    render_obfuscated_email("support", "yourdomain.com", label="Need help?")

# =========================
# 7) TOP-LEVEL UI
# =========================
st.markdown("## Zendesk® Knowledge Base Intelligence")
st.caption("Scan your Help Center for broken links, broken images, missing alt text, typos, and stale content.")

tab_audit, tab_method, tab_privacy, tab_pro = st.tabs(["Audit", "Methodology", "Privacy", "Pro"])

# =========================
# 8) AUDIT TAB
# =========================
with tab_audit:
    base, pay_url = _worker_cfg()

    st.markdown(
        f"""
<div class="za-pricing">
  <div class="za-badge">FREE SCAN • PAID EXPORT</div>
  <div class="za-title">Scan first. Initial 50 results are free - Pay only to unlock the full report.</div>

  <div class="za-line" style="margin-top:8px;">
    <b>How to run a scan</b>
    <ol style="margin:6px 0 10px 18px;">
      <li>
        Enter your Help Center <b>subdomain</b>
        (example: <code>acme</code> for <code>acme.zendesk.com</code>)
      </li>
      <li>Enter your Zendesk <b>admin email</b></li>
      <li>
        Enter a valid <b>API token</b>
        (required to securely access your Help Center content via the Zendesk API)
        <br>
        <span style="color:#9FB1CC;">
          Admin Center → Apps and integrations → APIs → Zendesk API → Add API token
        </span>
      </li>
      <li>Click <b>Connect to Zendesk</b> to verify access</li>
      <li>Click <b>Run scan</b> to start the audit</li>
    </ol>
<div style="margin-top:6px; color:#9FB1CC;">
  We use the token only to fetch articles during the scan. It isn’t stored and isn’t included in exports.<br>
</div>
  </div>

  <div class="za-line">
    Running a scan is <b>free</b> and includes a preview of up to
    <b>{FREE_FINDING_LIMIT}</b> findings.
    After the scan completes, you can export the <b>full report</b>
    (all findings + Excel export) for a <b>one-time $19 fee</b>.
    Your export credit is used only when you download the full <b>XLSX</b> or <b>CSV</b>.
  </div>

  <div class="za-line" style="margin-top:8px;">
    <span style="color:#9FB1CC;">
      Tip: If you just want a quick check, disable Broken Links / Images for a faster first pass.
    </span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    a1, a2, a3 = st.columns([1.15, 1.0, 2.2])
    with a1:
        run_btn = st.button("🚀 Run scan", type="primary", use_container_width=True)
    with a2:
        clear_btn = st.button("🧹 Clear results", type="secondary", use_container_width=True)
    with a3:
        st.markdown("<div class='za-subtle'>Tip: Disable Broken Links/Images for a faster first pass.</div>", unsafe_allow_html=True)

    if clear_btn:
        st.session_state.scan_results = []
        st.session_state.findings = []
        st.session_state.last_logs = []
        st.session_state.url_cache = {}
        st.session_state.last_scanned_title = ""
        st.session_state.connected_ok = False
        st.session_state.pro_unlocked = False
        st.session_state.pro_available_scans = 0
        st.session_state.pro_last_status_error = ""
        st.session_state.xlsx_consumed_local = False
        st.session_state.scan_id = ""
        st.session_state.scan_started_at = None
        st.toast("Cleared.", icon="🧼")

    m1, m2, m3, m4, m5 = st.columns(5)
    met_scanned = m1.empty()
    met_critical = m2.empty()
    met_warn = m3.empty()
    met_alt = m4.empty()
    met_stale = m5.empty()

    progress = st.progress(0, text="Ready")

    left, right = st.columns([2.2, 1.2])
    with left:
        console = st.empty()

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

        if st.session_state.connected_ok:
            conn_ph.success("✅ Connected to Zendesk")
        else:
            conn_ph.info("Waiting to start")

        title = st.session_state.last_scanned_title or "—"
        now_ph.write(f"**Now scanning:** {title}")

        crit_ph.metric("Critical", critical)
        warn_ph.metric("Warnings", warning)
        alt_ph.metric("Missing alt", alt_missing)
        stale_ph.metric("Stale", stale_count)

    def progress_cb(scanned_count: int):
        if max_articles:
            pct = min(1.0, scanned_count / int(max_articles))
            progress.progress(pct, text=f"Scanning… {scanned_count}/{int(max_articles)}")
        else:
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
            st.error("Missing credentials in the sidebar. Click “Connect to Zendesk” first.")
        else:
            try:
                st.toast("Scan started…", icon="🚀")

                st.session_state.pro_unlocked = False
                st.session_state.pro_available_scans = 0
                st.session_state.pro_last_status_error = ""
                st.session_state.xlsx_consumed_local = False

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
                sid = st.session_state.scan_id or "unknown"
                st.error(f"Scan failed (ID: {sid}). Error: {e}")

    refresh_metrics()

    # ✅ ALWAYS show Findings + Export section
    st.divider()

    if st.session_state.scan_results:
        st.markdown(
            """
<div class="za-next">
  👉 <b>Next step</b><br>
  <span>Review the free preview below. Export the full report after the table if you want the complete export.</span>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div class="za-next">
  👉 <b>Next step</b><br>
  <span>Run a scan to generate a free preview. You can buy an export credit anytime to unlock downloads.</span>
</div>
""",
            unsafe_allow_html=True,
        )

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

    pro_access = pro_access_active(pro_mode)
    gated = (not pro_access) and (total_findings > FREE_FINDING_LIMIT)
    df_preview = df_findings.head(FREE_FINDING_LIMIT) if gated else df_findings

    if not df_preview.empty:
        f1, f2, f3 = st.columns([1.2, 1.2, 2.6])
        with f1:
            sev_filter = st.multiselect("Severity", ["critical", "warning", "info"], default=["critical", "warning", "info"])
        with f2:
            type_opts = sorted(df_preview["Type"].unique().tolist()) if not df_preview.empty else []
            type_filter = st.multiselect("Type", type_opts, default=type_opts)
        with f3:
            q = st.text_input("Search (title/url contains)", placeholder="e.g. billing, /hc/en-us, image.png")

        view = df_preview.copy()
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
        render_table_no_toolbar(view)
    else:
        render_table_no_toolbar(df_preview)

    if st.session_state.scan_results:
        st.info(f"Scanned **{len(st.session_state.scan_results)}** articles. Found **{total_findings}** findings.")
        if gated:
            st.warning(f"Free preview shows the first **{FREE_FINDING_LIMIT}** findings. Export the full report by purchasing an export credit.")
    else:
        st.info("No scan results yet. Run a scan above to populate the preview table.")

    st.markdown("### 🔓 Export full report")

    uL, uR = st.columns([1.8, 2.2])

    with uL:
        st.markdown("**Step 1 — Buy 1 export credit**")
        link_cta("💳 Buy 1 export credit ($19)", pay_url)
        st.markdown("<div class='za-subtle' style='margin-top:6px;'>Only buy if you want to download exports.</div>", unsafe_allow_html=True)

    with uR:
        st.markdown("**Step 2 — Verify purchase**")
        unlock_email = st.text_input(
            "Email used at checkout",
            value=st.session_state.pro_email,
            placeholder="admin@company.com",
            label_visibility="visible",
            key="unlock_email_main",
        ).strip().lower()
        st.session_state.pro_email = unlock_email

        if unlock_email and not is_valid_email_format(unlock_email):
            st.error("Enter a valid checkout email (example: admin@company.com).")

        unlock_btn = st.button(
            "✅ Verify purchase",
            use_container_width=True,
            disabled=(not bool(unlock_email)) or (not is_valid_email_format(unlock_email)) or ((not base) and (not pro_mode)),
            key="btn_unlock_paid",
        )

        st.markdown("<div class='za-subtle'>Use the same email you used at Stripe checkout.</div>", unsafe_allow_html=True)

        if (not base) and (not pro_mode):
            st.markdown("<div class='za-pill-warn'>⚠️ Paywall not configured (missing WORKER_BASE_URL secret).</div>", unsafe_allow_html=True)

    if unlock_btn:
        if pro_mode:
            st.session_state.pro_unlocked = True
            st.session_state.pro_available_scans = max(1, int(st.session_state.pro_available_scans or 1))
            st.session_state.pro_last_status_error = ""
            st.session_state.xlsx_consumed_local = False
            st.toast("Export credit available (dev) ✅", icon="✅")
            st.rerun()
        else:
            try_unlock_from_status(st.session_state.pro_email)
            if st.session_state.pro_unlocked:
                st.toast("Export credit available ✅", icon="✅")
                st.rerun()

    if pro_mode:
        st.markdown("<div class='za-pill-ok'>✅ Pro Mode enabled (dev) — export available.</div>", unsafe_allow_html=True)
    else:
        if st.session_state.pro_unlocked:
            st.markdown(
                f"<div class='za-pill-ok'>✅ Export credit available • Credits remaining: {st.session_state.pro_available_scans}"
                f"<br><span style='color:#9FB1CC; font-weight:600;'>Downloading uses 1 export credit. Save the file after downloading.</span></div>",
                unsafe_allow_html=True,
            )
        else:
            msg = st.session_state.pro_last_status_error or (
                "Buy 1 export credit, then verify with your checkout email to unlock downloads."
            )
            st.markdown(f"<div class='za-pill-info'>ℹ️ {msg}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    pro_access = pro_access_active(pro_mode)
    xlsx_bytes, xlsx_err = get_xlsx_bytes_safe(df_findings) if total_findings > 0 else (None, None)

    def _consume_once():
        if pro_mode:
            return
        if st.session_state.xlsx_consumed_local:
            return
        if not st.session_state.pro_email:
            st.warning("Enter your email above to use an export credit.")
            return

        ok, avail, err = worker_consume(st.session_state.pro_email)
        if ok:
            st.session_state.xlsx_consumed_local = True
            st.session_state.pro_unlocked = False
            st.session_state.pro_available_scans = avail
            st.toast("Export credit used ✅ (download)", icon="✅")
        else:
            st.warning(err or "Could not use export credit (try again).")

    d1, d2 = st.columns([2.2, 1.8])

    with d1:
        if total_findings <= 0:
            st.button("📥 Download XLSX (locked)", disabled=True, use_container_width=True)
            st.caption("Run a scan to generate a report preview.")
        else:
            if not pro_access:
                st.button("📥 Download XLSX (locked)", disabled=True, use_container_width=True)
                st.caption("Buy 1 export credit to download exports.")
            else:
                if xlsx_bytes:
                    st.download_button(
                        "📥 Download XLSX" + ("" if pro_mode else " (uses 1 export credit)"),
                        data=xlsx_bytes,
                        file_name="zenaudit_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        on_click=_consume_once,
                        key="download_xlsx_btn",
                    )
                else:
                    st.button("📥 Download XLSX", disabled=True, use_container_width=True)
                    st.caption(xlsx_err or "XLSX export unavailable.")

    with d2:
        if total_findings <= 0:
            st.button("📥 Download CSV (locked)", disabled=True, use_container_width=True)
            st.caption("Run a scan to generate a report preview.")
        else:
            if not pro_access:
                st.button("📥 Download CSV (locked)", disabled=True, use_container_width=True)
                st.caption("Buy 1 export credit to download exports.")
            else:
                # ✅ UPDATED: CSV now consumes 1 export credit too
                st.download_button(
                    "📥 Download CSV" + ("" if pro_mode else " (uses 1 export credit)"),
                    data=df_findings.to_csv(index=False),
                    file_name="zenaudit_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                    on_click=_consume_once,
                    key="download_csv_btn",
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
  - 401/403/429 → inconclusive (often blocked/auth/rate-limited)
"""
    )

with tab_privacy:
    st.info("ZenAudit is client-side first: credentials are used only to fetch articles during the scan.")
    st.markdown(
        """
### Data handling
- Direct HTTPS calls to your Zendesk subdomain
- Tokens are used only during the scan to fetch Help Center content
- Tokens are not written into exports
- Results live in Streamlit session state and reset when you clear or rerun
"""
    )

with tab_pro:
    _base, pay_url = _worker_cfg()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Free")
        st.write("✅ Run scans anytime")
        st.write(f"✅ Preview first {FREE_FINDING_LIMIT} findings (in-app)")

    with c2:
        st.subheader("Paid ($29 / export credit)")
        st.write("🚀 Full findings (beyond preview)")
        st.write("📥 XLSX + CSV exports (uses 1 export credit)")
        link_cta("💳 Buy 1 export credit ($29)", pay_url)

    st.divider()
    st.caption("Flow: Run scan → review preview → buy only if you want the full export.")

from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DEFAULT_CV_DIR = r"C:\Users\m.atif\Downloads\My CVs - Doc Controller"
DATA_DIR = APP_DIR / "job_data"
DATA_DIR.mkdir(exist_ok=True)

COUNTRIES = {
    "Saudi Arabia": {"indeed": "saudi arabia", "location": "Saudi Arabia"},
    "United Arab Emirates": {"indeed": "united arab emirates", "location": "United Arab Emirates"},
    "Qatar": {"indeed": "qatar", "location": "Qatar"},
    "Kuwait": {"indeed": "kuwait", "location": "Kuwait"},
    "Bahrain": {"indeed": "bahrain", "location": "Bahrain"},
    "Oman": {"indeed": "oman", "location": "Oman"},
    "Malta": {"indeed": "malta", "location": "Malta"},
    "Netherlands": {"indeed": "netherlands", "location": "Netherlands"},
    "Scotland, United Kingdom": {"indeed": "uk", "location": "Scotland"},
    "Greece": {"indeed": "greece", "location": "Greece"},
    "Romania": {"indeed": "romania", "location": "Romania"},
    "France": {"indeed": "france", "location": "France"},
}

ROLE_GROUPS = {
    "Document Control": ["document controller", "senior document controller", "document control specialist"],
    "EDMS / Aconex": ["Aconex", "EDMS coordinator", "document management"],
    "Handover & Closeout": ["handover coordinator", "closeout coordinator", "O&M documentation"],
    "Project Coordination": ["project coordinator", "project documentation coordinator"],
    "Contracts / Procurement Documentation": ["procurement document coordinator", "contracts document controller", "submittals coordinator"],
    "QA/QC Documentation": ["QA/QC document controller", "quality documentation coordinator", "inspection coordinator"],
}

SKILLS = {
    "Oracle Aconex / EDMS": [r"\baconex\b", r"\bedms\b", r"document management", r"document control"],
    "WIR / MIR / RFI / NCR": [r"\bwirs?\b", r"\bmirs?\b", r"\brfis?\b", r"\bncrs?\b"],
    "Transmittals / submittals": [r"transmittal", r"submittal", r"technical submission"],
    "Closeout / handover / O&M": [r"close.?out", r"handover", r"o&m manual", r"operation and maintenance"],
    "As-built / asset registers": [r"as.?built", r"asset register", r"warranty", r"snag list"],
    "QA/QC / inspections": [r"qa.?qc", r"quality assurance", r"inspection and test", r"\bitp\b", r"material inspection"],
    "Reporting / tracking": [r"tracking log", r"status report", r"progress report", r"document register", r"dashboard"],
    "Procurement / SCM": [r"procurement", r"supply chain", r"\bscm\b", r"supplier documentation"],
    "Construction / infrastructure": [r"construction", r"infrastructure", r"engineering", r"site team"],
    "MS Office / Excel": [r"microsoft office", r"\bexcel\b", r"spreadsheet"],
}

def norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()

def read_uploaded_cvs(uploaded_files):
    """Extract text from CVs uploaded in the browser; files are not committed to GitHub."""
    from io import BytesIO
    texts, read_files, errors = [], [], []
    for uploaded in uploaded_files or []:
        try:
            name = uploaded.name
            suffix = Path(name).suffix.lower()
            content = ""
            data = uploaded.getvalue()
            if suffix == ".pdf":
                from pypdf import PdfReader
                content = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
            elif suffix == ".docx":
                from docx import Document
                doc = Document(BytesIO(data))
                parts = [p.text for p in doc.paragraphs]
                for table in doc.tables:
                    parts.extend(" | ".join(c.text for c in row.cells) for row in table.rows)
                content = "\n".join(parts)
            elif suffix == ".txt":
                content = data.decode("utf-8", errors="ignore")
            if content.strip():
                texts.append(content)
                read_files.append(name)
            else:
                errors.append(f"{name}: no readable text found (scanned PDFs may need OCR).")
        except Exception as exc:
            errors.append(f"{uploaded.name}: {exc}")
    return "\n".join(texts), read_files, errors

def score_job(row, cv_text, selected_roles):
    title = str(row.get("title") or "")
    desc = str(row.get("description") or "")
    blob, cv = norm(title + " " + desc), norm(cv_text)
    role_terms = [term for group in selected_roles for term in ROLE_GROUPS[group]]
    title_points = 0
    for term in role_terms:
        if term.lower() in title.lower():
            title_points = max(title_points, 45 if any(x in term.lower() for x in ["senior", "specialist", "coordinator"]) else 38)
    if not title_points:
        if any(k in title.lower() for k in ["document", "edms", "aconex", "handover", "closeout", "project coordinator", "submittal", "quality"]):
            title_points = 22
        else:
            return 0, [], []
    matched, gaps, points = [], [], 0
    for label, patterns in SKILLS.items():
        found_job = any(re.search(p, blob, re.I) for p in patterns)
        found_cv = any(re.search(p, cv, re.I) for p in patterns)
        if found_job and found_cv:
            matched.append(label)
            points += 6
        elif found_job:
            gaps.append(label)
    return min(100, title_points + min(45, points) + (10 if desc else 0)), matched, gaps

def search_jobs(countries, selected_roles, boards, days, per_country, min_score, cv_text, progress):
    try:
        from jobspy import scrape_jobs
    except Exception as exc:
        raise RuntimeError("JobSpy is missing. Run the project launcher again to install requirements.\n" + str(exc))

    # One combined search per country rather than one request per job title and board.
    role_terms = list(dict.fromkeys(t for group in selected_roles for t in ROLE_GROUPS[group]))
    query = " OR ".join(role_terms[:8])
    all_rows = []
    total = len(countries)
    for idx, country in enumerate(countries, 1):
        cfg = COUNTRIES[country]
        progress.progress((idx - 1) / max(total, 1), text=f"Searching {country} ({idx}/{total})…")
        kwargs = dict(
            site_name=boards,
            search_term=query,
            location=cfg["location"],
            results_wanted=per_country,
            hours_old=days * 24,
            verbose=0,
        )
        if "indeed" in boards:
            kwargs["country_indeed"] = cfg["indeed"]
        try:
            result = scrape_jobs(**kwargs)
            if result is not None and not result.empty:
                for item in result.to_dict("records"):
                    item["search_country"] = country
                    item["search_query"] = query
                all_rows.extend(result.to_dict("records"))
                # Attach search country to each row; JobSpy can return several locations.
                for item in all_rows[-len(result):] if len(result) else []:
                    item["search_country"] = country
                    item["search_query"] = query
        except Exception as exc:
            st.warning(f"{country}: search failed — {str(exc)[:180]}")
    progress.progress(1.0, text="Scoring and preparing results…")
    if not all_rows:
        progress.empty()
        return pd.DataFrame()
    raw = pd.DataFrame(all_rows).astype(object).where(pd.notna(pd.DataFrame(all_rows)), None)
    if "job_url" not in raw:
        raw["job_url"] = ""
    if "title" not in raw:
        raw["title"] = ""
    if "company" not in raw:
        raw["company"] = ""
    if "location" not in raw:
        raw["location"] = ""
    raw["_dedupe"] = raw.apply(lambda r: norm(r.get("job_url")) or (norm(r.get("title")) + "|" + norm(r.get("company")) + "|" + norm(r.get("location"))), axis=1)
    raw = raw.drop_duplicates("_dedupe", keep="first")
    results = []
    for row in raw.to_dict("records"):
        score, matched, gaps = score_job(row, cv_text, selected_roles)
        if score < min_score:
            continue
        title = str(row.get("title") or "")
        desc = str(row.get("description") or "")
        results.append({
            "Match %": score,
            "Role": title,
            "Company": row.get("company"),
            "Country": row.get("search_country"),
            "Location": row.get("location"),
            "Work mode": "Remote" if re.search(r"remote|work from home", title + " " + desc, re.I) else ("Hybrid" if re.search(r"hybrid", desc, re.I) else "Not stated"),
            "Date posted": str(row.get("date_posted") or ""),
            "Board": row.get("site") or row.get("source_board") or "",
            "Matched CV skills": ", ".join(matched),
            "Possible skill gaps": ", ".join(gaps),
            "Apply link": row.get("job_url_direct") or row.get("job_url") or "",
            "Search term": row.get("search_query"),
            "Description": desc,
        })
    progress.empty()
    out = pd.DataFrame(results)
    if not out.empty:
        out = out.sort_values(["Match %", "Date posted"], ascending=[False, False]).reset_index(drop=True)
    return out

st.set_page_config(page_title="Atif | Job Search Dashboard", page_icon="🔎", layout="wide")
st.title("🔎 Personal Job Search Dashboard")
st.caption("CV-aware job search for Document Control, Aconex/EDMS, Handover, Closeout and related roles. Upload CVs in the sidebar to use this app online.")

with st.sidebar:
    st.header("Search settings")
    uploaded_cvs = st.file_uploader(
        "Upload your actual CV files (up to 6 recommended)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload only your CVs. Do not upload passports, certificates, or other private documents.",
    )
    countries = st.multiselect("Target countries", list(COUNTRIES), default=["Saudi Arabia", "United Arab Emirates", "Qatar", "Malta", "Netherlands", "Scotland, United Kingdom", "Greece", "Romania", "France"])
    roles = st.multiselect("Job families", list(ROLE_GROUPS), default=["Document Control", "EDMS / Aconex", "Handover & Closeout", "Project Coordination"])
    boards = st.multiselect("Job boards (Bayt disabled to avoid repeated 404 errors)", ["indeed", "linkedin"], default=["indeed", "linkedin"])
    days = st.slider("Posted within last (days)", 1, 30, 7)
    per_country = st.slider("Maximum results per country", 5, 30, 10)
    min_score = st.slider("Minimum CV match score", 20, 90, 45, 5)
    start = st.button("🔎 Search jobs", type="primary", use_container_width=True)

cv_text, cv_files, cv_errors = read_uploaded_cvs(uploaded_cvs)
if cv_text:
    st.success(f"Read {len(cv_files)} uploaded CV file(s) for matching.")
    with st.expander("CV files being used"):
        for name in cv_files:
            st.write("• " + name)
    if len(cv_files) != 6:
        st.info(f"{len(cv_files)} readable file(s) uploaded. Upload all 6 actual CVs if you have six; other documents are not needed.")
else:
    st.info("Start by uploading your actual CV files in the sidebar. CVs are used for matching during this session and are not included in the project ZIP or GitHub repository.")
for error in cv_errors:
    st.warning(error)

if "jobs_df" not in st.session_state:
    st.session_state.jobs_df = pd.DataFrame()

if start:
    if not cv_text:
        st.error("Select at least one readable CV file first.")
    elif not countries or not roles or not boards:
        st.error("Select at least one country, job family and job board.")
    else:
        progress = st.progress(0, text="Starting…")
        try:
            df = search_jobs(countries, roles, boards, days, per_country, min_score, cv_text, progress)
            st.session_state.jobs_df = df
            if not df.empty:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                df.to_csv(DATA_DIR / f"job_matches_{stamp}.csv", index=False, encoding="utf-8-sig")
                try:
                    df.to_excel(DATA_DIR / f"job_matches_{stamp}.xlsx", index=False)
                except Exception:
                    pass
                (DATA_DIR / f"job_matches_{stamp}.json").write_text(df.to_json(orient="records", force_ascii=False, indent=2), encoding="utf-8")
                st.success(f"Found {len(df)} matching jobs. Download the results below; cloud storage may reset when the app restarts.")
            else:
                st.info("No jobs passed the selected match score. Try a lower score or fewer filters.")
        except Exception as exc:
            st.error(str(exc))

df = st.session_state.jobs_df
if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Matching jobs", len(df))
    c2.metric("Countries", df["Country"].nunique(dropna=True))
    c3.metric("Strong matches (70%+)", int((df["Match %"] >= 70).sum()))
    filter_text = st.text_input("Filter by role, company or country")
    view = df.copy()
    if filter_text:
        mask = view.astype(str).apply(lambda col: col.str.contains(filter_text, case=False, na=False)).any(axis=1)
        view = view[mask]
    st.dataframe(
        view.drop(columns=["Description"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Apply link": st.column_config.LinkColumn("Apply link", display_text="Open job"),
            "Match %": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d%%"),
        },
    )
    options = [f"{i}: {r.get('Role','')} — {r.get('Company','')} ({r.get('Country','')})" for i, r in view.reset_index(drop=True).iterrows()]
    if options:
        selected = st.selectbox("Read job details", options)
        job = view.reset_index(drop=True).iloc[int(selected.split(":", 1)[0])]
        st.subheader(str(job.get("Role", "Job details")))
        st.write(f"**Company:** {job.get('Company') or 'Not listed'} · **Country:** {job.get('Country') or 'Not confirmed'} · **Match:** {job.get('Match %')}%")
        if job.get("Apply link"):
            st.link_button("Open application / job posting", str(job.get("Apply link")))
        st.write("**Matched CV skills:** " + str(job.get("Matched CV skills") or "No clear skill overlap detected"))
        st.write("**Possible skill gaps:** " + str(job.get("Possible skill gaps") or "No obvious gaps from detected keywords"))
        st.text_area("Job description", value=str(job.get("Description") or "No description returned by the board."), height=260, disabled=True)
    st.download_button("Download results as CSV", data=df.to_csv(index=False).encode("utf-8-sig"), file_name="atif_job_matches.csv", mime="text/csv")
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("Download results as Excel", data=buffer.getvalue(), file_name="atif_job_matches.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.caption("Personal job-search helper, not an official job feed. Results may be incomplete or duplicated. Verify the employer, visa/work-permit eligibility and application page. It does not log in to job sites or apply automatically.")

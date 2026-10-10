from pathlib import Path
from datetime import datetime, date
from io import BytesIO
import re, time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Atif Job Finder Pro", page_icon="🎯", layout="wide")
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "job_data"
DATA_DIR.mkdir(exist_ok=True)

# Indeed country names are restricted to the countries supported by JobSpy.
COUNTRIES = {
    "Saudi Arabia": {"indeed": "saudi arabia", "location": "Saudi Arabia", "sites": [("Bayt", "https://www.bayt.com/en/saudi-arabia/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/saudi-arabia/jobs"), ("Jadarat", "https://jadarat.sa/")]},
    "United Arab Emirates": {"indeed": "united arab emirates", "location": "United Arab Emirates", "sites": [("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/uae/jobs"), ("Foundit Gulf", "https://www.founditgulf.com/"), ("UAE Government Careers", "https://u.ae/en/information-and-services/jobs/searching-for-a-job")]},
    "Qatar": {"indeed": "qatar", "location": "Qatar", "sites": [("Bayt", "https://www.bayt.com/en/qatar/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/qatar/jobs")]},
    "Kuwait": {"indeed": "kuwait", "location": "Kuwait", "sites": [("Bayt", "https://www.bayt.com/en/kuwait/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/kuwait/jobs")]},
    "Bahrain": {"indeed": "bahrain", "location": "Bahrain", "sites": [("Bayt", "https://www.bayt.com/en/bahrain/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/bahrain/jobs")]},
    "Oman": {"indeed": "oman", "location": "Oman", "sites": [("Bayt", "https://www.bayt.com/en/oman/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/oman/jobs")]},
    "Germany": {"indeed": "germany", "location": "Germany", "sites": [("StepStone", "https://www.stepstone.de/"), ("XING Jobs", "https://www.xing.com/jobs"), ("Make it in Germany", "https://www.make-it-in-germany.com/en/working-in-germany/job-listings")]},
    "Netherlands": {"indeed": "netherlands", "location": "Netherlands", "sites": [("Nationale Vacaturebank", "https://www.nationalevacaturebank.nl/"), ("Werk.nl", "https://www.werk.nl/werkzoekenden/vacatures/"), ("EURES", "https://eures.europa.eu/")]},
    "Ireland": {"indeed": "ireland", "location": "Ireland", "sites": [("IrishJobs", "https://www.irishjobs.ie/"), ("Jobs.ie", "https://www.jobs.ie/"), ("JobsIreland", "https://jobsireland.ie/")]},
    "United Kingdom - Scotland": {"indeed": "uk", "location": "Scotland, United Kingdom", "sites": [("Reed", "https://www.reed.co.uk/"), ("Totaljobs", "https://www.totaljobs.com/"), ("Find a Job", "https://findajob.dwp.gov.uk/")]},
    "Malta": {"indeed": None, "location": "Malta", "sites": [("JobsinMalta", "https://jobsinmalta.com/"), ("Keepmeposted", "https://keepmeposted.com.mt/"), ("JobsPlus", "https://jobsplus.gov.mt/")]},
    "France": {"indeed": "france", "location": "France", "sites": [("France Travail", "https://www.francetravail.fr/"), ("APEC", "https://www.apec.fr/"), ("Welcome to the Jungle", "https://www.welcometothejungle.com/")]},
    "Belgium": {"indeed": "belgium", "location": "Belgium", "sites": [("VDAB", "https://www.vdab.be/vindeenjob"), ("Le Forem", "https://www.leforem.be/"), ("Actiris", "https://www.actiris.brussels/")]},
    "Austria": {"indeed": "austria", "location": "Austria", "sites": [("AMS eJob-Room", "https://www.ams.at/arbeitsuchende"), ("karriere.at", "https://www.karriere.at/")]},
    "Poland": {"indeed": "poland", "location": "Poland", "sites": [("Pracuj.pl", "https://www.pracuj.pl/"), ("Praca.gov.pl", "https://oferty.praca.gov.pl/portal/"), ("EURES", "https://eures.europa.eu/")]},
    "Czechia": {"indeed": "czech republic", "location": "Czechia", "sites": [("Jobs.cz", "https://www.jobs.cz/"), ("Prace.cz", "https://www.prace.cz/"), ("EURES", "https://eures.europa.eu/")]},
    "Romania": {"indeed": None, "location": "Romania", "sites": [("eJobs", "https://www.ejobs.ro/"), ("BestJobs", "https://www.bestjobs.eu/"), ("ANOFM", "https://www.anofm.ro/")]},
    "Greece": {"indeed": "greece", "location": "Greece", "sites": [(" kariera.gr", "https://www.kariera.gr/"), ("Skywalker", "https://www.skywalker.gr/"), ("DYPA", "https://www.dypa.gov.gr/")]},
    "Italy": {"indeed": "italy", "location": "Italy", "sites": [("InfoJobs", "https://www.infojobs.it/"), ("Cliclavoro", "https://www.cliclavoro.gov.it/"), ("EURES", "https://eures.europa.eu/")]},
    "Spain": {"indeed": "spain", "location": "Spain", "sites": [("InfoJobs", "https://www.infojobs.net/"), ("Empléate", "https://empleate.gob.es/"), ("Tecnoempleo", "https://www.tecnoempleo.com/")]},
    "Portugal": {"indeed": "portugal", "location": "Portugal", "sites": [("Net-Empregos", "https://www.net-empregos.com/"), ("IEFP", "https://iefponline.iefp.pt/"), ("EURES", "https://eures.europa.eu/")]},
    "Hungary": {"indeed": "hungary", "location": "Hungary", "sites": [("Profession.hu", "https://www.profession.hu/"), ("EURES", "https://eures.europa.eu/")]},
    "Slovakia": {"indeed": None, "location": "Slovakia", "sites": [("Profesia.sk", "https://www.profesia.sk/"), ("EURES", "https://eures.europa.eu/")]},
    "Bulgaria": {"indeed": None, "location": "Bulgaria", "sites": [("Jobs.bg", "https://www.jobs.bg/"), ("EURES", "https://eures.europa.eu/")]},
    "Croatia": {"indeed": None, "location": "Croatia", "sites": [("MojPosao", "https://www.moj-posao.net/"), ("EURES", "https://eures.europa.eu/")]},
    "Estonia": {"indeed": None, "location": "Estonia", "sites": [("CVKeskus", "https://www.cvkeskus.ee/"), ("Töötukassa", "https://www.tootukassa.ee/")]},
    "Norway": {"indeed": "norway", "location": "Norway", "sites": [("NAV", "https://arbeidsplassen.nav.no/"), ("FINN Jobb", "https://www.finn.no/job/"), ("EURES", "https://eures.europa.eu/")]},
    "Denmark": {"indeed": "denmark", "location": "Denmark", "sites": [("Jobnet", "https://job.jobnet.dk/"), ("Workindenmark", "https://www.workindenmark.dk/")]},
    "Sweden": {"indeed": "sweden", "location": "Sweden", "sites": [("Arbetsförmedlingen", "https://arbetsformedlingen.se/platsbanken/"), ("Jobbsafari", "https://www.jobbsafari.se/")]},
    "Finland": {"indeed": "finland", "location": "Finland", "sites": [("Job Market Finland", "https://tyomarkkinatori.fi/en"), ("Duunitori", "https://duunitori.fi/")]},
    "Switzerland": {"indeed": "switzerland", "location": "Switzerland", "sites": [("jobs.ch", "https://www.jobs.ch/"), ("Job-Room", "https://www.job-room.ch/")]},
    "Luxembourg": {"indeed": "luxembourg", "location": "Luxembourg", "sites": [("ADEM", "https://adem.public.lu/"), ("Moovijob", "https://www.moovijob.com/")]},
    "Canada": {"indeed": "canada", "location": "Canada", "sites": [("Job Bank", "https://www.jobbank.gc.ca/"), ("Workopolis", "https://www.workopolis.com/")]},
    "Australia": {"indeed": "australia", "location": "Australia", "sites": [("SEEK", "https://www.seek.com.au/"), ("Workforce Australia", "https://www.workforceaustralia.gov.au/")]},
}

ROLE_TITLES = [
    "Document Controller", "Senior Document Controller", "Lead Document Controller", "Document Control Specialist",
    "Document Control Coordinator", "EDMS Coordinator", "Aconex Administrator", "Aconex Coordinator",
    "Document Management Specialist", "Project Document Controller", "Technical Document Controller",
    "Construction Document Controller", "Engineering Document Controller", "Project Coordinator",
    "Project Documentation Coordinator", "Information Management Coordinator", "Records Management Coordinator",
    "Handover Coordinator", "Turnover Coordinator", "Closeout Coordinator", "O&M Documentation Coordinator",
    "Completions Coordinator", "Asset Information Coordinator", "QA/QC Document Controller",
    "Quality Documentation Coordinator", "Inspection Coordinator", "Submittals Coordinator",
    "Transmittal Coordinator", "Procurement Document Controller", "Contracts Document Controller",
    "Document Control Manager", "Project Administrator", "Technical Clerk", "Site Administrator",
    "Document Control Engineer", "Information Controller", "Records Controller", "Project Support Coordinator",
]
ROLE_KEYWORDS = {
    "Document Controller": ["document controller", "document control"],
    "Senior Document Controller": ["senior document controller", "senior document control"],
    "Lead Document Controller": ["lead document controller", "lead document control"],
    "Document Control Specialist": ["document control specialist"],
    "Document Control Coordinator": ["document control coordinator"],
    "EDMS Coordinator": ["EDMS coordinator", "EDMS specialist"],
    "Aconex Administrator": ["Aconex administrator", "Oracle Aconex"],
    "Aconex Coordinator": ["Aconex coordinator"],
    "Document Management Specialist": ["document management specialist"],
    "Project Document Controller": ["project document controller"],
    "Technical Document Controller": ["technical document controller"],
    "Construction Document Controller": ["construction document controller"],
    "Engineering Document Controller": ["engineering document controller"],
    "Project Coordinator": ["project coordinator"],
    "Project Documentation Coordinator": ["project documentation coordinator"],
    "Information Management Coordinator": ["information management coordinator"],
    "Records Management Coordinator": ["records management coordinator"],
    "Handover Coordinator": ["handover coordinator", "handover documentation"],
    "Turnover Coordinator": ["turnover coordinator"],
    "Closeout Coordinator": ["closeout coordinator", "close-out coordinator"],
    "O&M Documentation Coordinator": ["O&M documentation", "operation and maintenance documentation"],
    "Completions Coordinator": ["completions coordinator"],
    "Asset Information Coordinator": ["asset information coordinator", "asset register"],
    "QA/QC Document Controller": ["QA/QC document controller", "quality document controller"],
    "Quality Documentation Coordinator": ["quality documentation coordinator"],
    "Inspection Coordinator": ["inspection coordinator", "WIR MIR RFI"],
    "Submittals Coordinator": ["submittals coordinator", "technical submittals"],
    "Transmittal Coordinator": ["transmittal coordinator"],
    "Procurement Document Controller": ["procurement document controller", "procurement documentation"],
    "Contracts Document Controller": ["contracts document controller"],
    "Document Control Manager": ["document control manager"],
    "Project Administrator": ["project administrator"],
    "Technical Clerk": ["technical clerk"],
    "Site Administrator": ["site administrator"],
    "Document Control Engineer": ["document control engineer"],
    "Information Controller": ["information controller"],
    "Records Controller": ["records controller"],
    "Project Support Coordinator": ["project support coordinator"],
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
STATUSES = ["To Apply", "Saved", "Applied", "Follow-up", "Interview", "Rejected", "Closed"]
TRACK_COLUMNS = ["Job ID", "Status", "Date Applied", "Follow-up Date", "Priority", "Notes"]

def norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()

def read_uploaded_cvs(uploaded_files):
    texts, names, errors = [], [], []
    for uploaded in uploaded_files or []:
        try:
            data, name = uploaded.getvalue(), uploaded.name
            suffix, content = Path(name).suffix.lower(), ""
            if suffix == ".pdf":
                from pypdf import PdfReader
                content = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(data)).pages)
            elif suffix == ".docx":
                from docx import Document
                doc = Document(BytesIO(data))
                parts = [p.text for p in doc.paragraphs]
                for table in doc.tables:
                    parts.extend(" | ".join(c.text for c in row.cells) for row in table.rows)
                content = "\n".join(parts)
            elif suffix == ".txt": content = data.decode("utf-8", errors="ignore")
            if content.strip(): texts.append(content); names.append(name)
            else: errors.append(f"{name}: no readable text; scanned PDFs may need OCR.")
        except Exception as e: errors.append(f"{uploaded.name}: {e}")
    return "\n".join(texts), names, errors

def score_job(row, cv_text, selected_roles):
    title, desc = str(row.get("title") or ""), str(row.get("description") or "")
    title_n, blob, cv = norm(title), norm(title + " " + desc), norm(cv_text)
    terms = [t for role in selected_roles for t in ROLE_KEYWORDS.get(role, [role.lower()])]
    title_points = max([48 if term in title_n else 0 for term in terms] + [0])
    if not title_points and any(k in title_n for k in ["document", "edms", "aconex", "handover", "closeout", "coordinator", "submittal", "quality", "records"]): title_points = 24
    if not title_points: return 0, [], []
    matched, gaps, points = [], [], 0
    for label, patterns in SKILLS.items():
        in_job, in_cv = any(re.search(p, blob, re.I) for p in patterns), any(re.search(p, cv, re.I) for p in patterns)
        if in_job and in_cv: matched.append(label); points += 5
        elif in_job: gaps.append(label)
    return min(100, title_points + min(42, points) + (10 if desc else 0)), matched, gaps

def search_jobs(countries, roles, boards, days, per_query, min_score, cv_text, job_type, remote_only, progress):
    from jobspy import scrape_jobs
    all_rows, errors = [], []
    tasks = [(country, role) for country in countries for role in roles]
    for ix, (country, role) in enumerate(tasks, 1):
        cfg = COUNTRIES[country]
        progress.progress((ix-1)/max(len(tasks),1), text=f"Searching {country}: {role} ({ix}/{len(tasks)})")
        active_boards = list(boards)
        if not cfg.get("indeed"):
            # Indeed and Glassdoor country parameter support is limited to JobSpy's listed markets.
            active_boards = [b for b in active_boards if b not in ("indeed", "glassdoor")]
        if not active_boards:
            errors.append(f"{country}: selected boards do not support this country in the current connector."); continue
        kwargs = dict(site_name=active_boards, search_term='"' + role + '"', location=cfg["location"], results_wanted=per_query, hours_old=days*24, verbose=0)
        if "indeed" in active_boards: kwargs["country_indeed"] = cfg["indeed"]
        if job_type != "Any": kwargs["job_type"] = job_type.lower()
        if remote_only: kwargs["is_remote"] = True
        try:
            result = scrape_jobs(**kwargs)
            if result is not None and not result.empty:
                for item in result.to_dict("records"):
                    item["search_country"], item["search_role"] = country, role
                    all_rows.append(item)
        except Exception as e: errors.append(f"{country} / {role}: {str(e)[:160]}")
        # Be gentle to job boards; do not run requests in parallel.
        time.sleep(0.25)
    progress.progress(1.0, text="Removing duplicates and scoring matches…")
    if not all_rows: progress.empty(); return pd.DataFrame(), errors
    raw = pd.DataFrame(all_rows)
    for col in ["job_url", "title", "company", "location", "description"]:
        if col not in raw: raw[col] = ""
    raw["_dedupe"] = raw.apply(lambda r: norm(r.get("job_url")) or (norm(r.get("title"))+"|"+norm(r.get("company"))+"|"+norm(r.get("location"))), axis=1)
    raw = raw.drop_duplicates("_dedupe", keep="first")
    out = []
    for row in raw.to_dict("records"):
        score, matched, gaps = score_job(row, cv_text, roles)
        if score < min_score: continue
        desc = str(row.get("description") or "")
        job_url = row.get("job_url_direct") or row.get("job_url") or ""
        job_id = str(job_url).strip() or (norm(row.get("title"))+"|"+norm(row.get("company"))+"|"+norm(row.get("location")))
        out.append({"Job ID": job_id, "Match %": score, "Role": row.get("title"), "Matched Search Title": row.get("search_role"), "Company": row.get("company"), "Country": row.get("search_country"), "Location": row.get("location"), "Work Mode": "Remote" if re.search(r"remote|work from home", str(row.get("title"))+" "+desc, re.I) else ("Hybrid" if re.search(r"hybrid", desc, re.I) else "Not stated"), "Job Type": row.get("job_type") or "Not stated", "Date Posted": str(row.get("date_posted") or ""), "Board": row.get("site") or "", "Matched CV Skills": ", ".join(matched), "Possible Skill Gaps": ", ".join(gaps), "Apply Link": job_url, "Status": "To Apply", "Date Applied": "", "Follow-up Date": "", "Priority": "Normal", "Notes": "", "Description": desc})
    progress.empty()
    df = pd.DataFrame(out)
    if not df.empty: df = df.sort_values(["Match %", "Date Posted"], ascending=[False, False]).reset_index(drop=True)
    return df, errors

st.title("🎯 Atif Job Finder Pro")
st.caption("Multi-title job search · multi-country filters · application tracking · direct local job portals")
with st.sidebar:
    st.header("1. CV & search filters")
    uploaded_cvs = st.file_uploader("Upload up to 6 actual CVs", type=["pdf", "docx", "txt"], accept_multiple_files=True, help="CVs are processed for matching in this session. Do not upload passports or other sensitive documents.")
    st.divider()
    countries = st.multiselect("Target countries (multi-select)", list(COUNTRIES), default=["Saudi Arabia", "United Arab Emirates", "Qatar", "Germany", "Netherlands", "Ireland", "United Kingdom - Scotland", "Malta", "Romania", "France"])
    roles = st.multiselect("Job titles (38 options; multi-select)", ROLE_TITLES, default=["Document Controller", "Senior Document Controller", "Document Control Specialist", "EDMS Coordinator", "Aconex Administrator", "Handover Coordinator", "Closeout Coordinator", "QA/QC Document Controller"])
    boards = st.multiselect("Search connectors", ["indeed", "linkedin", "glassdoor", "bayt", "naukri", "bdjobs"], default=["indeed", "linkedin"], help="Connector availability varies by country. Some sites may block automated access. Local portals are listed separately below.")
    days = st.select_slider("Posted within", options=[1, 3, 7, 14, 30, 60], value=14)
    per_query = st.select_slider("Results per title/country search", options=[5, 10, 15, 20], value=10)
    min_score = st.slider("Minimum CV match", 0, 90, 25, 5)
    job_type = st.selectbox("Job type", ["Any", "Fulltime", "Contract", "Parttime", "Internship", "Temporary"])
    remote_only = st.checkbox("Remote jobs only", value=False)
    st.caption(f"Estimated search requests: {len(countries) * len(roles)}. For a faster run, select fewer countries and titles.")
    run_search = st.button("🚀 Search jobs", type="primary", use_container_width=True)
    st.divider()
    st.header("2. Import application tracker")
    tracker_upload = st.file_uploader("Import previous tracker CSV", type=["csv"], key="tracker_upload")
    st.divider()
    all_portals = sorted({name.strip() for cfg in COUNTRIES.values() for name, _ in cfg["sites"]})
    selected_portals = st.multiselect("Country-specific portals to show", all_portals, default=["Bayt", "Naukrigulf", "GulfTalent", "StepStone", "IrishJobs", "JobsinMalta", "France Travail", "Pracuj.pl", "Jobs.cz"])

cv_text, cv_names, cv_errors = read_uploaded_cvs(uploaded_cvs)
if cv_text:
    st.success(f"CV text extracted from {len(cv_names)} file(s).")
    with st.expander("CV files being used"): st.write("\n".join("• "+n for n in cv_names))
else: st.info("Upload your real CVs in the left sidebar. You do not need to upload CVs to GitHub.")
for e in cv_errors: st.warning(e)

if "jobs_df" not in st.session_state: st.session_state.jobs_df = pd.DataFrame()
if tracker_upload is not None and "tracker_loaded" not in st.session_state:
    try:
        imported = pd.read_csv(tracker_upload).fillna("")
        st.session_state.jobs_df = imported
        st.session_state.tracker_loaded = True
        st.success(f"Imported {len(imported)} tracker rows.")
    except Exception as e: st.error(f"Could not import tracker CSV: {e}")
if run_search:
    if not cv_text: st.error("Upload at least one readable CV first.")
    elif not countries or not roles or not boards: st.error("Select at least one country, job title and search connector.")
    else:
        prog = st.progress(0, text="Preparing searches…")
        try:
            found, errs = search_jobs(countries, roles, boards, days, per_query, min_score, cv_text, job_type, remote_only, prog)
            # Keep previously tracked status/notes when a job appears again.
            old = st.session_state.jobs_df
            if not old.empty and "Job ID" in old.columns and not found.empty:
                old = old.drop_duplicates("Job ID", keep="last").set_index("Job ID", drop=False)
                for i, row in found.iterrows():
                    jid = row["Job ID"]
                    if jid in old.index:
                        for col in ["Status", "Date Applied", "Follow-up Date", "Priority", "Notes"]:
                            if col in old.columns and str(old.loc[jid].get(col, "")): found.at[i, col] = old.loc[jid, col]
            st.session_state.jobs_df = found
            if found.empty: st.warning("No jobs passed your current filters. Try a lower match score, more countries/titles, or a longer posting window.")
            else: st.success(f"Found {len(found)} unique matching jobs across {found['Country'].nunique()} countries.")
            for err in errs[:12]: st.warning(err)
            if len(errs) > 12: st.caption(f"{len(errs)-12} additional source/query warnings omitted.")
        except Exception as e: st.error(f"Search failed: {e}")

df = st.session_state.jobs_df
if not df.empty:
    # Ensure tracker columns exist for older CSVs / previous searches.
    for col, default in [("Status", "To Apply"), ("Date Applied", ""), ("Follow-up Date", ""), ("Priority", "Normal"), ("Notes", "")]:
        if col not in df: df[col] = default
    a,b,c,d,e = st.columns(5)
    a.metric("Unique findings", len(df))
    b.metric("Countries found", df["Country"].nunique(dropna=True))
    c.metric("Strong matches 70%+", int((pd.to_numeric(df["Match %"], errors="coerce") >= 70).sum()))
    d.metric("Applied", int((df["Status"] == "Applied").sum()))
    e.metric("Interviews", int((df["Status"] == "Interview").sum()))
    st.subheader("🔎 Filter findings")
    f1,f2,f3,f4 = st.columns(4)
    with f1: country_filter = st.multiselect("Country", sorted(df["Country"].dropna().astype(str).unique()), default=[])
    with f2: role_filter = st.multiselect("Role", sorted(df["Role"].dropna().astype(str).unique()), default=[])
    with f3: status_filter = st.multiselect("Application status", STATUSES, default=[])
    with f4: board_filter = st.multiselect("Board", sorted(df["Board"].dropna().astype(str).unique()), default=[])
    f5,f6 = st.columns(2)
    with f5: score_filter = st.slider("Match score range", 0, 100, (0,100))
    with f6: search_text = st.text_input("Find company, keyword, location")
    view = df.copy()
    if country_filter: view = view[view["Country"].astype(str).isin(country_filter)]
    if role_filter: view = view[view["Role"].astype(str).isin(role_filter)]
    if status_filter: view = view[view["Status"].astype(str).isin(status_filter)]
    if board_filter: view = view[view["Board"].astype(str).isin(board_filter)]
    view = view[pd.to_numeric(view["Match %"], errors="coerce").between(score_filter[0], score_filter[1])]
    if search_text: view = view[view.astype(str).apply(lambda col: col.str.contains(search_text, case=False, na=False)).any(axis=1)]
    st.caption(f"Showing {len(view)} of {len(df)} findings. Search results are not the same as all vacancies on the internet.")
    show_cols = ["Match %", "Role", "Company", "Country", "Location", "Board", "Date Posted", "Work Mode", "Status", "Date Applied", "Follow-up Date", "Priority", "Apply Link", "Notes"]
    show_cols = [c for c in show_cols if c in view.columns]
    edited = st.data_editor(view[show_cols], use_container_width=True, hide_index=True, num_rows="fixed", key="tracker_editor", column_config={"Apply Link": st.column_config.LinkColumn("Apply Link", display_text="Open job"), "Match %": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d%%"), "Status": st.column_config.SelectboxColumn("Status", options=STATUSES, required=True), "Priority": st.column_config.SelectboxColumn("Priority", options=["Low", "Normal", "High", "Urgent"]), "Date Applied": st.column_config.TextColumn("Date Applied", help="YYYY-MM-DD"), "Follow-up Date": st.column_config.TextColumn("Follow-up Date", help="YYYY-MM-DD")})
    # Persist edits back into full data by Job ID.
    if not edited.empty and "Job ID" in view.columns:
        edited_ids = view.loc[edited.index, "Job ID"] if set(edited.index).issubset(set(view.index)) else None
        if edited_ids is not None:
            for idx, jid in edited_ids.items():
                mask = st.session_state.jobs_df["Job ID"].astype(str) == str(jid)
                for col in ["Status", "Date Applied", "Follow-up Date", "Priority", "Notes"]:
                    if col in edited.columns: st.session_state.jobs_df.loc[mask, col] = edited.loc[idx, col]
    st.subheader("📌 Job details")
    choices = view.to_dict("records")
    if choices:
        labels = [f"{r.get('Role','')} — {r.get('Company','')} | {r.get('Country','')} | {r.get('Match %','')}%" for r in choices]
        selected_idx = st.selectbox("Choose a finding", range(len(labels)), format_func=lambda i: labels[i])
        job = choices[selected_idx]
        st.write(f"**Status:** {job.get('Status','To Apply')} · **Priority:** {job.get('Priority','Normal')} · **Board:** {job.get('Board','')}")
        if job.get("Apply Link"): st.link_button("Open job posting / application", str(job.get("Apply Link")))
        st.write("**Matched CV skills:** " + str(job.get("Matched CV Skills") or "No clear skill overlap detected"))
        st.write("**Possible skill gaps:** " + str(job.get("Possible Skill Gaps") or "No obvious gaps detected"))
        st.text_area("Job description", value=str(job.get("Description") or "No description returned by the board."), height=220, disabled=True)
    st.subheader("⬇️ Export & backup")
    x1,x2 = st.columns(2)
    with x1: st.download_button("Download findings + tracker (CSV)", data=st.session_state.jobs_df.to_csv(index=False).encode("utf-8-sig"), file_name="atif_job_tracker.csv", mime="text/csv", use_container_width=True)
    with x2:
        buff = BytesIO()
        with pd.ExcelWriter(buff, engine="openpyxl") as writer: st.session_state.jobs_df.to_excel(writer, index=False, sheet_name="Job Tracker")
        st.download_button("Download findings + tracker (Excel)", data=buff.getvalue(), file_name="atif_job_tracker.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.caption("Tracker edits live in this session. Download the CSV/Excel regularly; hosted app memory may reset when the app restarts. Import the CSV next time to continue tracking.")
else:
    st.info("No findings loaded yet. Upload CVs, select multiple job titles and countries, then press Search jobs. Start with 3–5 countries and 5–8 titles to keep search times reasonable.")

with st.expander("🌍 Country-specific job portals (direct links)"):
    st.caption("Choose portal names in the sidebar filter. These are country-specific external sites; they open their own search pages and are not counted as scraped live findings.")
    for country, cfg in COUNTRIES.items():
        matches = [(name.strip(), url) for name, url in cfg["sites"] if name.strip() in selected_portals]
        if matches:
            st.markdown(f"**{country}**")
            st.markdown(" · ".join(f"[{name}]({url})" for name,url in matches))

st.divider()
st.caption("Important: this app does not automatically submit applications or log in to job-board accounts. Scraping coverage depends on each board and may be blocked or incomplete. Use local portal links for extra sources, verify each vacancy and work-permit eligibility. This tool does not guarantee jobs or visa sponsorship.")

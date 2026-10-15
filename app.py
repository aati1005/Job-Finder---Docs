from datetime import datetime
from io import BytesIO
import re, time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Atif Job Finder", page_icon="🎯", layout="wide")

COUNTRIES = {
    "Saudi Arabia": {
        "indeed": "saudi arabia", "location": "Saudi Arabia",
        "portals": [("Bayt", "https://www.bayt.com/en/saudi-arabia/jobs/"), ("Naukrigulf", "https://www.naukrigulf.com/"), ("GulfTalent", "https://www.gulftalent.com/saudi-arabia/jobs"), ("Jadarat", "https://jadarat.sa/"), ("LinkedIn Jobs", "https://www.linkedin.com/jobs/")]
    },
    "Dubai": {
        "indeed": "united arab emirates", "location": "Dubai, United Arab Emirates",
        "portals": [("Naukrigulf Dubai", "https://www.naukrigulf.com/jobs-in-dubai"), ("GulfTalent UAE", "https://www.gulftalent.com/uae/jobs"), ("Foundit Gulf", "https://www.founditgulf.com/"), ("Bayt UAE", "https://www.bayt.com/en/uae/jobs/"), ("LinkedIn Jobs", "https://www.linkedin.com/jobs/")]
    }
}

ROLE_TITLES = [
    "Document Controller", "Senior Document Controller", "Lead Document Controller", "Document Control Specialist",
    "Document Control Coordinator", "Document Control Supervisor", "Document Control Manager", "EDMS Coordinator",
    "EDMS Specialist", "Aconex Administrator", "Aconex Coordinator", "Document Management Specialist",
    "Project Document Controller", "Technical Document Controller", "Construction Document Controller",
    "Engineering Document Controller", "Information Management Coordinator", "Records Controller",
    "Records Management Coordinator", "Handover Coordinator", "Turnover Coordinator", "Closeout Coordinator",
    "O&M Documentation Coordinator", "Completions Coordinator", "Asset Information Coordinator",
    "QA/QC Document Controller", "Quality Documentation Coordinator", "Inspection Coordinator",
    "Submittals Coordinator", "Transmittal Coordinator", "Procurement Document Controller",
    "Contracts Document Controller", "Project Coordinator", "Project Documentation Coordinator",
    "Project Administrator", "Technical Clerk", "Site Administrator", "Project Support Coordinator"
]
STATUSES = ["To Apply", "Saved", "Applied", "Follow-up", "Interview", "Rejected", "Closed"]

ROLE_TERMS = {
    "Document Controller": ["document controller", "document control"],
    "Senior Document Controller": ["senior document controller", "senior document control"],
    "Lead Document Controller": ["lead document controller", "lead document control"],
    "Document Control Specialist": ["document control specialist"],
    "Document Control Coordinator": ["document control coordinator"],
    "Document Control Supervisor": ["document control supervisor"],
    "Document Control Manager": ["document control manager"],
    "EDMS Coordinator": ["edms coordinator", "edms specialist"],
    "EDMS Specialist": ["edms specialist", "electronic document management"],
    "Aconex Administrator": ["aconex administrator", "oracle aconex"],
    "Aconex Coordinator": ["aconex coordinator"],
    "Document Management Specialist": ["document management specialist"],
    "Project Document Controller": ["project document controller"],
    "Technical Document Controller": ["technical document controller"],
    "Construction Document Controller": ["construction document controller"],
    "Engineering Document Controller": ["engineering document controller"],
    "Information Management Coordinator": ["information management coordinator"],
    "Records Controller": ["records controller", "records coordinator"],
    "Records Management Coordinator": ["records management coordinator"],
    "Handover Coordinator": ["handover coordinator", "handover documentation"],
    "Turnover Coordinator": ["turnover coordinator"],
    "Closeout Coordinator": ["closeout coordinator", "close-out coordinator"],
    "O&M Documentation Coordinator": ["o&m documentation", "operation and maintenance documentation"],
    "Completions Coordinator": ["completions coordinator"],
    "Asset Information Coordinator": ["asset information coordinator"],
    "QA/QC Document Controller": ["qa/qc document controller", "quality document controller"],
    "Quality Documentation Coordinator": ["quality documentation coordinator"],
    "Inspection Coordinator": ["inspection coordinator"],
    "Submittals Coordinator": ["submittals coordinator", "submittal coordinator"],
    "Transmittal Coordinator": ["transmittal coordinator"],
    "Procurement Document Controller": ["procurement document controller"],
    "Contracts Document Controller": ["contracts document controller"],
    "Project Coordinator": ["project coordinator"],
    "Project Documentation Coordinator": ["project documentation coordinator"],
    "Project Administrator": ["project administrator"],
    "Technical Clerk": ["technical clerk"],
    "Site Administrator": ["site administrator"],
    "Project Support Coordinator": ["project support coordinator"]
}

def norm(v):
    return re.sub(r"\s+", " ", str(v or "").strip().lower())

def relevance_score(title, description, selected_roles):
    title_n = norm(title)
    desc_n = norm(description)
    terms = [t for role in selected_roles for t in ROLE_TERMS.get(role, [role.lower()])]
    if any(t in title_n for t in terms):
        score = 80
    elif any(t in (title_n + " " + desc_n) for t in terms):
        score = 55
    elif any(k in title_n for k in ["document", "edms", "aconex", "handover", "closeout", "coordinator", "records", "submittal"]):
        score = 35
    else:
        score = 15
    if desc_n:
        score += min(15, sum(1 for k in ["aconex", "edms", "transmittal", "rfi", "mir", "wir", "ncr", "handover", "closeout", "document control"] if k in desc_n) * 2)
    return min(100, score)

def search_jobs(countries, roles, boards, days, per_search, job_type, remote_only, progress):
    from jobspy import scrape_jobs
    rows, errors = [], []
    tasks = [(country, role) for country in countries for role in roles]
    for i, (country, role) in enumerate(tasks, 1):
        cfg = COUNTRIES[country]
        progress.progress((i-1)/max(1, len(tasks)), text=f"Searching {country} · {role} ({i}/{len(tasks)})")
        active = list(boards)
        # Bayt and other connectors may not be available consistently; errors are recorded per query.
        kwargs = dict(site_name=active, search_term='"' + role + '"', location=cfg["location"], results_wanted=per_search, hours_old=days*24, verbose=0)
        if "indeed" in active:
            kwargs["country_indeed"] = cfg["indeed"]
        if job_type != "Any": kwargs["job_type"] = job_type.lower()
        if remote_only: kwargs["is_remote"] = True
        try:
            result = scrape_jobs(**kwargs)
            if result is not None and not result.empty:
                for item in result.to_dict("records"):
                    item["_target_country"] = country
                    item["_search_role"] = role
                    rows.append(item)
        except Exception as exc:
            errors.append(f"{country} / {role}: {str(exc)[:180]}")
        time.sleep(0.2)
    progress.progress(1.0, text="Removing duplicate listings…")
    progress.empty()
    if not rows: return pd.DataFrame(), errors
    raw = pd.DataFrame(rows)
    for col in ["job_url", "job_url_direct", "title", "company", "location", "description", "date_posted", "site", "job_type"]:
        if col not in raw: raw[col] = ""
    raw["_dedupe"] = raw.apply(lambda r: norm(r.get("job_url_direct")) or norm(r.get("job_url")) or "|".join([norm(r.get("title")), norm(r.get("company")), norm(r.get("location")), norm(r.get("_target_country"))]), axis=1)
    raw = raw.drop_duplicates("_dedupe", keep="first")
    out = []
    for r in raw.to_dict("records"):
        title, desc = str(r.get("title") or ""), str(r.get("description") or "")
        score = relevance_score(title, desc, roles)
        url = str(r.get("job_url_direct") or r.get("job_url") or "")
        out.append({"Job ID": url or "|".join([norm(title), norm(r.get("company")), norm(r.get("location")), norm(r.get("_target_country"))]),
                    "Relevance %": score, "Role": title, "Search title": r.get("_search_role"), "Company": r.get("company") or "Not listed",
                    "Country": r.get("_target_country"), "Location": r.get("location") or COUNTRIES[r.get("_target_country", "Saudi Arabia")]["location"],
                    "Work Mode": "Remote" if re.search(r"remote|work from home", title+" "+desc, re.I) else ("Hybrid" if re.search(r"hybrid", desc, re.I) else "Not stated"),
                    "Job Type": r.get("job_type") or "Not stated", "Date Posted": str(r.get("date_posted") or ""), "Board": r.get("site") or "",
                    "Apply Link": url, "Status": "To Apply", "Date Applied": "", "Follow-up Date": "", "Priority": "Normal", "Notes": "", "Description": desc})
    df = pd.DataFrame(out)
    if not df.empty: df = df.sort_values(["Relevance %", "Date Posted"], ascending=[False, False]).reset_index(drop=True)
    return df, errors

st.title("🎯 Atif Job Finder")
st.caption("Simple job search for Saudi Arabia and Dubai · save jobs · track applications")

with st.sidebar:
    st.subheader("1. Choose where")
    countries = st.multiselect("Country / city", list(COUNTRIES.keys()), default=["Saudi Arabia", "Dubai"])
    st.subheader("2. Choose job titles")
    roles = st.multiselect("Job titles (select more than one)", ROLE_TITLES, default=["Document Controller", "Senior Document Controller", "Document Control Specialist", "EDMS Coordinator", "Aconex Administrator", "Handover Coordinator", "Closeout Coordinator", "QA/QC Document Controller"])
    with st.expander("Search settings"):
        boards = st.multiselect("Job sources", ["indeed", "linkedin", "glassdoor", "bayt", "naukri"], default=["indeed", "linkedin"], help="Availability depends on each website; blocked sources may return no results.")
        days = st.selectbox("Jobs posted within", [1, 3, 7, 14, 30, 60], index=3)
        per_search = st.selectbox("Results per title", [5, 10, 15, 20], index=1)
        job_type = st.selectbox("Job type", ["Any", "Fulltime", "Contract", "Parttime", "Temporary"])
        remote_only = st.checkbox("Remote jobs only", value=False)
    run_search = st.button("🔎 Search jobs", type="primary", use_container_width=True)
    st.divider()
    st.subheader("Application tracker")
    tracker_upload = st.file_uploader("Import saved tracker (CSV)", type=["csv"], key="tracker_upload")

if "jobs_df" not in st.session_state: st.session_state.jobs_df = pd.DataFrame()
if tracker_upload is not None and not st.session_state.get("tracker_loaded", False):
    try:
        st.session_state.jobs_df = pd.read_csv(tracker_upload).fillna("")
        st.session_state.tracker_loaded = True
        st.success("Previous tracker imported.")
    except Exception as e: st.error(f"Could not import tracker: {e}")

if run_search:
    if not countries or not roles or not boards:
        st.error("Select at least one country, job title and source.")
    else:
        prog = st.progress(0, text="Starting search…")
        try:
            found, errors = search_jobs(countries, roles, boards, days, per_search, job_type, remote_only, prog)
            old = st.session_state.jobs_df
            if not old.empty and "Job ID" in old.columns and not found.empty:
                old = old.drop_duplicates("Job ID", keep="last").set_index("Job ID", drop=False)
                for ix, row in found.iterrows():
                    jid = row["Job ID"]
                    if jid in old.index:
                        for col in ["Status", "Date Applied", "Follow-up Date", "Priority", "Notes"]:
                            if col in old.columns and str(old.loc[jid].get(col, "")): found.at[ix, col] = old.loc[jid, col]
            st.session_state.jobs_df = found
            if found.empty: st.warning("No jobs returned. Try more titles, a longer posting window, or another source.")
            else: st.success(f"Found {len(found)} unique listings.")
            for err in errors[:8]: st.warning(err)
            if len(errors) > 8: st.caption(f"{len(errors)-8} more source errors not shown.")
        except Exception as e: st.error(f"Search failed: {e}")

# Small quick links are shown regardless of whether any scraped listings were found.
with st.expander("🌐 Local job websites", expanded=False):
    for country, cfg in COUNTRIES.items():
        st.markdown(f"**{country}** · " + " · ".join(f"[{name}]({url})" for name, url in cfg["portals"]))

df = st.session_state.jobs_df
if not df.empty:
    for col, default in [("Status", "To Apply"), ("Date Applied", ""), ("Follow-up Date", ""), ("Priority", "Normal"), ("Notes", "")]:
        if col not in df: df[col] = default
    st.subheader("Your job dashboard")
    a, b, c, d = st.columns(4)
    a.metric("Findings", len(df))
    b.metric("To apply", int((df["Status"] == "To Apply").sum()))
    c.metric("Applied", int((df["Status"] == "Applied").sum()))
    d.metric("Interviews", int((df["Status"] == "Interview").sum()))
    with st.expander("Filter results", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1: country_filter = st.multiselect("Country", sorted(df["Country"].dropna().astype(str).unique()))
        with f2: status_filter = st.multiselect("Application status", STATUSES)
        with f3: board_filter = st.multiselect("Source", sorted(df["Board"].dropna().astype(str).unique()))
        keyword = st.text_input("Search company / title / location", placeholder="e.g. NEOM, Aconex, Riyadh")
    view = df.copy()
    if country_filter: view = view[view["Country"].astype(str).isin(country_filter)]
    if status_filter: view = view[view["Status"].astype(str).isin(status_filter)]
    if board_filter: view = view[view["Board"].astype(str).isin(board_filter)]
    if keyword: view = view[view.astype(str).apply(lambda col: col.str.contains(keyword, case=False, na=False)).any(axis=1)]
    st.caption(f"Showing {len(view)} of {len(df)} listings. Use the status and notes columns to track applications.")
    columns = ["Relevance %", "Role", "Company", "Country", "Location", "Board", "Date Posted", "Status", "Date Applied", "Follow-up Date", "Priority", "Apply Link", "Notes"]
    columns = [c for c in columns if c in view.columns]
    edited = st.data_editor(view[columns], use_container_width=True, hide_index=True, key="tracker_editor", column_config={
        "Apply Link": st.column_config.LinkColumn("Apply", display_text="Open job"),
        "Relevance %": st.column_config.ProgressColumn("Relevance", min_value=0, max_value=100, format="%d%%"),
        "Status": st.column_config.SelectboxColumn("Status", options=STATUSES, required=True),
        "Priority": st.column_config.SelectboxColumn("Priority", options=["Low", "Normal", "High", "Urgent"]),
    })
    if not edited.empty:
        # Update tracker edits using stable job IDs from the visible view.
        for visible_index in view.index:
            jid = str(df.loc[visible_index, "Job ID"])
            mask = st.session_state.jobs_df["Job ID"].astype(str) == jid
            if visible_index in edited.index:
                for col in ["Status", "Date Applied", "Follow-up Date", "Priority", "Notes"]:
                    if col in edited.columns: st.session_state.jobs_df.loc[mask, col] = edited.loc[visible_index, col]
    st.subheader("Download / backup")
    x1, x2 = st.columns(2)
    with x1:
        st.download_button("Download CSV tracker", st.session_state.jobs_df.to_csv(index=False).encode("utf-8-sig"), "atif_job_tracker.csv", "text/csv", use_container_width=True)
    with x2:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer: st.session_state.jobs_df.to_excel(writer, index=False, sheet_name="Job Tracker")
        st.download_button("Download Excel tracker", buffer.getvalue(), "atif_job_tracker.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.caption("Important: download your tracker regularly. Hosted app memory may reset after restart. Import the CSV next time to restore it.")
else:
    st.info("Start here: select Saudi Arabia and/or Dubai, choose your job titles, then press **Search jobs**. No CV upload is needed.")

st.caption("Search results depend on each job board's availability and may be incomplete. The relevance score is a title/keyword estimate, not an AI review of your CV. The app does not submit applications automatically.")

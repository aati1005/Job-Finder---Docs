# Atif Job Finder Pro — Advanced

A Streamlit dashboard for targeted document-control and construction-documentation job searches, CV keyword matching, filters, local country job-portal links, and application tracking.

## What's new
- 38 multi-select job titles related to Document Control, Oracle Aconex/EDMS, construction, QA/QC, handover/closeout, records, procurement, project support, and documentation.
- Expanded target countries across the GCC, Europe, Canada, and Australia.
- Per-country + per-title searches rather than one shared OR query for every country, reducing the same few jobs appearing everywhere.
- Selectable job-board connectors (Indeed, LinkedIn, Glassdoor, Bayt, Naukri, BDJobs); site/country support and availability vary. Some sites may block automated searches.
- Country-specific direct links to local job portals, including government portals where available. These direct portals are links, not scraped feeds.
- Advanced filters: country, role, board, application status, match-score range, keyword/company/location, posting age, job type, remote-only.
- Application tracker: To Apply, Saved, Applied, Follow-up, Interview, Rejected, Closed; date applied, follow-up date, priority, notes.
- Import/export tracker CSV and export Excel.
- Upload CVs in the app; no CVs are included in this repository.

## Deploy to Streamlit Community Cloud
1. Replace the existing repository's `app.py`, `requirements.txt`, and `README.md` with these files (do not upload personal CVs).
2. Commit changes to the `main` branch.
3. Streamlit Community Cloud will normally detect the GitHub update and redeploy. If it does not, open Manage app and reboot/redeploy.
4. Open the app, upload your CV files in the sidebar, select countries/titles/boards, and press **Search jobs**.

## Recommended first search
Start with 3–5 countries and 5–8 titles. The app searches each selected title in each selected country, so selecting everything at once may take a long time and can trigger rate limits.

## Local run
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Privacy and limitations
- Do not commit CVs, passports, certificates, bank statements, passwords, or other sensitive documents to GitHub.
- Uploaded CV text is used for matching in the active session. Do not upload anything you do not want processed by the hosted service.
- Job board results can be incomplete, duplicated, blocked, or stale. Local portal links open the site's own search page and are not represented as live scraped results.
- The application tracker is held in the active app session. Download CSV/Excel regularly and re-import the CSV next time, because hosted memory may reset.
- This app does not sign into accounts or apply automatically.

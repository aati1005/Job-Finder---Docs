# Atif Job Finder — Simple Edition

A simplified Streamlit job finder focused **only on Saudi Arabia and Dubai**. No CV upload is required. Select multiple job titles from the sidebar, choose job sources, and search.

## Features
- Saudi Arabia and Dubai only
- 38 document-control, EDMS/Aconex, handover, closeout, QA/QC documentation and project-support titles
- Multi-select job titles
- Indeed/LinkedIn/Glassdoor/Bayt/Naukri connectors (availability varies by country and site)
- Local job portal links for Saudi Arabia and Dubai
- Simple results filters, job status tracker, follow-up date, priority and notes
- CSV/Excel export and CSV import to restore a tracker

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this folder.
3. Double-click `Run_Atif_Job_Dashboard.bat`.

## Deploy to Streamlit Community Cloud
1. Upload `app.py`, `requirements.txt`, `README.md` to your GitHub repository.
2. In Streamlit Community Cloud, use branch `main` and main file path `app.py`.
3. Deploy the app.

## Notes
- Search providers can block automated access or return incomplete results; this tool does not guarantee all vacancies are found.
- Relevance is a simple title/keyword estimate; no CV is uploaded or analyzed.
- The app does not apply to jobs automatically. Download your CSV/Excel tracker regularly because hosted session data may reset.
- Do not commit private documents or credentials to a public repository.

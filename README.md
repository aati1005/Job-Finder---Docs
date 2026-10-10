# Atif Job Search Dashboard

A Streamlit job-search dashboard for CV-aware matching of Document Control, Oracle Aconex/EDMS, Handover/Closeout, project coordination, procurement documentation and QA/QC documentation roles.

## Latest updates
- Faster search: one combined search per country instead of repeating a search for every job title.
- Bayt disabled by default because repeated 404 errors were occurring; Indeed and LinkedIn are available.
- Upload your actual CV files in the sidebar (PDF, DOCX or TXT). This works locally and on Streamlit Community Cloud; no fixed Windows folder path is required.
- Choose countries, job families, posting age, results per country and minimum match score.
- Filter and inspect job descriptions, open job links, and download results as CSV or Excel.
- The ZIP does not contain personal CVs or other private documents.

## Run on Windows
1. Extract this ZIP into a normal folder.
2. Install Python 3.11 or newer from https://www.python.org/downloads/ if needed. During setup, select **Add Python to PATH**.
3. Double-click `Run_Atif_Job_Dashboard.bat`.
4. When Streamlit opens in your browser, upload your six actual CVs in the left sidebar and press **Search jobs**.

If Windows blocks the BAT file, open Command Prompt in this folder and run:
```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Free online hosting (Streamlit Community Cloud)
1. Create/sign in to GitHub: https://github.com/signup
2. Create a repository, e.g. `atif-job-dashboard`.
3. Upload `app.py`, `requirements.txt`, and this `README.md`. Do **not** upload CVs, passports, certificates, bank statements, passwords, or other private files.
4. Open https://share.streamlit.io/ and connect GitHub.
5. Choose **Create app**, select your repository and branch, and set the app file to `app.py`; then deploy.
6. Open the app URL and upload your CV files through the sidebar.

**Privacy note:** GitHub repository code can be visible to others if you choose a public repository. Keep personal documents out of GitHub. CVs uploaded in the app are processed for text matching during the session; do not upload documents you do not want processed by the hosted service. The app does not need your CV files stored in the repository.

## Notes / limitations
- Job board access and results vary. Sites may block automated searches, return incomplete results, or change their behavior; this tool cannot guarantee every vacancy will appear.
- Verify every vacancy and employer on the official application page, including work-permit eligibility.
- The dashboard does not log into accounts or apply for jobs automatically.
- On Streamlit Community Cloud, local files written by the app are temporary and may disappear after a restart. Use the CSV/Excel download buttons to keep your results.
- Scanned PDFs may not contain selectable text; those may need OCR before upload.

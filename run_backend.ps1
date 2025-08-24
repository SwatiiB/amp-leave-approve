Set-Location -Path "d:\INTERNSHIP\amp-inbox-leave-approval\backend"
& "D:\INTERNSHIP\amp-inbox-leave-approval\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

@echo off
echo Starting LocalLogger Dashboard...
echo.
echo The dashboard will open in your browser at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run logger_dashboard.py --server.port 8501

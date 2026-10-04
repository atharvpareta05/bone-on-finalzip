@echo off
cd /d "%~dp0\.."
echo ========================================================
echo   CareLens 1.0 - Streamlit Clinical Prototype
echo ========================================================
echo.

if exist .venv\Scripts\streamlit.exe (
    echo Starting Streamlit app from project virtual environment...
    .\.venv\Scripts\streamlit.exe run carelens-v1-streamlit\streamlit_app.py
) else (
    echo Streamlit not found in .venv. Trying system streamlit...
    streamlit run carelens-v1-streamlit\streamlit_app.py
)
pause

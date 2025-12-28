# Home.py
import streamlit as st
from src.database import init_db

st.set_page_config(
    page_title="Personal Finance OS",
    page_icon="💸",
    layout="wide"
)

# Initialize DB on app startup
if 'db_initialized' not in st.session_state:
    try:
        init_db()
        st.session_state['db_initialized'] = True
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")

st.title("💸 Personal Finance OS")
st.markdown("""
### Welcome to your Financial Command Center

Use the sidebar to navigate:
* **💰 Portfolio:** View your current stock holdings and performance.
* **📝 Trade Log:** Enter new stock purchases or sales.
* **🏦 CDS Manager:** Track your Fixed Deposits and Cash.
* **🤖 AI Analyzer:** Analyze CSE Quarterly Reports (PDFs).
* **🧮 Calculator:** Simulate profit scenarios.
""")

# Optional: Show a quick summary metric here (e.g., Total Cash in CDS)
# app.py
import streamlit as st
import os
from dotenv import load_dotenv

# Import our custom modules
from src.services.llm_service import GeminiService
from src.core.calculator import RatioCalculator
from src.models.schemas import FinancialExtract

# 1. Load Environment Variables
load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="CSE Financial Analyzer", page_icon="📈", layout="wide")

def main():
    # --- API Key Validation ---
    # We fetch the key immediately. If it's missing, we stop everything.
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        st.error("🚨 **Configuration Error:** `GEMINI_API_KEY` not found.")
        st.info("Please create a `.env` file in your project root and add: `GEMINI_API_KEY=your_key_here`")
        st.stop() # Stops execution here so the rest of the app doesn't crash

    # --- Header ---
    st.title("🇱🇰 CSE Financial Analyzer")
    st.markdown("""
    **Automated Investment Analysis for the Colombo Stock Exchange.** Upload an Interim Financial Report (PDF) to extract data and calculate key ratios instantly.
    """)

    # --- Sidebar: Operational Inputs ---
    with st.sidebar:
        st.header("⚙️ Data Input")
        st.write("Upload the specific Quarterly Report you want to analyze.")
        
        uploaded_file = st.file_uploader("Upload Report (PDF)", type=["pdf"])
        
        st.divider()
        
        st.write("Enter the market price at the time of analysis.")
        current_price = st.number_input(
            "Current Stock Price (LKR)", 
            min_value=0.0, 
            format="%.2f",
            help="The closing price of the stock to calculate P/E and Yield."
        )

    # --- Main Logic ---
    if uploaded_file and current_price > 0:
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # --- State Management ---
        # Initialize session state for this file if not present
        if 'extracted_data' not in st.session_state or st.session_state.get('current_file') != uploaded_file.name:
            
            # Show the "Analyze" button only if we haven't analyzed this file yet
            if st.button("🚀 Analyze Report with AI", type="primary"):
                with st.spinner("Gemini 1.5 is scanning the financial statements..."):
                    try:
                        # Pass the env key to the service
                        service = GeminiService(api_key=api_key)
                        data = service.analyze_report(temp_path)
                        
                        # Store in session state
                        st.session_state['extracted_data'] = data
                        st.session_state['current_file'] = uploaded_file.name
                        
                        # Force a rerun to show the Verification Form immediately
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

        # --- Section: Verification (Human-in-the-Loop) ---
        if 'extracted_data' in st.session_state:
            st.divider()
            
            # Using a container for the verification section to make it pop
            with st.container(border=True):
                st.subheader("🧐 Verify Extracted Data")
                st.caption("AI extraction is ~95% accurate. Please review figures against the PDF before calculating.")

                with st.form("verification_form"):
                    data = st.session_state['extracted_data']
                    st.markdown(data.company_name)

                    # Layout: 2 Columns
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Income Statement**")
                        net_profit = st.number_input("Net Profit (LKR)", value=float(data.net_profit), format="%f")
                        dividends = st.number_input("Dividend Paid (LKR)", value=float(data.dividend_paid or 0), format="%f")
                    with c2:
                        st.markdown("**Balance Sheet**")
                        total_equity = st.number_input("Total Equity (LKR)", value=float(data.total_equity), format="%f")
                        shares = st.number_input("Shares Outstanding", value=int(data.shares_outstanding), step=1)

                    st.markdown("---")
                    submitted = st.form_submit_button("✅ Confirm & Calculate Ratios", use_container_width=True)

                    if submitted:
                        # Update data object
                        updated_data = FinancialExtract(
                            company_name=data.company_name,
                            report_period_ending=data.report_period_ending,
                            net_profit=net_profit,
                            total_equity=total_equity,
                            shares_outstanding=shares,
                            dividend_paid=dividends
                        )
                        
                        # Calculate
                        results = RatioCalculator.calculate(updated_data, current_price)
                        st.session_state['results'] = results
                        st.rerun()

        # --- Section: Results Dashboard ---
        if 'results' in st.session_state:
            res = st.session_state['results']
            st.divider()
            st.subheader("📊 Analysis Results")
            st.caption(f"*Note: Ratios are calculated based on an annualized projection of the period ending {data.report_period_ending}.*")

            # Row 1: Per-Share Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("EPS (Earnings Per Share)", f"LKR {res.eps_ratio}")
            c2.metric("NAVPS (Net Asset Value)", f"LKR {res.navps_ratio}")
            
            # Logic for P/E coloring
            pe_delta = "Low/Good" if 0 < res.pe_ratio < 12 else None
            c3.metric("P/E Ratio", res.pe_ratio, delta=pe_delta)

            st.markdown("---") # Visual separator

            # Row 2: Ratios & Percentages
            c4, c5, c6 = st.columns(3)
            c4.metric("PBV Ratio", res.pbv_ratio, delta="Undervalued" if res.pbv_ratio < 1.0 else None)
            c5.metric("ROE %", f"{res.roe_percent}%", delta="Healthy" if res.roe_percent > 15 else None)
            c6.metric("Dividend Yield", f"{res.dividend_yield_percent}%")

            # Raw Data View
            with st.expander("View Raw JSON Data"):
                st.json(res.model_dump())

    elif uploaded_file and current_price == 0:
        st.info("👈 Please enter the **Current Stock Price** in the sidebar to begin.")
    
    elif not uploaded_file:
        st.info("👈 Upload a Quarterly Report (PDF) in the sidebar to start.")

if __name__ == "__main__":
    main()
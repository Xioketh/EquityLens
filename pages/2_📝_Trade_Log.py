import streamlit as st
import pandas as pd
from datetime import date
from src.database import engine, run_query

# --- Global Configurations ---
BUY_FEE_PCT = 0.011198591549  # 1.11%
SELL_FEE_PCT = 0.011198591549 # 1.11%

st.header("📝 Trade Log")

# --- Input Form ---
with st.form("trade_form"):
    c1, c2, c3 = st.columns(3)
    tx_date = c1.date_input("Date", date.today())
    ticker = c2.text_input("Ticker Symbol (e.g. JKH)").upper()
    action = c3.selectbox("Action", ["BUY", "SELL"])
    
    c4, c5 = st.columns(2)
    qty = c4.number_input("Quantity", min_value=1, step=1, value=100)
    price = c5.number_input("Price per Share", min_value=0.01, format="%.2f", value=10.0)
    
    # --- Auto-Calculation Logic ---
    # Determine the fee percentage based on action
    current_fee_pct = BUY_FEE_PCT if action == "BUY" else SELL_FEE_PCT
    
    # Calculate values
    raw_amount = qty * price
    calculated_fee = raw_amount * current_fee_pct
    
    # Calculate Net Amount (Add fee if Buying, Subtract fee if Selling)
    if action == "BUY":
        net_amount = raw_amount + calculated_fee
        summary_text = f"You Pay: LKR {net_amount:,.2f}"
    else:
        net_amount = raw_amount - calculated_fee
        summary_text = f"You Receive: LKR {net_amount:,.2f}"

    # --- Display Calculated Info ---
    st.divider()
    info_col1, info_col2, info_col3 = st.columns(3)
    info_col1.info(f"**Gross Value:** {raw_amount:,.2f}")
    info_col2.warning(f"**Fee ({current_fee_pct*100}%):** {calculated_fee:,.2f}")
    info_col3.success(f"**{summary_text}**")
    
    submitted = st.form_submit_button("💾 Save Transaction")
    
    if submitted:
        if ticker and qty > 0 and price > 0:
            run_query(
                """INSERT INTO trades 
                   (date, ticker, action, quantity, price, fees, gross_amount, net_amount) 
                   VALUES (:date, :ticker, :action, :qty, :price, :fees, :gross_amount, :net_amount)""",
                {
                    "date": tx_date, 
                    "ticker": ticker, 
                    "action": action, 
                    "qty": qty, 
                    "price": price, 
                    "fees": calculated_fee, # Saving the auto-calculated fee
                    "gross_amount": raw_amount, # Saving the gross amount
                    "net_amount": net_amount # Saving the net amount
                }
            )
            st.success(f"Saved {action} order for {ticker} | Fee: {calculated_fee:.2f}")
        else:
            st.error("Please fill in all fields correctly.")

# --- View History ---
st.divider()
st.subheader("Transaction History")
df = pd.read_sql("SELECT * FROM trades ORDER BY date DESC", engine)
st.dataframe(df, use_container_width=True)
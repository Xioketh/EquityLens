import streamlit as st

# --- Global Configurations ---
BUY_FEE_PCT = 0.011198591549  # 1.11%
SELL_FEE_PCT = 0.011198591549 # 1.11%

st.header("🧮 Profit Simulator")
st.caption(f"Calculations apply a **{BUY_FEE_PCT*100}%** fee on buys and sells.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Buying Scenario")
    buy_qty = st.number_input("Shares Bought", min_value=1, value=1000, step=1)
    buy_price = st.number_input("Avg Buy Price", min_value=0.01, value=50.0, step=0.5)
    
    # Auto-calc buy stats
    buy_gross = buy_qty * buy_price
    buy_fee = buy_gross * BUY_FEE_PCT
    total_cost = buy_gross + buy_fee
    
    st.markdown(f"""
    * Gross: {buy_gross:,.2f}
    * Fee: `{buy_fee:,.2f}`
    * **Total Cost:** :red[{total_cost:,.2f}]
    """)

with col2:
    st.subheader("2. Selling Scenario")
    # Default sell qty to match buy qty for convenience
    sell_qty = st.number_input("Shares to Sell", min_value=1, max_value=buy_qty, value=buy_qty)
    sell_price = st.number_input("Target Sell Price", min_value=0.01, value=55.0, step=0.5)
    
    # Auto-calc sell stats
    sell_gross = sell_qty * sell_price
    sell_fee = sell_gross * SELL_FEE_PCT
    total_revenue = sell_gross - sell_fee
    
    st.markdown(f"""
    * Gross: {sell_gross:,.2f}
    * Fee: `{sell_fee:,.2f}`
    * **Net Revenue:** :green[{total_revenue:,.2f}]
    """)

st.divider()

# --- Final Calculation ---
# We calculate profit based on the PROPORTIONAL cost of the shares being sold
# (Cost per share * sold qty)
avg_cost_per_share = total_cost / buy_qty
cost_of_sold_shares = avg_cost_per_share * sell_qty

profit = total_revenue - cost_of_sold_shares
roi = (profit / cost_of_sold_shares) * 100

# Display Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Net Profit / Loss", f"LKR {profit:,.2f}", delta_color="normal")
m2.metric("ROI %", f"{roi:.2f}%", delta=roi)
m3.metric("Break-even Price", f"{(total_cost/buy_qty)/(1-SELL_FEE_PCT):.2f}", help="Price needed to cover both buy & sell fees")

# if profit > 0:
#     st.balloons()
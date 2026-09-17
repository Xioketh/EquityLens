# pages/3_💵_Dividends.py
import time
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.services.cse_service import CSEAccessError, CSEDividendService, parse_dividend_record

REQUEST_DELAY_SECONDS = 0.1

st.header("💵 Dividend History")
st.caption(
    "Pulls CASH DIVIDEND announcements from the CSE for a date range, then fetches the "
    "per-announcement breakdown to analyse which companies pay consistently."
)

c1, c2 = st.columns(2)
from_date = c1.date_input("From", value=date.today() - timedelta(days=365))
to_date = c2.date_input("To", value=date.today())

submitted = st.button("🔍 Fetch Dividend History", type="primary")

if submitted:
    if from_date > to_date:
        st.error("'From' date must be before 'To' date.")
        st.stop()

    service = CSEDividendService()

    try:
        with st.spinner("Fetching dividend announcements..."):
            announcements = service.list_dividend_announcements(from_date, to_date)
    except CSEAccessError as e:
        st.error(f"🚨 {e}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to fetch announcement list: {e}")
        st.stop()

    if not announcements:
        st.info("No CASH DIVIDEND announcements found in that date range.")
        st.stop()

    records = []
    progress = st.progress(0.0, text=f"Fetching details 0/{len(announcements)}")
    for i, item in enumerate(announcements):
        try:
            detail = service.get_announcement_detail(item["announcementId"])
            records.append(parse_dividend_record(item, detail))
        except CSEAccessError as e:
            progress.empty()
            st.error(f"🚨 {e}")
            st.stop()
        except Exception as e:
            st.warning(f"Skipped announcement {item.get('announcementId')}: {e}")
        time.sleep(REQUEST_DELAY_SECONDS)
        progress.progress((i + 1) / len(announcements), text=f"Fetching details {i + 1}/{len(announcements)}")
    progress.empty()

    if not records:
        st.warning("No dividend details could be retrieved.")
        st.stop()

    df = pd.DataFrame([r.model_dump() for r in records])
    for col in ("date_of_announcement", "xd_date", "payment_date"):
        df[col] = pd.to_datetime(df[col])
    st.session_state["dividend_df"] = df

if "dividend_df" in st.session_state:
    df = st.session_state["dividend_df"]

    st.divider()
    st.subheader(f"📋 {len(df)} Dividend Announcements")
    st.dataframe(
        df.sort_values("payment_date", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "announcement_id": "Ann. ID",
            "symbol": "Symbol",
            "company_name": "Company",
            "dividend_type": "Type",
            "voting_div_per_share": st.column_config.NumberColumn("Div/Share (Voting)", format="LKR %.2f"),
            "non_voting_div_per_share": st.column_config.NumberColumn("Div/Share (Non-Voting)", format="LKR %.2f"),
            "financial_year": "Financial Year",
            "date_of_announcement": st.column_config.DateColumn("Announced", format="YYYY-MM-DD"),
            "xd_date": st.column_config.DateColumn("XD Date", format="YYYY-MM-DD"),
            "payment_date": st.column_config.DateColumn("Payment Date", format="YYYY-MM-DD"),
            "remarks": "Remarks",
        },
    )

    st.divider()
    st.subheader("📊 By Company")
    st.caption("Click a row to see that company's individual dividend events below.")

    summary = (
        df.groupby("company_name")
        .agg(
            events=("announcement_id", "count"),
            total_voting_div_per_share=("voting_div_per_share", "sum"),
            latest_payment_date=("payment_date", "max"),
        )
        .sort_values(["events", "total_voting_div_per_share"], ascending=[False, False])
        .reset_index()
    )

    selection = st.dataframe(
        summary,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "company_name": "Company",
            "events": "Dividend Events",
            "total_voting_div_per_share": st.column_config.NumberColumn("Total Div/Share (Voting)", format="LKR %.2f"),
            "latest_payment_date": st.column_config.DateColumn("Latest Payment", format="YYYY-MM-DD"),
        },
    )

    selected_rows = selection.selection.rows
    if selected_rows:
        company = summary.iloc[selected_rows[0]]["company_name"]
        st.markdown(f"#### 🔍 {company} — Dividend Events")
        events = df[df["company_name"] == company].sort_values("payment_date", ascending=False)
        st.dataframe(
            events,
            width="stretch",
            hide_index=True,
            column_config={
                "announcement_id": "Ann. ID",
                "symbol": "Symbol",
                "company_name": None,
                "dividend_type": "Type",
                "voting_div_per_share": st.column_config.NumberColumn("Div/Share (Voting)", format="LKR %.2f"),
                "non_voting_div_per_share": st.column_config.NumberColumn("Div/Share (Non-Voting)", format="LKR %.2f"),
                "financial_year": "Financial Year",
                "date_of_announcement": st.column_config.DateColumn("Announced", format="YYYY-MM-DD"),
                "xd_date": st.column_config.DateColumn("XD Date", format="YYYY-MM-DD"),
                "payment_date": st.column_config.DateColumn("Payment Date", format="YYYY-MM-DD"),
                "remarks": "Remarks",
            },
        )

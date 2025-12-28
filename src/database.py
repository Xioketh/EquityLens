# src/database.py
import os
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("POSTGRES_URL")

if not DB_URL:
    st.error("🚨 POSTGRES_URL not found in .env file")
    st.stop()

# Create the engine (connection pool)
engine = create_engine(DB_URL)

def init_db():
    """Create tables if they don't exist."""
    with engine.connect() as conn:
        # Table: Stock Trades
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                action VARCHAR(10) NOT NULL, -- 'BUY' or 'SELL'
                quantity NUMERIC NOT NULL,
                price NUMERIC NOT NULL,
                fees NUMERIC DEFAULT 0,
                gross_amount NUMERIC DEFAULT 0,
                net_amount NUMERIC DEFAULT 0
            );
        """))
        
        # Table: CDS / Cash History
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cash_ledger (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                type VARCHAR(20) NOT NULL, -- 'DEPOSIT', 'WITHDRAW', 'CD_OPEN', 'CD_CLOSE'
                amount NUMERIC NOT NULL,
                bank VARCHAR(50),
                maturity_date DATE,
                interest_rate NUMERIC
            );
        """))
        conn.commit()

def run_query(query, params=None):
    """Helper to run SQL queries."""
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        conn.commit()
        return result
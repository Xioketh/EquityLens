# src/core/calculator.py
import datetime
from dateutil import parser
from src.models.schemas import FinancialExtract, InvestmentRatios

class RatioCalculator:
    
    @staticmethod
    def _get_annualization_factor(report_date_str: str) -> float:
        """
        Determines the multiplier to annualize earnings based on the report month.
        Assumes standard Sri Lankan Fiscal Year (April 1 - March 31).
        """
        try:
            # Flexible date parsing (handles "30th Sept 2025", "2025-09-30", etc.)
            dt = parser.parse(report_date_str)
            month = dt.month
            
            # Map month to quarters (Fiscal Year starts April)
            # Q1: June (3mo), Q2: Sept (6mo), Q3: Dec (9mo), Q4: March (12mo)
            if month == 6:  return 4.0      # Q1
            if month == 9:  return 2.0      # Q2
            if month == 12: return 1.3333   # Q3
            if month == 3:  return 1.0      # Full Year
            
            # Fallback for odd dates: return 1.0 (Safety net)
            return 1.0
        except:
            return 1.0

    @staticmethod
    def calculate(data: FinancialExtract, current_price: float) -> InvestmentRatios:
        # 1. Get Multiplier
        factor = RatioCalculator._get_annualization_factor(data.report_period_ending)
        
        # 2. Annualize Profit (Projected)
        annualized_profit = data.net_profit * factor
        
        # Avoid DivisionByZero
        shares = data.shares_outstanding if data.shares_outstanding else 1
        equity = data.total_equity if data.total_equity else 1
        
        # 3. Calculate Metrics
        # EPS uses Annualized Profit
        eps = annualized_profit / shares
        navps = equity / shares
        
        # P/E uses Annualized EPS
        pe = current_price / eps if eps > 0 else 0
        
        pbv = current_price / navps if navps > 0 else 0
        
        # ROE uses Annualized Profit / Equity
        roe = (annualized_profit / equity) * 100
        
        # Dividend Yield (Usually strictly trailing, but if interim, we might not annualize strictly)
        # Let's keep dividend extraction as "Paid so far" or strictly what extracted.
        div_yield = 0
        if data.dividend_paid and current_price > 0:
            # Note: Dividends are tricky. Usually, we don't annualize them blindly.
            # We calculate yield based on "Paid in this period".
            div_yield = ((data.dividend_paid / shares) / current_price) * 100

        return InvestmentRatios(
            eps_ratio=round(eps, 2),
            navps_ratio=round(navps, 2),
            pe_ratio=round(pe, 2),
            pbv_ratio=round(pbv, 2),
            roe_percent=round(roe, 2),
            dividend_yield_percent=round(div_yield, 2)
        )
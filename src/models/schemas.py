# src/models/schemas.py
from datetime import date
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FinancialExtract(BaseModel):
    """
    Schema for financial data extracted from the PDF.
    """
    company_name: str = Field(..., description="Name of the company from the report")
    report_period_ending: str = Field(..., description="The date the reporting period ended")
    
    # --- Financial Data ---
    # Note: Do not pass 'None' as the first argument to Field().
    # It creates a 'default' key in the schema which Gemini rejects.
    
    net_profit: float = Field(..., description="Net Profit for the period (Group/Consolidated figure) in LKR")
    net_profit_page: Optional[int] = Field(description="PDF page number where Net Profit was found")

    total_equity: float = Field(..., description="Total Equity (Group/Consolidated) in LKR")
    total_equity_page: Optional[int] = Field(description="PDF page number where Total Equity was found")

    shares_outstanding: int = Field(..., description="Number of ordinary shares in issue")
    shares_outstanding_page: Optional[int] = Field(description="PDF page number where Shares count was found")

    dividend_paid: Optional[float] = Field(description="Total dividends paid. If none, return null.")
    dividend_paid_page: Optional[int] = Field(description="PDF page number where Dividend info was found")

    @field_validator('net_profit', 'total_equity', 'dividend_paid', mode='before')
    @classmethod
    def clean_financial_strings(cls, v):
        """
        Cleans common formatting issues (commas, currency codes, 'Nil', brackets).
        """
        if v is None:
            return 0.0
            
        if isinstance(v, (int, float)):
            return v
            
        if isinstance(v, str):
            clean = v.replace(',', '').replace('LKR', '').replace('Rs.', '').strip()
            
            if clean.lower() in ['nil', '-', 'none', 'n/a']:
                return 0.0
                
            if clean.startswith('(') and clean.endswith(')'):
                clean = '-' + clean[1:-1]
            
            try:
                return float(clean)
            except ValueError:
                return 0.0
                
        return v
    
class InvestmentRatios(BaseModel):
    eps_ratio: float
    navps_ratio: float
    pe_ratio: float
    pbv_ratio: float
    roe_percent: float
    dividend_yield_percent: float


class DividendRecord(BaseModel):
    """
    A single CASH DIVIDEND announcement from the CSE, parsed from the
    approvedAnnouncement list entry + getAnnouncementById detail.
    """
    announcement_id: int
    symbol: Optional[str] = None
    company_name: str
    dividend_type: str
    voting_div_per_share: float = 0.0
    non_voting_div_per_share: float = 0.0
    financial_year: Optional[str] = None
    date_of_announcement: Optional[date] = None
    xd_date: Optional[date] = None
    payment_date: Optional[date] = None
    remarks: Optional[str] = None
# src/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# src/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class FinancialExtract(BaseModel):
    """
    Schema for financial data extracted from the PDF.
    """
    company_name: str = Field(..., description="Name of the company from the report")
    report_period_ending: str = Field(..., description="The date the reporting period ended")
    
    net_profit: float = Field(..., description="Net Profit for the period (Group/Consolidated figure) in LKR")
    total_equity: float = Field(..., description="Total Equity (Group/Consolidated) in LKR")
    shares_outstanding: int = Field(..., description="Number of ordinary shares in issue")
    
    # FIX: Removed 'default=0.0'. We rely on Optional to allow 'null' from AI.
    dividend_paid: Optional[float] = Field(description="Total dividends paid during the period. If none, return null.")

    @field_validator('net_profit', 'total_equity', 'dividend_paid', mode='before')
    @classmethod
    def clean_financial_strings(cls, v):
        """
        Cleans common formatting issues (commas, currency codes, 'Nil', brackets).
        """
        if v is None:
            return 0.0  # Handle None inputs gracefully
            
        if isinstance(v, (int, float)):
            return v
            
        if isinstance(v, str):
            # clean string
            clean = v.replace(',', '').replace('LKR', '').replace('Rs.', '').strip()
            
            # Handle "Nil" or "-" common in reports
            if clean.lower() in ['nil', '-', 'none', 'n/a']:
                return 0.0
                
            # Handle accounting negative format: (1000) -> -1000
            if clean.startswith('(') and clean.endswith(')'):
                clean = '-' + clean[1:-1]
            
            try:
                return float(clean)
            except ValueError:
                return 0.0 # Fallback safety
                
        return v
    
class InvestmentRatios(BaseModel):
    eps_ratio: float
    navps_ratio: float
    pe_ratio: float
    pbv_ratio: float
    roe_percent: float
    dividend_yield_percent: float
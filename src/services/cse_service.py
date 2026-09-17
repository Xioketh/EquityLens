# src/services/cse_service.py
import logging
from datetime import date
from typing import Optional

import requests
from dateutil import parser as date_parser

from src.models.schemas import DividendRecord

logger = logging.getLogger(__name__)

BASE_URL = "https://www.cse.lk/api"


class CSEAccessError(Exception):
    """Raised when the CSE API rejects or blocks a request (e.g. rate limiting)."""


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date_parser.parse(value).date()
    except (ValueError, TypeError):
        return None


def _dividend_type_label(detail: dict) -> str:
    if detail.get("firstAndFinal"):
        return "First & Final"
    if detail.get("finalDividend"):
        return "Final"
    if detail.get("typeFirstInt"):
        return "1st Interim"
    if detail.get("typeSecondInt"):
        return "2nd Interim"
    if detail.get("typeThirdInt"):
        return "3rd Interim"
    if detail.get("typeFourthInt"):
        return "4th Interim"
    if detail.get("typeOther"):
        return detail.get("otherRemark") or "Other"
    return "Unspecified"


def parse_dividend_record(list_item: dict, detail: dict) -> DividendRecord:
    return DividendRecord(
        announcement_id=list_item["announcementId"],
        symbol=detail.get("symbol"),
        company_name=detail.get("companyName") or list_item.get("company") or "Unknown",
        dividend_type=_dividend_type_label(detail),
        voting_div_per_share=detail.get("votingDivPerShare") or 0.0,
        non_voting_div_per_share=detail.get("nonVotingDivPerShare") or 0.0,
        financial_year=detail.get("financialYear"),
        date_of_announcement=_parse_date(detail.get("dateOfAnnouncement")),
        xd_date=_parse_date(detail.get("xd")),
        payment_date=_parse_date(detail.get("payment")),
        remarks=detail.get("remarks"),
    )


class CSEDividendService:
    """
    Thin client for the (undocumented, public, unauthenticated) cse.lk announcement API.
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.cse.lk",
            "referer": "https://www.cse.lk/general-announcements",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })

    def _post(self, path: str, data: dict) -> dict:
        try:
            resp = self._session.post(f"{BASE_URL}/{path}", data=data, timeout=20)
        except requests.RequestException as e:
            logger.error(f"CSE request to {path} failed: {e}")
            raise

        if resp.status_code in (401, 403, 429):
            raise CSEAccessError(
                f"CSE API rejected the request (HTTP {resp.status_code}). "
                "It may be temporarily rate-limiting or blocking this IP."
            )
        resp.raise_for_status()
        return resp.json()

    def list_dividend_announcements(self, from_date: date, to_date: date) -> list[dict]:
        payload = {
            "type": "",
            "fromDate": from_date.isoformat(),
            "toDate": to_date.isoformat(),
            "announcementCategories": "CASH DIVIDEND",
        }
        data = self._post("approvedAnnouncement", payload)
        return data.get("approvedAnnouncements", [])

    def get_announcement_detail(self, announcement_id: int) -> dict:
        data = self._post("getAnnouncementById", {"announcementId": announcement_id})
        return data.get("reqBaseAnnouncement", {})

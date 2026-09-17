# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

EquityLens is a Streamlit app for Colombo Stock Exchange (CSE) investment research: AI-extracting
financial ratios from quarterly report PDFs via Gemini, a buy/sell profit simulator, and dividend-history
analysis pulled from the CSE's own announcement API. There is no database — everything is session-local.

## Commands

```bash
# Setup (Windows, existing venv/ dir)
venv\Scripts\activate
pip install -r requirements.txt

# Run the app
streamlit run Home.py
```

There is no test suite, linter, or build step configured in this repo.

Required `.env` variable (never commit `.env`):
- `GEMINI_API_KEY` — Google Generative AI key for the LLM extraction service

## Architecture

**Streamlit multipage app.** `Home.py` is the entry point (just page config + a nav welcome message).
Streamlit auto-discovers pages from `pages/*.py` (filenames are `N_<emoji>_Name.py`; the number controls
sidebar order):
- `1_🤖_AI_Analyzer.py` — PDF upload → Gemini extraction → verification form → ratio calculation
- `2_🧮_Calculator.py` — what-if profit/ROI simulator, self-contained, no dependency on the other pages
- `3_💵_Dividends.py` — date range → CSE dividend announcement history → per-company summary

**AI extraction pipeline (`src/services/llm_service.py` → `src/core/calculator.py`).**
1. `GeminiService.analyze_report(pdf_path)` uploads the PDF to the Gemini Files API, polls until
   `ACTIVE`, then calls `generate_content` with `response_schema=FinancialExtract` so Gemini returns
   JSON constrained to the Pydantic schema directly (see `src/models/schemas.py`). The prompt instructs
   Gemini to extract *Group/Consolidated* (not Company) figures and to cite the PDF page number for each
   extracted value — the UI shows these page numbers so the user can verify against the source PDF
   before committing.
2. `FinancialExtract` has a `field_validator` that cleans LLM-returned numeric strings (commas, `LKR`/
   `Rs.` prefixes, `Nil`/`-`/`N/A`, bracket-negatives) before validation.
3. The Streamlit page renders extracted values in an editable form (human-in-the-loop correction) before
   calling `RatioCalculator.calculate(data, current_price)`.
4. `RatioCalculator` annualizes profit based on the **Sri Lankan fiscal year (April–March)**: it infers
   which quarter a report covers from `report_period_ending`'s month (Jun=Q1×4, Sep=Q2×2, Dec=Q3×1.3333,
   Mar=full year×1) and computes EPS, NAVPS, P/E, PBV, ROE, and dividend yield from the annualized figures.
   Dividend yield is deliberately **not** annualized — it uses dividends paid-to-date as extracted.

**Dividend history (`src/services/cse_service.py` → `pages/3_💵_Dividends.py`).** `CSEDividendService`
wraps two undocumented `cse.lk` endpoints, both `POST application/x-www-form-urlencoded`:
1. `api/approvedAnnouncement` — list announcements by category/date range. We always pass
   `announcementCategories=CASH DIVIDEND` and an empty `type` (a non-empty `type` filters to an unrelated
   announcement subtype and returns nothing for dividends).
2. `api/getAnnouncementById` — per-announcement breakdown, keyed by the list entry's `announcementId`
   (not its `id`). Returns per-share amounts (`votingDivPerShare`/`nonVotingDivPerShare`), XD/payment
   dates, and boolean flags (`typeFirstInt`, `finalDividend`, `firstAndFinal`, `typeOther` + `otherRemark`,
   …) that `_dividend_type_label()` collapses into a single label.

Both endpoints are **unauthenticated** — verified directly against the live API with no cookies at all.
(The captured request that this was reverse-engineered from included an `accessToken` cookie, but that was
just incidental to being logged into cse.lk in-browser at capture time; it made no difference to the
response.) `CSEAccessError` (raised on HTTP 401/403/429) exists as a defensive guard in case CSE starts
rate-limiting or blocking — not because auth is expected.

The page fetches announcement details sequentially (one `get_announcement_detail` call per list entry,
with a small delay between calls) rather than in parallel, to avoid hammering an undocumented endpoint
that could start rate-limiting or blocking the session.

## Conventions to preserve

- Page files under `pages/` keep the `N_<emoji>_Name.py` naming scheme — Streamlit uses it for both
  ordering and the sidebar label.
- `FinancialExtract` fields that back optional data use `Optional[...]` with **no explicit default** in
  `Field(...)` — a comment in `schemas.py` notes that passing `None` as Field's first arg adds a
  `default` key to the generated JSON schema that Gemini's `response_schema` rejects.

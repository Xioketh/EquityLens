# src/services/llm_service.py
import os
import time
import json
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.models.schemas import FinancialExtract

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-flash-latest",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": FinancialExtract, # Enforces the Pydantic schema
                "temperature": 0.1, # Low temperature for factual extraction
            }
        )

    def _upload_to_gemini(self, file_path: str, mime_type: str = "application/pdf"):
        """
        Uploads file to Gemini Files API and waits for processing state.
        """
        try:
            file_ref = genai.upload_file(file_path, mime_type=mime_type)
            logger.info(f"Uploaded file: {file_ref.display_name} as {file_ref.uri}")

            # Verify file is ready (State.ACTIVE)
            while file_ref.state.name == "PROCESSING":
                logger.info("File is processing...")
                time.sleep(2)
                file_ref = genai.get_file(file_ref.name)
            
            if file_ref.state.name != "ACTIVE":
                raise ValueError(f"File processing failed: {file_ref.state.name}")
            
            return file_ref
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

    def analyze_report(self, pdf_path: str) -> FinancialExtract:
            file_ref = None
            try:
                # 1. Upload
                file_ref = self._upload_to_gemini(pdf_path)

                # 2. Construct Domain-Specific Prompt
                prompt = """
                Act as a Senior Financial Analyst for the Colombo Stock Exchange. 
                Analyze this Interim Financial Report.
                
                CRITICAL INSTRUCTIONS:
                1. Extract the 'Group' (Consolidated) figures, NOT 'Company' figures.
                2. Look for the "Number of Shares in Issue" usually found in the notes or "Stated Capital" section.
                3. If figures are in thousands ('000), MULTIPLY them by 1,000 to return the absolute LKR value.
                4. If a value is represented in brackets (e.g., (500)), it is negative.
                
                PAGE CITATIONS:
                For every numerical value extracted (Net Profit, Equity, Shares, Dividends), you MUST identify the PDF page number where you found this specific figure. 
                Populate the corresponding '_page' fields in the JSON.
                
                Return PURE JSON matching the schema.
                """

                # 3. Generate Content
                response = self.model.generate_content(
                    [file_ref, prompt],
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )

                # 4. Parse & Validate
                # The SDK with `response_schema` usually returns a Python object directly if accessed via simple JSON parsing
                # specific to the schema, but explicit validation is safer.
                print(response.text)
                json_data = json.loads(response.text)
                validated_data = FinancialExtract(**json_data)
                
                return validated_data

            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                # Re-raise to let the UI know something went wrong
                raise e
            
            finally:
                # 5. Cleanup (Crucial for Privacy & Storage Limits)
                if file_ref:
                    logger.info(f"Deleting file {file_ref.name} from Gemini storage.")
                    genai.delete_file(file_ref.name)
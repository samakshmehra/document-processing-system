import json
import os
from typing import Dict
import google.generativeai as genai
from email_agent import SimpleEmailAgent
from json_agent import JSONAgent

# Configure Gemini API
os.environ["GEMINI_API_KEY"] = "AIzaSyC9Jj2cPonYRjVblF7ZuWO6FdIFaMU8h-4"

class ClassifierAgent:
    def __init__(self, api_key: str = None):
        """Initialize the ClassifierAgent with Gemini API configuration."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Initialize other agents
        self.email_agent = SimpleEmailAgent(self.api_key)
        self.json_agent = JSONAgent(self.api_key)

    def detect_format(self, file_path: str) -> str:
        """Detect the format of the input file."""
        if file_path.endswith(".pdf"):
            return "PDF"
        elif file_path.endswith(".json"):
            return "JSON"
        return "Email"

    def load_file(self, file_path: str) -> str:
        """Load and return the content of the file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def classify_intent(self, document_text: str) -> str:
        """Classify the intent of the document using Gemini."""
        prompt = f"""
Classify this document's intent (one word): {document_text[:1000]}
Examples: Invoice, RFQ, Complaint, Regulation, Resume, Legal Notice
"""
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def process_document(self, file_path: str) -> Dict[str, str]:
        """Process a document and return its format and intent."""
        try:
            file_format = self.detect_format(file_path)
            content = self.load_file(file_path)
            intent = self.classify_intent(content)
            
            # Route to appropriate agent based on format
            if file_format == "Email":
                try:
                    result = self.email_agent.process_email(content)
                    result["format"] = "Email"
                    result["intent"] = intent
                    result["status"] = "success"
                    return result
                except Exception as e:
                    return {
                        "format": "Email",
                        "status": "error",
                        "error": str(e),
                        "intent": intent
                    }
            elif file_format == "JSON":
                try:
                    json_content = json.loads(content)
                    result = self.json_agent.process_json(
                        json_content,
                        intent=intent,
                        format=file_format
                    )
                    result["status"] = "success"
                    return result
                except json.JSONDecodeError as e:
                    return {
                        "format": "JSON",
                        "status": "error",
                        "error": "Invalid JSON format",
                        "intent": intent
                    }
            else:
                return {
                    "format": file_format,
                    "status": "success",
                    "intent": intent
                }
        except Exception as e:
            return {
                "format": "Unknown",
                "status": "error",
                "error": str(e)
            }
    
    
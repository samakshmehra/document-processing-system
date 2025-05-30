import json
import os
import google.generativeai as genai

class JSONAgent:
    def __init__(self, api_key: str = None):
        """Initialize the JSONAgent with Gemini API."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Please provide GEMINI_API_KEY")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def validate_json(self, json_data: dict, required_fields: list = None) -> dict:
        """Validate JSON data and check for required fields."""
        results = {
            "is_valid": True,
            "missing_fields": [],
            "issues": []
        }
        
        # Check required fields
        if required_fields:
            for field in required_fields:
                if field not in json_data:
                    results["is_valid"] = False
                    results["missing_fields"].append(field)
        
        # Use Gemini to check for other issues
        prompt = f"""
        Check this JSON data for any issues or inconsistencies.
        Return ONLY a JSON object with this format:
        {{
            "issues": ["list", "of", "issues", "found"],
            "is_valid": true/false
        }}
        
        If no issues found, return empty list for issues.
        
        JSON data:
        {json.dumps(json_data, indent=2)}
        """
        
        try:
            response = self.model.generate_content(prompt)
            ai_analysis = eval(response.text.strip())
            
            if ai_analysis.get("issues"):
                results["is_valid"] = False
                results["issues"].extend(ai_analysis["issues"])
        except Exception as e:
            results["issues"].append(f"Error in validation: {str(e)}")
            results["is_valid"] = False
        
        return results

    def format_json(self, json_data: dict, required_fields: list = None) -> dict:
        """Format JSON data to include required fields."""
        formatted = json_data.copy()
        
        if required_fields:
            for field in required_fields:
                if field not in formatted:
                    formatted[field] = None
        
        return formatted

    def classify_intent(self, json_data: dict) -> str:
        """Classify the intent of the JSON data using Gemini."""
        prompt = f"""
        Classify this JSON data's intent (one word): {json.dumps(json_data, indent=2)}
        Examples: Project, Configuration, Report, Settings, Data
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "Unknown"

    def process_json(self, json_data: dict, required_fields: list = None, intent: str = None, format: str = None) -> dict:
        """Process JSON data: validate and format."""
        # Validate the data
        validation = self.validate_json(json_data, required_fields)
        
        # Format the data
        formatted_data = self.format_json(json_data, required_fields)
        
        # Create the output with all fields
        output = {
            "is_valid": validation["is_valid"],
            "validation": validation,
            "formatted_data": formatted_data,
            "status": "success" if validation["is_valid"] else "error"
        }
        
        # Add intent and format if provided
        if intent:
            output["intent"] = intent
        if format:
            output["format"] = format
            
        return output

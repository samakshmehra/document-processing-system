import re
import google.generativeai as genai
import os

class SimpleEmailAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Simple Email Agent with Gemini API."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Please provide GEMINI_API_KEY")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def extract_sender(self, email_content: str) -> dict:
        """Extract sender information using Gemini."""
        prompt = f"""
        Extract sender information from this email. Return ONLY a JSON object:
        {{
            "name": "sender's name",
            "email": "sender's email",
            "company": "company name"
        }}
        If unknown, use "Unknown". Email content:
        {email_content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return eval(response.text.strip())
        except Exception:
            # Fallback to basic regex extraction
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', email_content)
            email = email_match.group(1) if email_match else "Unknown"
            return {
                "name": "Unknown",
                "email": email,
                "company": email.split('@')[1].split('.')[0].title() if email != "Unknown" else "Unknown"
            }

    def process_email(self, email_content: str) -> dict:
        """Process email and return structured data."""
        sender_info = self.extract_sender(email_content)
        
        # Extract key information
        prompt = f"""
        Extract key information from this email. Return ONLY a JSON object:
        {{
            "subject": "email subject",
            "urgency": "High/Medium/Low",
            "key_points": ["list", "of", "main", "points"],
            "action_required": "what action is needed"
        }}
        Email: {email_content}
        """
        
        try:
            response = self.model.generate_content(prompt)
            key_info = eval(response.text.strip())
        except Exception:
            key_info = {
                "subject": "Unknown",
                "urgency": "Medium",
                "key_points": [],
                "action_required": "Unknown"
            }
        
        return {
            "sender": sender_info,
            "subject": key_info.get("subject", "Unknown"),
            "urgency": key_info.get("urgency", "Medium"),
            "key_points": key_info.get("key_points", []),
            "action_required": key_info.get("action_required", "Unknown"),
            "content_preview": email_content[:200] + "..." if len(email_content) > 200 else email_content
        }

    def format_for_display(self, processed_data: dict) -> str:
        """Format processed data for display."""
        urgency_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        
        return f"""
📧 EMAIL SUMMARY
═══════════════════════════════════════

📌 SUBJECT: {processed_data['subject']}

👤 SENDER:
   Name: {processed_data['sender']['name']}
   Email: {processed_data['sender']['email']}
   Company: {processed_data['sender']['company']}

🎯 INTENT: {processed_data.get('intent', 'Unknown')}

📋 CLASSIFICATION:
   Format: {processed_data.get('format', 'Email')}
   Urgency: {urgency_emoji.get(processed_data['urgency'], '⚪')} {processed_data['urgency']}

🎯 ACTION REQUIRED:
   {processed_data['action_required']}

📝 KEY POINTS:
{chr(10).join('   • ' + point for point in processed_data['key_points'])}

📄 CONTENT PREVIEW:
{processed_data['content_preview']}
"""
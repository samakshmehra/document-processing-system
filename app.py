import streamlit as st
import tempfile
import os
from datetime import datetime, timedelta
from classifier_agent import ClassifierAgent
import json

# Set page config
st.set_page_config(
    page_title="Document Processing System",
    page_icon="📄",
    layout="wide"
)

# Initialize session state
if 'classifier' not in st.session_state:
    st.session_state.classifier = ClassifierAgent()
if 'processing_history' not in st.session_state:
    st.session_state.processing_history = []

def add_to_history(source: str, type: str, extracted_values: dict, thread_id: str = None):
    """Add a processing step to history."""
    entry = {
        "source": source,
        "type": type,
        "timestamp": datetime.now().isoformat(),
        "thread_id": thread_id,
        "extracted_values": extracted_values
    }
    st.session_state.processing_history.append(entry)

def process_document_with_history(file_path: str, content: str = None) -> dict:
    """Process document with history tracking."""
    # Step 1: Classifier Agent - Detect format and intent
    with st.spinner('Classifying document...'):
        format_result = st.session_state.classifier.detect_format(file_path)
        intent = st.session_state.classifier.classify_intent(content or st.session_state.classifier.load_file(file_path))
        
        # Log classification in history
        classification_entry = {
            "format": format_result,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
        add_to_history(
            source="classifier_agent",
            type="document_classified",
            extracted_values=classification_entry
        )
    
    # Step 2: Route to appropriate agent based on format
    if format_result == "Email":
        # Process email without nested spinner
        email_result = st.session_state.classifier.email_agent.process_email(
            content or st.session_state.classifier.load_file(file_path)
        )
        
        # Determine urgency based on content
        content_lower = (content or st.session_state.classifier.load_file(file_path)).lower()
        if any(word in content_lower for word in ["urgent", "immediate", "asap", "critical"]):
            email_result["urgency"] = "High"
        elif any(word in content_lower for word in ["important", "priority", "attention"]):
            email_result["urgency"] = "Medium"
        else:
            email_result["urgency"] = "Low"
        
        # Log email processing in history
        add_to_history(
            source="email_agent",
            type="email_processed",
            thread_id=classification_entry["timestamp"],
            extracted_values=email_result
        )
        
        return {
            "format": "Email",
            "intent": intent,
            "status": "success",
            **email_result
        }
        
    elif format_result == "JSON":
        with st.spinner('Processing JSON...'):
            try:
                json_content = st.session_state.classifier.load_file(file_path)
                # Ensure proper JSON formatting
                json_data = json.loads(json_content)
                
                # Validate JSON structure
                validation_result = {
                    "is_valid": True,
                    "missing_fields": [],
                    "issues": []
                }
                
                # Check for required fields
                required_fields = ["project", "status", "team", "deadline"]
                for field in required_fields:
                    if field not in json_data:
                        validation_result["missing_fields"].append(field)
                        validation_result["is_valid"] = False
                
                # Format the data
                formatted_data = {
                    "project": json_data.get("project", ""),
                    "status": json_data.get("status", ""),
                    "team": json_data.get("team", []),
                    "deadline": json_data.get("deadline", "")
                }
                
                json_result = {
                    "validation": validation_result,
                    "formatted_data": formatted_data
                }
                
                # Log JSON processing in history
                add_to_history(
                    source="json_agent",
                    type="json_processed",
                    thread_id=classification_entry["timestamp"],
                    extracted_values=json_result
                )
                
                return {
                    "format": "JSON",
                    "intent": intent,
                    "status": "success",
                    **json_result
                }
                
            except json.JSONDecodeError as e:
                error_result = {
                    "validation": {
                        "is_valid": False,
                        "missing_fields": [],
                        "issues": [f"JSON syntax error: {str(e)}"]
                    },
                    "formatted_data": {}
                }
                
                # Log error in history
                add_to_history(
                    source="json_agent",
                    type="json_processed",
                    thread_id=classification_entry["timestamp"],
                    extracted_values=error_result
                )
                
                return {
                    "format": "JSON",
                    "intent": intent,
                    "status": "error",
                    **error_result
                }
    
    return {
        "format": format_result,
        "intent": intent,
        "status": "success"
    }

# App title and description
st.title("📄 Document Processing System")
st.markdown("""
This app processes documents using AI agents to classify, extract information, and validate content.
Upload a document to get started!
""")

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    # Input type selection
    input_type = st.radio(
        "Choose input type",
        ["Upload File", "Enter Email Text"],
        horizontal=True
    )

    if input_type == "Upload File":
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'json', 'txt', 'eml'],
            help="Upload a PDF, JSON, or Email file"
        )

        if uploaded_file is not None:
            # Create a temporary file to save the upload
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                # Process the document
                with st.spinner('Processing document...'):
                    result = process_document_with_history(tmp_file_path)
                
                # Display results
                st.markdown("### 📊 Processing Results")
                
                # Format and Intent - Now directly from agent output
                col_format, col_intent = st.columns(2)
                with col_format:
                    st.metric("Document Format", result.get('format', 'Unknown'))
                with col_intent:
                    st.metric("Document Intent", result.get('intent', 'Unknown'))
                
                # Processed Data
                st.markdown("#### Processed Data")
                if result.get('status') == 'success':
                    if result.get('format') == "Email":
                        # Display email-specific information
                        st.markdown("**Sender Information:**")
                        st.json(result.get('sender', {}))
                        st.markdown(f"**Urgency:** {result.get('urgency', 'Unknown')}")
                        st.markdown("**Content Preview:**")
                        st.text(result.get('content_preview', ''))
                    
                    elif result.get('format') == "JSON":
                        # Display JSON validation results
                        st.markdown("**Validation Results:**")
                        st.json(result.get('validation', {}))
                        st.markdown("**Formatted Data:**")
                        st.json(result.get('formatted_data', {}))
                    
                    else:
                        # Display raw content for other formats
                        st.text(result.get('raw_content', ''))
                
                # Status
                if result.get('status') == 'success':
                    st.success("Document processed successfully!")
                else:
                    st.error(f"Error processing document: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)
    
    else:  # Enter Email Text
        email_text = st.text_area(
            "Enter your email content",
            height=300,
            help="Paste your email content here"
        )
        
        if st.button("Process Email"):
            if email_text:
                try:
                    # Create a temporary file for the email text
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                        tmp_file.write(email_text.encode())
                        tmp_file_path = tmp_file.name

                    # Process the email
                    with st.spinner('Processing email...'):
                        result = process_document_with_history(tmp_file_path, email_text)
                    
                    # Display results
                    st.markdown("### 📊 Processing Results")
                    
                    # Format and Intent - Now directly from agent output
                    col_format, col_intent = st.columns(2)
                    with col_format:
                        st.metric("Document Format", result.get('format', 'Unknown'))
                    with col_intent:
                        st.metric("Document Intent", result.get('intent', 'Unknown'))
                    
                    # Processed Data
                    st.markdown("#### Processed Data")
                    if result.get('status') == 'success':
                        st.markdown("**Sender Information:**")
                        st.json(result.get('sender', {}))
                        st.markdown(f"**Urgency:** {result.get('urgency', 'Unknown')}")
                        st.markdown("**Content Preview:**")
                        st.text(result.get('content_preview', ''))
                    
                    # Status
                    if result.get('status') == 'success':
                        st.success("Email processed successfully!")
                    else:
                        st.error(f"Error processing email: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    # Clean up the temporary file
                    os.unlink(tmp_file_path)
            else:
                st.warning("Please enter some email content to process.")

with col2:
    # Search and History Section
    st.markdown("### 🔍 Search & History")
    
    # Search options
    st.markdown("#### Search Documents")
    search_source = st.selectbox(
        "Source",
        ["All", "email_agent", "json_agent", "classifier_agent"]
    )
    
    search_type = st.selectbox(
        "Type",
        ["All", "email_processed", "json_processed", "document_classified"]
    )
    
    time_range = st.selectbox(
        "Time Range",
        ["Last hour", "Last 24 hours", "Last 7 days", "All time"]
    )
    
    if st.button("Search"):
        st.info("Search functionality is currently disabled as we're using direct agent processing.")

# Add some helpful information in the sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This app uses AI agents to process and analyze documents:
    
    **Supported File Types:**
    - PDF (.pdf)
    - JSON (.json)
    - Email (.eml, .txt)
    
    **Features:**
    - Document classification
    - Email analysis
    - JSON validation
    
    **Agents:**
    - Classifier Agent: Detects document format and intent
    - Email Agent: Extracts sender info and urgency
    - JSON Agent: Validates and reformats JSON data
    """) 
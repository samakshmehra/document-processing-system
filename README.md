# Multi-Agent Document Processing System

A Streamlit-based application that uses multiple AI agents to process and analyze different types of documents (emails, JSON files) with shared memory tracking.

## Features

- **Document Classification**: Automatically detects document format and intent
- **Email Processing**: Extracts sender information, urgency, and content
- **JSON Validation**: Validates and formats JSON data
- **Shared Memory**: Tracks processing history across all agents
- **Real-time History**: Displays processing steps with timestamps and relationships

## Project Structure

```
.
├── app.py                 # Main Streamlit application
├── classifier_agent.py    # Document classification agent
├── memory_store.py       # Shared memory implementation
├── requirements.txt      # Project dependencies
├── samples/             # Sample input files
│   ├── emails/          # Sample email files
│   └── json/           # Sample JSON files
├── docs/               # Documentation
│   └── screenshots/    # Application screenshots
└── tests/             # Test files
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/document-processing-system.git
cd document-processing-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Access the application at `http://localhost:8501`

3. Process documents:
   - Upload files (PDF, JSON, TXT, EML)
   - Enter email text directly
   - View processing results and history

## Sample Files

### Email Example
```text
From: john.doe@abctech.com
To: team@abctech.com
Subject: Immediate Action Needed: Project Update
Date: March 20, 2024

Hi Team,

This is urgent. Please address the following immediately:
...
```

### JSON Example
```json
{
    "project": "Website Redesign",
    "status": "In Progress",
    "team": ["John", "Alice", "Bob"],
    "deadline": "2024-04-01"
}
```

## Processing Flow

1. Document received
2. Classifier detects format and intent
3. Document routed to appropriate agent
4. Results stored in shared memory
5. History updated in real-time

## Memory Tracking

The system maintains a processing history that includes:
- Source agent
- Processing type
- Timestamp
- Thread ID (for linked operations)
- Extracted values

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
# Real-Time CSV Processing with Pathway and Gemini AI

**Author:** Akshat Rai  
**Admission Number:** 24JE0728  
**Institution:** IIT (ISM) Dhanbad  
**Application:** Pathway Problem Statement - Inter IIT Tech Meet 14.0

---

## Overview

This project demonstrates a real-time streaming data pipeline that integrates **Pathway**, **Google Drive**, and **Google Gemini AI** to process CSV data and generate AI-powered summaries. The solution showcases seamless streaming capabilities, automated data decoding, and intelligent content summarization in a production-ready architecture.

### Key Features

- **Real-time Streaming**: Continuously monitors Google Drive for new CSV files using Pathway's streaming mode
- **Automatic Data Decoding**: Converts binary data from Google Drive into readable CSV format
- **AI-Powered Summarization**: Leverages Google Gemini API to generate intelligent summaries of CSV content
- **Persistent Storage**: Writes summaries to local CSV files with full streaming metadata
- **Error Handling**: Robust exception handling for network issues, API failures, and data corruption

---

## Architecture

```
Google Drive (Source)
        ↓
   Pathway Streaming
        ↓
   Decode Bytes → CSV Text
        ↓
   Gemini AI Summarization
        ↓
   CSV Output (gemini_summary.csv)
```

The pipeline operates in streaming mode, meaning it processes new data incrementally as it arrives on Google Drive, rather than performing batch operations on static data.

---

## Prerequisites

- **Linux/macOS/WSL**
- **Python 3.10+**
- **Virtual Environment** (venv)
- **Google Drive API credentials** (service account)
- **Google Gemini API key**

---

## Setup Instructions

### 1. Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Google Drive API Setup

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable the **Google Drive API**
- Create a **Service Account** and download the JSON credentials file
- Save the credentials file as `credentials.json` in your project directory
- Share the target Google Drive folder with the service account email

### 4. Google Gemini API Setup

- Visit [Google AI Studio](https://aistudio.google.com)
- Create an API key for Gemini access
- Create a `.env` file in your project directory:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Never commit `.env` file to version control!**

### 5. Configure the Script

In `main.py`, replace the `object_id` with your Google Drive folder ID:

```python
gdrive_table = pw.io.gdrive.read(
    object_id="YOUR_FOLDER_ID_HERE",  # Replace with your folder ID
    service_user_credentials_file="credentials.json",
    mode="streaming"
)
```

To find your folder ID, open the folder in Google Drive and copy the ID from the URL: `https://drive.google.com/drive/folders/{FOLDER_ID}`

---

## Project Structure

```
.
├── main.py                    # Main streaming pipeline
├── requirements.txt           # Python dependencies
├── credentials.json           # Google Drive API credentials (gitignore)
├── .env                       # Environment variables (gitignore)
├── .gitignore                 # Git ignore file
├── README.md                  # This file
└── gemini_summary.csv         # Output file (generated at runtime)
```

---

## How It Works

### 1. **Data Ingestion** (`pw.io.gdrive.read`)
The pipeline connects to Google Drive in streaming mode, continuously monitoring for new or updated CSV files.

### 2. **Data Decoding** (`decode_bytes_to_text`)
Binary data from Google Drive is converted to readable UTF-8 text. The UDF handles encoding errors gracefully.

### 3. **AI Summarization** (`get_gemini_summary`)
Each decoded CSV text is sent to Google Gemini API with a summarization prompt. The UDF:
- Constructs the API request with proper headers and payload
- Sends the CSV content to `gemini-2.5-flash` model
- Extracts the generated summary from the API response
- Handles HTTP errors and exceptions

### 4. **Output Storage** (`pw.io.csv.write`)
Summaries are written to `gemini_summary.csv` with Pathway's streaming metadata (timestamp and diff columns).

---

## Running the Application

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run the pipeline
python main.py
```

The script will:
1. Connect to your Google Drive folder
2. Wait for CSV files (or process existing ones in streaming mode)
3. Decode each file's content
4. Generate summaries using Gemini AI
5. Store summaries in `gemini_summary.csv`
6. Continue monitoring for new files in real-time

### Output File Example

**gemini_summary.csv:**
```
"summary_text","time","diff"
"This CSV contains sales data from Q3 2025 with 150 transactions totaling $45,000 in revenue across 5 regions...","1761219939474","1"
"Employee attendance records for October 2025 showing 95% average attendance across 50 staff members with detailed daily logs...","1761219945162","1"
```

---

## Requirements File

The `requirements.txt` includes:
- **pathway**: Real-time streaming data processing
- **requests**: HTTP library for Gemini API calls
- **python-dotenv**: Environment variable management
- **google-auth-httplib2**: Google authentication
- **google-api-python-client**: Google Drive API client

---

## Key Design Decisions

### Why Pathway?
- Native support for streaming data sources without batch reprocessing
- Efficient incremental computation
- Built-in connectors for Google Drive and CSV output
- Python UDF support for custom transformations

### Why Gemini API?
- State-of-the-art LLM for content understanding and summarization
- Fast inference with `gemini-2.5-flash` model
- Simple REST API integration
- Cost-effective for batch summarization tasks

### Streaming vs. Batch
This implementation uses streaming mode because:
- New CSV files are continuously added to Google Drive
- Each file should be processed immediately upon arrival
- Results should be accumulated in real-time
- Avoids redundant reprocessing of old data

---

## Error Handling

The pipeline handles multiple failure modes:

| Error Type | Handling |
|---|---|
| Decode Error | Returns empty string, continues processing |
| API 401 | Indicates authentication failure (check API key) |
| Network Timeout | Captured by exception handler |
| No Candidates | Returns "No summary generated" |
| Malformed CSV | Processed as-is; Gemini handles gracefully |

---

## Performance Considerations

- **Import Time**: Pathway takes a few seconds to initialize depending on your hardware (see console output)
- **API Latency**: Gemini summarization takes 1-3 seconds per request
- **Throughput**: Can process multiple CSV files concurrently if available
- **Storage**: Output CSV grows linearly with number of summaries
- **Memory**: Streaming mode maintains only active records in memory

---

## Future Enhancements

- Add filtering to process only CSV files above a certain size
- Implement custom summarization prompts for domain-specific data
- Cache summaries to avoid duplicate processing
- Add support for other output formats (JSON, Parquet)
- Integrate with cloud storage (GCS) for scalability
- Implement retry logic with exponential backoff for API failures
- Add logging framework for better debugging
- Support for batch processing with configurable batch size

---

## References

- [Pathway Documentation](https://pathway.com/developers)
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [Google Drive API](https://developers.google.com/drive/api)
- [Inter IIT Tech Meet 14.0](https://www.interiit-tech.in/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

---

**Contact:** [Akshat Rai](24je0728@iitism.ac.in) (24JE0728) - IIT (ISM) Dhanbad

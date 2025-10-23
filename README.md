# Real-Time CSV Processing with Pathway and Gemini AI

**Author:** Akshat Rai  
**Admission Number:** 24JE0728  
**Institution:** IIT (ISM) Dhanbad  
**Application:** Pathway Problem Statement - Inter IIT Tech Meet 14.0

---

## Overview

This project implements a **real-time streaming pipeline** with a robust **agentic architecture** that integrates **Pathway**, **Google Drive**, and **Google Gemini AI**. Beyond simple CSV ingestion and summarization, it employs a structured **ReAct-inspired agent loop** and **async UDF execution** to orchestrate tool calls, dynamic prompt engineering, and concurrent processing—ensuring scalable, reliable, and context-aware insights from streaming data.

## Key Features

- **Agentic Processing Loop**: Implements a ReAct pattern where the agent reasons, decides on tool usage (`analyze_csv_data`, `filter_data`), executes them, and synthesizes final analysis.
- **Async UDF Executor**: Uses Pathway’s async UDF with a thread pool to offload blocking LLM calls, maintaining stream throughput.
- **Structured Prompt Engineering**: Forces the LLM to output concrete sections (Summary, Distribution, Top Performers, Patterns, Outliers, Recommendations) without follow-ups.
- **Streaming \& Incremental Updates**: Pathway streams new CSV files and only reprocesses changed data, preserving resource efficiency.
- **Resilient Tool Integration**: Custom CSV-analysis tools drive precise agent actions before synthesizing combined insights.

---

## Architecture

```mermaid
flowchart LR
  A[Google Drive (streaming source)] --> B[Pathway Streaming Engine]
  B --> C[decode_bytes_to_text UDF] 
  C --> D[Agentic Loop UDF (process_with_agent)]
  D -->|Tool Call: analyze_csv_data| E[analyze_csv_data]
  D -->|Tool Call: filter_data| F[filter_data]
  E & F --> D
  D --> G[Gemini AI Summarization]
  G --> H[pw.io.csv.write → gemini_summary.csv]
```

1. **Pathway Streaming Engine**
Continuously ingests binary files from Google Drive with incremental checkpoints.
2. **Data Decoding UDF**
Transforms raw bytes into UTF-8 CSV text, handling errors gracefully.
3. **Agentic Loop UDF**
    - **Reason**: Builds a comprehensive prompt including analysis directives.
    - **Act**: Invokes custom tools (`analyze_csv_data`, `filter_data`) based on data needs.
    - **Observe**: Receives tool outputs as structured messages.
    - **Synthesize**: Compiles final agent response, enforcing sections (Summary, etc.).
4. **Async Execution**
Runs the agentic loop in a `ThreadPoolExecutor` via Pathway’s async UDF executor to prevent blocking the streaming pipeline.
5. **Gemini AI Summarization**
Final combined prompt is sent to the `gemini-2.5-flash` model for natural-language analysis.
6. **Output Storage**
Persists each analysis into `gemini_summary.csv` with Pathway metadata (`time`, `diff`).

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

1. **Ingestion** (`pw.io.gdrive.read`)
Streams CSV files from Drive as binary.
2. **Decoding** (`decode_bytes_to_text` UDF)
Decodes bytes→UTF-8 text, handling errors.
3. **Summarization** (`process_with_agent` async UDF)
     - Builds a strict prompt directing the LLM to provide:
       - **SUMMARY**
       - **GRADE DISTRIBUTION**
       - **TOP PERFORMERS**
       - **PERFORMANCE PATTERNS**
       - **OUTLIERS**
       - **RECOMMENDATIONS**
    - Executes in a thread pool to avoid blocking.
    - Enforced `timeout=3000.0` seconds to accommodate large analyses.
4. **Output** (`pw.io.csv.write`)
Appends each analysis to `gemini_summary.csv` with Pathway’s `time` and `diff`.

---

## Running the Application

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Run the pipeline
python main.py
```

The pipeline will:

1. Connect to your Drive folder in streaming mode.
2. Decode and analyze each CSV with Gemini AI.
3. Write structured insights to `gemini_summary.csv`.
4. Continue monitoring for new files in real time.

## Output Example

```csv
"agent_response","time","diff"
"SUMMARY: 134 rows, 11 columns…  
GRADE DISTRIBUTION: Quiz 1 avg 6.8, min 2, max 10, std 1.8;…  
TOP PERFORMERS: ADM. No. 0021 (Total 295), ADM. No. 0107 (Total 292);  
PERFORMANCE PATTERNS: Strong correlation (0.78) between Quiz 2 and End Sem;  
OUTLIERS: ADM. No. 0450 scored 5 on Quiz 1 but 48 on End Sem;  
RECOMMENDATIONS: Offer targeted support for low quiz scorers.","1761234567890","1"
```
(The output of my run is given in gemini_summary.csv)

---

## Key Design Decisions

### Why Pathway?
- Native support for streaming data sources without batch reprocessing
- Efficient incremental computation
- Built-in connectors for Google Drive and CSV output
- Python UDF support for custom transformations

### Why Gemini API?
- State-of-the-art (and free) LLM for content understanding and summarization
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

## Performance Considerations

- **Import Time**: Pathway takes a few seconds to initialize depending on your hardware (see console output)
- **API Latency**: Gemini summarization takes a few seconds seconds per request
- **Throughput**: Can process multiple CSV files concurrently if available
- **Storage**: Output CSV grows linearly with number of summaries
- **Memory**: Streaming mode maintains only active records in memory

---

## Future Enhancements

- Extend agent with additional tools (e.g., outlier detection).
- Introduce multi-agent coordination for complex pipelines.
- Integrate caching of tool outputs to optimize repeated analyses.
- Add detailed metrics collection within the agent loop for observability.

---

## References

- [Pathway Documentation](https://pathway.com/developers)
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [Google Drive API](https://developers.google.com/drive/api)
- [Inter IIT Tech Meet 14.0](https://www.interiit-tech.in/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

---

**Contact:** [Akshat Rai](24je0728@iitism.ac.in) (24JE0728) - IIT (ISM) Dhanbad

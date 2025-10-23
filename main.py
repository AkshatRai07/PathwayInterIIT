from dotenv import load_dotenv
load_dotenv()
import os
import requests
import time

start = time.time()
import pathway as pw
end = time.time()
print(f"Took {end-start} sec to import pathway\nStarting streaming...")

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class InputSchema(pw.Schema):
    name: str
    value: int
    timestamp: str

gdrive_table = pw.io.gdrive.read(
    object_id="19DMQzidCyVGkXVUUyJM8j4jtgCSgRr9D", ## Replace this with your Folder ID
    service_user_credentials_file="credentials.json",
    mode="streaming"
)

@pw.udf
def decode_bytes_to_text(data: bytes) -> str:
    try:
        return data.decode('utf-8')
    except Exception as e:
        print(f"Decode error: {e}")
        return ""

decoded_csv_table = gdrive_table.select(
    decoded_text = decode_bytes_to_text(gdrive_table.data)
)

@pw.udf
def get_gemini_summary(csv_text: str) -> str:
    if not csv_text.strip():
        return ""
    headers = {
        "x-goog-api-key": gemini_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Summarize this CSV data: {csv_text}"
                    }
                ]
            }
        ]
    }
    try:
        response = requests.post(gemini_endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            # Extract from the correct nested path
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            return "No summary generated"
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {e}"

summary_table = decoded_csv_table.select(
    summary_text = get_gemini_summary(decoded_csv_table.decoded_text)
)

pw.io.csv.write(summary_table, "gemini_summary.csv")

pw.run()

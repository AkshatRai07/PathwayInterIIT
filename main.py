import pathway as pw
import csv
import io

class InputSchema(pw.Schema):
    name: str
    value: int
    timestamp: str

gdrive_table = pw.io.gdrive.read(
    object_id="19DMQzidCyVGkXVUUyJM8j4jtgCSgRr9D",
    service_user_credentials_file="credentials.json",
    mode="streaming"
)

pw.io.jsonlines.write(gdrive_table, "gdrive_raw_output.jsonl")

# @pw.udf
# def parse_csv_to_rows(data: bytes) -> pw.Table[InputSchema]:
#     """
#     Parse CSV binary data and return a Pathway table (pw.Table) 
#     containing all rows from the CSV.
#     """
#     try:
#         csv_text = data.decode('utf-8')
#         reader = csv.DictReader(io.StringIO(csv_text))
        
#         rows = []
#         for row in reader:
#             rows.append(InputSchema(
#                 name=row.get('name', ''),
#                 value=int(row.get('value', 0)),
#                 timestamp=row.get('timestamp', '')
#             ))

#         return pw.Table.from_list(rows)
    
#     except Exception as e:
#         print(f"Parse error: {e}")
#         return pw.Table.from_list([])

# parsed_table = gdrive_table.flat_map(parse_csv_to_rows)

# result = parsed_table.groupby().reduce(
#     total=pw.reducers.sum(parsed_table.value),
#     count=pw.reducers.count()
# )

# pw.io.jsonlines.write(result, "gdrive_output.jsonl")
# pw.io.csv.write(result, "gdrive_output.csv")

@pw.udf
def decode_bytes_to_text(data: bytes) -> str:
    """
    This function *only* decodes the raw bytes into a human-readable
    text string. This is the "conversion" you're asking about.
    """
    try:
        # This is the exact conversion from bytes to text
        return data.decode('utf-8')
    except Exception as e:
        print(f"Decode error: {e}")
        return "" # Return empty string on error

# 1. Create a new table that just has the decoded CSV text
decoded_csv_table = gdrive_table.select(
    decoded_text=decode_bytes_to_text(gdrive_table.data)
)

# 2. Write this human-readable CSV content to a text file.
# A new file will be created for each input CSV, in a folder
# named 'received_csv_content'
pw.io.csv.write(
    decoded_csv_table, 
    "received_csv_content.txt"
)

pw.run()

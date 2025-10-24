from dotenv import load_dotenv
import os
import io
import csv
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import pathway as pw
from typing import Any
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

def _get_string_content(content: Any) -> str:
    """Safely extracts string content from a LangChain message."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_content = ""
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_content = part.get("text", "")
                break
            elif isinstance(part, str):
                text_content = part
                break
        return text_content
    return str(content)

@tool
def analyze_csv_data(csv_text: str, query: str) -> str:
    """
    Analyzes CSV data and extracts key statistics or insights based on the query.

    Args:
        csv_text: The CSV data as a string.
        query: The analysis query (e.g., "summary", "describe columns", "find trends").

    Returns:
        A text summary of the analysis.
    """
    import io, csv, statistics

    if not csv_text.strip():
        return "Error: CSV data is empty."

    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    rows = list(reader)
    headers = reader.fieldnames or []

    if not rows or not headers:
        return "Error: Invalid or empty CSV data."

    numeric_columns = {}
    for h in headers:
        col_values = []
        for row in rows:
            val = row.get(h, "").strip()
            try:
                col_values.append(float(val))
            except ValueError:
                continue
        if len(col_values) > 0:
            numeric_columns[h] = col_values

    query_lower = query.lower().strip()

    if "summary" in query_lower or "overview" in query_lower or query_lower == "":
        summary = [
            f"CSV contains {len(rows)} rows and {len(headers)} columns.",
            f"Columns: {', '.join(headers)}.",
            "",
            "Numeric column statistics:"
        ]
        for h, vals in numeric_columns.items():
            summary.append(
                f"- {h}: mean={statistics.mean(vals):.2f}, "
                f"min={min(vals):.2f}, max={max(vals):.2f}, "
                f"std={statistics.pstdev(vals):.2f}"
            )
        return "\n".join(summary)

    for h in headers:
        if h.lower() in query_lower:
            vals = numeric_columns.get(h)
            if vals:
                return (
                    f"Column '{h}' has {len(vals)} numeric values.\n"
                    f"Mean: {statistics.mean(vals):.2f}\n"
                    f"Min: {min(vals):.2f}\n"
                    f"Max: {max(vals):.2f}\n"
                    f"Std Dev: {statistics.pstdev(vals):.2f}"
                )
            else:
                freq = {}
                for row in rows:
                    val = row.get(h, "").strip()
                    if val:
                        freq[val] = freq.get(val, 0) + 1
                top_vals = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
                return (
                    f"Column '{h}' appears to be categorical.\n"
                    f"Top values:\n" +
                    "\n".join([f"- {v}: {c} occurrences" for v, c in top_vals])
                )

    if "correlation" in query_lower or "trend" in query_lower:
        import numpy as np
        corrs = []
        cols = list(numeric_columns.keys())
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                a, b = numeric_columns[cols[i]], numeric_columns[cols[j]]
                n = min(len(a), len(b))
                if n < 2:
                    continue
                corr = np.corrcoef(a[:n], b[:n])[0, 1]
                corrs.append((cols[i], cols[j], corr))
        if not corrs:
            return "No numeric correlations found."
        corrs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_corrs = "\n".join([f"- {a} ↔ {b}: corr={c:.2f}" for a, b, c in corrs[:5]])
        return f"Top correlations:\n{top_corrs}"

    return (
        f"Sorry, I couldn't interpret the query '{query}'. "
        f"Try asking for 'summary', 'describe <column>', or 'correlation'."
    )

@tool
def filter_data(csv_text: str, column_name: str, operator: str, value: str) -> str:
    """
    Filters CSV data based on a condition.
    
    Args:
        csv_text: The CSV data as a string
        column_name: Column to filter on
        operator: Filtering operator (e.g., '==', '!=', '>', '<', '>=', '<=')
        value: The value to compare against (will be string-compared or float-compared if possible)
    
    Returns:
        Filtered CSV data as a string, including headers, or an error message.
    """
    try:
        f = io.StringIO(csv_text)
        reader = csv.reader(f)
        lines = list(reader)
        
        if not lines:
            return "Error: CSV data is empty."
            
        headers = lines[0]
        
        try:
            col_index = headers.index(column_name)
        except ValueError:
            return f"Error: Column '{column_name}' not found. Available columns: {', '.join(headers)}"

        try_numeric = True
        try:
            compare_value = float(value)
        except ValueError:
            try_numeric = False
            compare_value = value

        op_map = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
        }
        
        if operator not in op_map:
            return f"Error: Invalid operator '{operator}'. Use one of: {', '.join(op_map.keys())}"
        
        op_func = op_map[operator]
        
        filtered_rows = [headers]
        for row in lines[1:]:
            if len(row) <= col_index:
                continue
                
            cell_value_str = row[col_index]
            
            try:
                if try_numeric:
                    cell_value = float(cell_value_str)
                else:
                    cell_value = cell_value_str
                
                if op_func(cell_value, compare_value):
                    filtered_rows.append(row)
                    
            except (ValueError, TypeError):
                if not try_numeric and op_func(cell_value_str, compare_value):
                     filtered_rows.append(row)
                
        if len(filtered_rows) == 1:
            return f"Filtered data for {column_name} {operator} {value}: No matching rows found."

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(filtered_rows)
        return output.getvalue().strip()

    except Exception as e:
        return f"Error during filtering: {str(e)}"

tools = [analyze_csv_data, filter_data]
llm_with_tools = llm.bind_tools(tools)

def process_tool_calls(tool_calls: list, csv_data: str) -> list:
    """Execute tool calls and return results."""
    results = []
    
    tools_dict = {
        "analyze_csv_data": analyze_csv_data,
        "filter_data": filter_data
    }
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in tools_dict:
            tool_args["csv_text"] = csv_data
        
        try:
            tool_func = tools_dict[tool_name]
            result = tool_func.invoke(tool_args)
            results.append({
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "content": str(result)
            })
        except Exception as e:
            results.append({
                "tool_call_id": tool_call.get("id"),
                "name": tool_name,
                "content": f"Error: {str(e)}"
            })
    
    return results

def run_agentic_loop(user_query: str, csv_data: str, max_iterations: int = 5):
    """
    Main agentic loop that implements ReAct pattern.
    
    The loop continues until:
    1. Model returns a final answer (no tool calls)
    2. Max iterations reached
    """
    print(f"\n{'='*60}")
    print(f"User Query: {user_query}")
    print(f"{'='*60}\n")
    initial_prompt = f"{user_query}\n\nHere is the CSV data to analyze:\n\n{csv_data}"
    messages = [HumanMessage(content=initial_prompt)]
    
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")
        
        response = llm_with_tools.invoke(messages)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"Thought: Model decided to use tools")
            print(f"Tool calls: {[tc['name'] for tc in response.tool_calls]}\n")
            
            tool_results = process_tool_calls(response.tool_calls, csv_data)
            
            messages.append(response)
            
            for tool_result in tool_results:
                tool_message = ToolMessage(
                    content=tool_result["content"],
                    tool_call_id=tool_result["tool_call_id"],
                    name=tool_result["name"]
                )
                messages.append(tool_message)
                print(f"Action: {tool_result['name']}")
                print(f"Observation: {tool_result['content']}\n")
        else:
            final_content = _get_string_content(response.content)
            print(f"Final Answer: {final_content}")
            return final_content
    
    print(f"Max iterations ({max_iterations}) reached")
    
    if messages:
        last_content = _get_string_content(messages[-1].content)
        return last_content
    return "No response"

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

executor = ThreadPoolExecutor(max_workers=4)

@pw.udf(executor=pw.udfs.async_executor(capacity=2, timeout=3000.0))
async def process_with_agent(csv_text: str) -> str:
    """Process CSV using the agentic system with proper async handling."""
    if not csv_text.strip():
        return ""
    
    user_query = f"""You are a data analyst. Analyze the following CSV data and provide CONCRETE insights. 

DO NOT ask for clarification. DO NOT ask what kind of analysis. Just analyze and report.

Use the available tools to analyze this CSV data.
First, call analyze_csv_data to get a summary, then use filter_data if needed, then carry out further analysis if you wish.

CSV Data:
{csv_text}

Provide your analysis in this format:
1. SUMMARY: Basic statistics (row count, columns)
2. GRADE DISTRIBUTION: Average, min, max, and standard deviation for each grading component
3. TOP PERFORMERS: Students with highest total scores
4. PERFORMANCE PATTERNS: Any trends or correlations between different assessments
5. OUTLIERS: Notable scores (unusually high or low)
6. RECOMMENDATIONS: Key observations for instructors

Be specific - use actual numbers and student statistics from the data."""
    
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        executor,
        run_agentic_loop, 
        user_query, 
        csv_text
    )
    return result

result_table = decoded_csv_table.select(
    agent_response=process_with_agent(decoded_csv_table.decoded_text)
)

pw.io.csv.write(result_table, "gemini_summary.csv")

pw.run()

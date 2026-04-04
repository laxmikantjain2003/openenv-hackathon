#  API Debugger Agent - OpenEnv Hackathon Round 1

##  Environment Description
The **API Debugger Agent** is a real-world OpenEnv environment designed to train and evaluate AI agents on backend debugging and API configuration tasks. Instead of playing games, the agent acts as a Senior Backend Engineer. It reads server logs, inspects the current state of a failing API request, and modifies headers, payloads, or URLs to fix the errors.

This environment directly simulates the day-to-day responsibilities of a software engineer, making it highly valuable for evaluating frontier LLMs in practical, developer-oriented scenarios.

---

## Action & Observation Spaces

### **Observation Space**
The environment strictly uses Pydantic models to return the following state to the agent:
- `server_logs` (str): Output from the backend server (e.g., `[ERROR] 401 Unauthorized`).
- `current_request` (dict): The current state of the API request being built (Headers, Payload, URL).
- `last_status_code` (int): The HTTP status code of the previous attempt.
- `task_objective` (str): The specific bug the agent needs to fix.

### **Action Space**
The agent must return a JSON object containing:
- `action_type` (str): Must be `'update_header'`, `'update_payload'`, `'update_url'`, or `'submit'`.
- `key` (str, optional): The dictionary key to update (e.g., 'Authorization', 'age').
- `value` (str, optional): The new correct value to inject.

---

## Task Progression (Agent Graders)
The environment features 3 distinct tasks with increasing real-world difficulty. Graders evaluate the final submitted state and award a score between `0.0` and `1.0`.

1. **Easy: Task 1 (Auth Missing)**
   - **Scenario:** The API returns a `401 Unauthorized`.
   - **Goal:** The agent must add the correct `'Authorization'` header with the required Bearer token.
2. **Medium: Task 2 (Malformed Payload)**
   - **Scenario:** The API returns a `400 Bad Request` due to a type validation error (a string passed where an integer was expected).
   - **Goal:** The agent must update the payload field `'age'` to a valid integer.
3. **Hard: Task 3 (SQL Injection / Bad Query)**
   - **Scenario:** The API returns a `500 Internal Server Error` because of a dangerous SQL query in the URL parameters.
   - **Goal:** The agent must rewrite the URL to remove the SQL injection vulnerability and pass a safe query.

---

##  Setup & Usage Instructions

### **1. Local Execution**
Make sure you have Python 3.10+ installed.

```bash
# Install dependencies
pip install pydantic openai

# Set your API keys (Replace with your actual keys)
export API_BASE_URL="[https://api.openai.com/v1](https://api.openai.com/v1)"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-hf-or-openai-key-here"

# Run the inference script
python inference.py

# Build the Docker image
docker build -t api-debugger-env .

# Run the Docker container
docker run -e API_BASE_URL="..." -e MODEL_NAME="..." -e HF_TOKEN="..." api-debugger-env
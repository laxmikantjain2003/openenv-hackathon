from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Action(BaseModel):
    action_type: str = Field(description="Type of action: 'update_header', 'update_payload', 'update_url', or 'submit'")
    key: Optional[str] = Field(default=None, description="Key to update in header or payload (e.g., 'Authorization' or 'age')")
    value: Optional[str] = Field(default=None, description="New value for the key, or the new URL string")

class Observation(BaseModel):
    server_logs: str = Field(description="Recent logs from the backend server showing errors or success.")
    current_request: Dict[str, Any] = Field(description="Current state of the API request being built.")
    last_status_code: int = Field(description="HTTP status code of the last attempt.")
    task_objective: str = Field(description="Instruction on what the agent needs to fix.")

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]

class ApiDebuggerEnv:
    def __init__(self):
        self.current_task = None
        self.request_state = {}
        self.step_count = 0
        self.max_steps = 10
        self.last_status = 0
        
    def reset(self, task_id: str = "task_1_easy_auth") -> Observation:
        """Starts a new task and returns the initial broken state."""
        self.current_task = task_id
        self.step_count = 0
        
        if task_id == "task_1_easy_auth":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/secure-data"}
            logs = "[ERROR] 401 Unauthorized: Missing or invalid Authorization token."
            objective = "Fix the 401 error. Add an 'Authorization' header with value 'Bearer secret_token'."
            self.last_status = 401
            
        elif task_id == "task_2_medium_payload":
            self.request_state = {
                "headers": {"Content-Type": "application/json"}, 
                "payload": {"username": "admin", "age": "twenty_five"}, # Intentional Bug
                "url": "/api/users"
            }
            logs = "[ERROR] 400 Bad Request: Validation failed for field 'age'. Expected integer."
            objective = "Fix the 400 error by updating the 'age' field in the payload to a valid integer (e.g., 25)."
            self.last_status = 400
            
        elif task_id == "task_3_hard_db_query":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/search?query=SELECT*FROM_USERS"}
            logs = "[FATAL] 500 Internal Server Error: SQL Syntax Error near 'SELECT*FROM'."
            objective = "Fix the 500 error by changing the URL to remove the SQL injection. Use a safe query like '/api/search?query=safe_test'."
            self.last_status = 500
        else:
            raise ValueError(f"Unknown task_id: {task_id}")

        return self._get_obs(logs)

    def state(self) -> Observation:
        """Returns the current state of the environment."""
        return self._get_obs("Current state retrieved via state() call.")

    def _get_obs(self, logs: str) -> Observation:
        """Helper to generate standard Observation model."""
        return Observation(
            server_logs=logs,
            current_request=self.request_state,
            last_status_code=self.last_status,
            task_objective=self.current_task
        )

    def step(self, action: Action) -> StepResult:
        """Applies agent's action, updates state, and calculates partial rewards."""
        self.step_count += 1
        logs = "[INFO] Action applied."
        reward = 0.0
        done = False
        
        # --- ACTION LOGIC ---
        if action.action_type == "update_header" and action.key:
            self.request_state["headers"][action.key] = action.value
            logs = f"[INFO] Header '{action.key}' updated to '{action.value}'."
            reward = 0.1  # Partial reward for attempting to fix
            
        elif action.action_type == "update_payload" and action.key:
            self.request_state["payload"][action.key] = action.value
            logs = f"[INFO] Payload field '{action.key}' updated to '{action.value}'."
            reward = 0.1  # Partial reward
            
        elif action.action_type == "update_url" and action.value:
            self.request_state["url"] = action.value
            logs = f"[INFO] URL updated to '{action.value}'."
            reward = 0.1  # Partial reward
            
        elif action.action_type == "submit":
            return self._evaluate_submission()
            
        else:
            logs = "[WARNING] Invalid action format or missing key/value."
            reward = -0.1 # Penalty for bad action syntax

        # Check max steps (prevent infinite loops)
        if self.step_count >= self.max_steps:
            done = True
            logs += " [SYSTEM] Max steps reached. Terminating episode."

        return StepResult(
            observation=self._get_obs(logs),
            reward=reward,
            done=done,
            info={"step": self.step_count}
        )

    def _evaluate_submission(self) -> StepResult:
        """GRADER: Checks if the problem is perfectly fixed when agent clicks submit."""
        done = True
        reward = 0.0
        logs = ""
        
        if self.current_task == "task_1_easy_auth":
            auth_header = self.request_state["headers"].get("Authorization", "")
            if auth_header == "Bearer secret_token":
                self.last_status = 200
                reward = 1.0 # 100% Correct
                logs = "[SUCCESS] 200 OK: Authentication successful."
            else:
                self.last_status = 401
                reward = 0.0
                logs = "[ERROR] 401 Unauthorized: Authorization header missing or incorrect."

        elif self.current_task == "task_2_medium_payload":
            age = self.request_state["payload"].get("age")
            try:
                # Check if age can be converted to integer
                int_age = int(age)
                self.last_status = 200
                reward = 1.0 # 100% Correct
                logs = "[SUCCESS] 200 OK: Payload validation passed."
            except (ValueError, TypeError):
                self.last_status = 400
                reward = 0.2 # Small reward for submitting, but failed validation
                logs = f"[ERROR] 400 Bad Request: 'age' ({age}) is still not an integer."

        elif self.current_task == "task_3_hard_db_query":
            url = self.request_state.get("url", "")
            # Check if SQL injection keywords are removed
            if "SELECT" not in url.upper() and url.startswith("/api/search?query=") and len(url) > 18:
                self.last_status = 200
                reward = 1.0 # 100% Correct
                logs = "[SUCCESS] 200 OK: Safe database query executed."
            else:
                self.last_status = 500
                reward = 0.0
                logs = "[FATAL] 500 Internal Server Error: Unsafe query detected."

        return StepResult(
            observation=self._get_obs(logs),
            reward=reward,
            done=done,
            info={"step": self.step_count, "final_eval": True}
        )
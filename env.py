from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Action(BaseModel):
    action_type: str = Field(description="Action type: 'update_header', 'update_payload', 'update_url', or 'submit'")
    key: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)

class Observation(BaseModel):
    server_logs: str = Field(description="Logs")
    current_request: Dict[str, Any] = Field(description="Request")
    last_status_code: int = Field(description="Status")
    task_objective: str = Field(description="Objective")

class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]

class ApiDebuggerEnv:
    def __init__(self):
        self.current_task = "task_1_easy_auth"
        self.request_state = {}
        self.step_count = 0
        self.max_steps = 10
        self.last_status = 0
        self.max_score_achieved = 0.0
        self.is_done = False

    def reset(self, task_id: str = "task_1_easy_auth") -> Observation:
        self.current_task = task_id
        self.step_count = 0
        self.last_status = 0
        self.max_score_achieved = 0.0
        self.is_done = False
        
        if task_id == "task_1_easy_auth":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/secure-data"}
            self.last_status = 401
        elif task_id == "task_2_medium_payload":
            self.request_state = {"headers": {"Content-Type": "application/json"}, "payload": {"username": "admin", "age": "twenty_five"}, "url": "/api/users"}
            self.last_status = 400
        elif task_id == "task_3_hard_db_query":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/search?query=SELECT*FROM_USERS"}
            self.last_status = 500
            
        return self._get_obs("Environment reset.")

    def _get_obs(self, logs: str) -> Observation:
        return Observation(
            server_logs=logs, 
            current_request=self.request_state, 
            last_status_code=self.last_status, 
            task_objective=str(self.current_task)
        )

    def _get_state_score(self) -> float:
        """Evaluates the current state and returns a base score (0.0 to 0.45)"""
        score = 0.0
        if self.current_task == "task_1_easy_auth":
            val = self.request_state.get("headers", {}).get("Authorization", "")
            if val == "Bearer secret_token": score = 0.45
            elif val != "": score = 0.10
        elif self.current_task == "task_2_medium_payload":
            age = self.request_state.get("payload", {}).get("age", "")
            try:
                int(age)
                score = 0.45
            except:
                if age != "twenty_five" and age != "": score = 0.10
        elif self.current_task == "task_3_hard_db_query":
            url = self.request_state.get("url", "")
            if "SELECT" not in url.upper() and "safe" in url.lower(): score = 0.45
            elif url != "/api/search?query=SELECT*FROM_USERS" and url != "": score = 0.10
        return score

    def step(self, action: Action) -> StepResult:
        if self.is_done:
            return StepResult(observation=self._get_obs("Already done."), reward=0.0, done=True, info={"step": self.step_count})

        self.step_count += 1
        done = False
        logs = "Action applied."
        
        # Apply the action
        if action.action_type == "update_header" and action.key:
            self.request_state.setdefault("headers", {})[action.key] = action.value
        elif action.action_type == "update_payload" and action.key:
            self.request_state.setdefault("payload", {})[action.key] = action.value
        elif action.action_type == "update_url" and action.value:
            self.request_state["url"] = action.value
        elif action.action_type == "submit":
            done = True

        if self.step_count >= self.max_steps:
            done = True

        new_score = self._get_state_score()
        reward = 0.0
        
        # Only give reward if they reached a HIGHER milestone
        if new_score > self.max_score_achieved:
            reward = round(new_score - self.max_score_achieved, 4)
            self.max_score_achieved = new_score

        # Final Submit Logic (Guarantees sum is strictly > 0.0 and < 1.0)
        if done:
            self.is_done = True
            if self.max_score_achieved >= 0.45:
                reward = round(reward + 0.50, 4)  # Perfect Success -> Total 0.95
            elif self.max_score_achieved > 0.0:
                reward = round(reward + 0.10, 4)  # Partial Success -> Total 0.20
            else:
                reward = round(reward + 0.05, 4)  # Complete Fail -> Total 0.05

        return StepResult(
            observation=self._get_obs(logs), 
            reward=reward, 
            done=done, 
            info={"step": self.step_count, "score": round(self.max_score_achieved + (0.50 if done and self.max_score_achieved>=0.45 else 0), 4)}
        )

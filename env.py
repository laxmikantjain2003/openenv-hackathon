from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Action(BaseModel):
    action_type: str = Field(description="Action type")
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
        self.current_task = None
        self.request_state = {}
        self.step_count = 0
        self.max_steps = 10
        self.last_status = 0
        
    def reset(self, task_id: str = "task_1_easy_auth") -> Observation:
        self.current_task = task_id
        self.step_count = 0
        if task_id == "task_1_easy_auth":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/secure-data"}
        elif task_id == "task_2_medium_payload":
            self.request_state = {"headers": {"Content-Type": "application/json"}, "payload": {"username": "admin", "age": "twenty_five"}, "url": "/api/users"}
        elif task_id == "task_3_hard_db_query":
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/search?query=SELECT*FROM_USERS"}
        return self._get_obs("Reset")

    def _get_obs(self, logs: str) -> Observation:
        return Observation(server_logs=logs, current_request=self.request_state, last_status_code=self.last_status, task_objective=str(self.current_task))

    def step(self, action: Action) -> StepResult:
        self.step_count += 1
        reward = 0.01  # Score fix: Never exactly 0
        done = False
        
        if action.action_type == "update_header" and action.key:
            self.request_state["headers"][action.key] = action.value
            reward = 0.1  
        elif action.action_type == "update_payload" and action.key:
            self.request_state["payload"][action.key] = action.value
            reward = 0.1  
        elif action.action_type == "update_url" and action.value:
            self.request_state["url"] = action.value
            reward = 0.1  
        elif action.action_type == "submit":
            return self._evaluate_submission()
            
        if self.step_count >= self.max_steps:
            done = True
            
        return StepResult(observation=self._get_obs("Action applied"), reward=reward, done=done, info={"step": self.step_count})

    def _evaluate_submission(self) -> StepResult:
        done = True
        reward = 0.01 
        
        if self.current_task == "task_1_easy_auth":
            if self.request_state.get("headers", {}).get("Authorization") == "Bearer secret_token":
                reward = 0.99 # Score fix: Never exactly 1.0
        elif self.current_task == "task_2_medium_payload":
            age = self.request_state.get("payload", {}).get("age")
            try:
                int(age)
                reward = 0.99
            except:
                pass
        elif self.current_task == "task_3_hard_db_query":
            url = self.request_state.get("url", "")
            if "SELECT" not in url.upper() and "safe_test" in url:
                reward = 0.99
                
        return StepResult(observation=self._get_obs("Evaluated"), reward=reward, done=done, info={"step": self.step_count, "final_eval": True})
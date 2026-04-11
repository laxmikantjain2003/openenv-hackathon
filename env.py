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

    def reset(self, task_id: str = "task_1_easy_auth") -> Observation:
        self.current_task = task_id
        self.step_count = 0
        self.last_status = 0
        
        if "auth" in task_id:
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/secure-data"}
            self.last_status = 401
        elif "payload" in task_id:
            self.request_state = {"headers": {"Content-Type": "application/json"}, "payload": {"username": "admin", "age": "twenty_five"}, "url": "/api/users"}
            self.last_status = 400
        else:
            self.request_state = {"headers": {}, "payload": {}, "url": "/api/search?query=SELECT*FROM_USERS"}
            self.last_status = 500
            
        return self._get_obs("Environment reset.")

    #  FIX: Added the mandatory state() method 
    def state(self) -> Observation:
        return self._get_obs("State requested.")

    def _get_obs(self, logs: str) -> Observation:
        return Observation(
            server_logs=logs, 
            current_request=self.request_state, 
            last_status_code=self.last_status, 
            task_objective=str(self.current_task)
        )

    def step(self, action: Action) -> StepResult:
        self.step_count += 1
        done = False
        logs = "Action applied."
        
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

        #  FIX: Strict rewards. NEVER 0.0 or 1.0.
        reward = 0.05  # Intermediate tiny reward
        
        if done:
            final_score = 0.15 # Baseline failure score
            
            if "auth" in self.current_task:
                val = self.request_state.get("headers", {}).get("Authorization", "")
                if "Bearer" in val: final_score = 0.85
            elif "payload" in self.current_task:
                age = self.request_state.get("payload", {}).get("age", "")
                try:
                    int(age)
                    final_score = 0.85
                except:
                    pass
            else:
                url = self.request_state.get("url", "")
                if "SELECT" not in url.upper() and "=" in url: final_score = 0.85
                
            reward = final_score

        return StepResult(
            observation=self._get_obs(logs), 
            reward=reward, 
            done=done, 
            info={"step": self.step_count, "score": reward}
        )
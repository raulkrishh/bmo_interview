import os
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent.controller import AgentController
from models import TaskRecord, TaskRequest
from storage.json_store import JsonTaskStore

app = FastAPI(
    title="Agentic Task Runner",
    description="Accepts a task, routes it through an AgentController to the right Tool, and returns a structured execution trace.",
    version="1.0.0",
)

# Wide-open CORS is fine for a local coding-challenge app talking to a
# local Vite dev server; a real deployment would restrict this to the
# actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = AgentController()
store = JsonTaskStore(os.environ.get("TASK_STORE_PATH", "data/tasks.json"))

_VALID_ROLES = {"admin", "user"}


def get_current_role(x_role: str = Header(default="user")) -> str:
    if x_role not in _VALID_ROLES:
        raise HTTPException(status_code=403, detail=f"Invalid role '{x_role}'. Must be one of: {sorted(_VALID_ROLES)}")
    return x_role


def require_admin(role: str = Depends(get_current_role)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tools")
def list_tools():
    return [{"name": t.name, "description": t.description} for t in agent.tools]


@app.post("/api/tasks", response_model=TaskRecord)
def submit_task(payload: TaskRequest, _role: str = Depends(get_current_role)):
    record = agent.run(payload.task)
    return store.add(record)


@app.get("/api/tasks", response_model=List[TaskRecord], dependencies=[Depends(require_admin)])
def get_history():
    return store.list_all()


@app.get("/api/tasks/{task_id}", response_model=TaskRecord, dependencies=[Depends(require_admin)])
def get_task(task_id: str):
    record = store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

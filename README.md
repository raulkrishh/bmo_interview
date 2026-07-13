# Agentic Task Runner

A lightweight full-stack system that accepts a natural-language task, routes it through an
`AgentController` that selects and executes the appropriate `Tool`, and returns a structured
execution trace alongside the final output.

**Stack:** FastAPI (Python) backend + React (Vite) frontend, JSON-file persistence.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node 18+

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

API is live at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm start          # also: npm run dev
```

Opens at `http://localhost:5173`. Talks to the backend at `http://localhost:8000` by default —
override with `VITE_API_BASE=http://your-host npm start` if needed.

### Docker (optional)

```bash
docker compose up --build
```

Frontend on `http://localhost:3000`, backend on `http://localhost:8000`.

### Run the test suite

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

37 tests covering all three tools, agent selection and chaining logic, RBAC, and the API layer.

---

## Architecture

```
Frontend (React)  --HTTP-->  FastAPI app  --calls-->  AgentController  --picks & runs-->  Tool
                                   |                                                        |
                                   +--------------------- JsonTaskStore <-------------------+
                                            (persists every task + trace)
```

### AgentController (`backend/agent/controller.py`)

The core reasoning loop:

1. **Parse** — splits the task on `"then"` / `"and then"` into ordered segments
2. **Select** — iterates the tool list and calls `can_handle()` on each; first match wins
3. **Execute** — runs the matched tool and records every step in a trace
4. **Chain** — pipes the output of one step into the next (see Output Chaining below)
5. **Respond** — returns the final output and the full execution trace

### Tools (`backend/tools/`)

All tools implement `BaseTool` (`can_handle(task) -> bool`, `execute(task) -> ToolResult`).
Adding a new tool means writing one class and appending it to the agent's tool list — no other
code changes.

| Tool | Triggers on | What it does |
|---|---|---|
| `CalculatorTool` | A valid arithmetic expression | Evaluates math safely via Python's `ast` module (no `eval`) |
| `WeatherMockTool` | The word `weather` | Returns a deterministic mock report for the extracted city |
| `TextProcessorTool` | Any text (catch-all) | Applies a text operation; defaults to uppercase if none specified |

**Tool selection order matters.** `CalculatorTool` and `WeatherMockTool` are tried first.
`TextProcessorTool` is last and acts as the fallback for any input neither specific tool claims.

### JsonTaskStore (`backend/storage/json_store.py`)

Appends every processed task (input, output, trace, tools used, timestamp) to
`backend/data/tasks.json`. Writes are lock-protected.

---

## Tool Logic and Input Rules

### CalculatorTool

- Triggers when the input contains a valid arithmetic expression (digits + operators)
- Supports: `+`, `-`, `*`, `/`, `%`, `^` (power), parentheses
- Extracts the expression from natural language — preamble like `"what is"` is ignored
- Trailing operators are stripped before parsing (`"5 + 10 -"` → evaluates `"5 + 10"`)
- Uses Python's `ast` module — only whitelisted numeric operators are permitted, no arbitrary code execution
- Rejects expressions that look like math but are syntactically invalid (e.g. `"100+two"`)

### WeatherMockTool

- Triggers when the input contains the word `weather` (case-insensitive)
- Supports city before or after the keyword: `"weather in Chicago"` and `"Chicago weather"` both work
- Optional prepositions: `in`, `for`, `at`
- Returns a deterministic mock report derived from a hash of the city name — same city always gives the same result, no external API

### TextProcessorTool

- Triggers on any non-empty input that neither Calculator nor Weather handles
- Supported operations: `uppercase`, `lowercase`, `title case`, `capitalize`, `reverse`, `word count`, `character count`, `trim`
- If no operation keyword is found, defaults to **uppercase**
- Target text is resolved in this order: quoted text → text after a colon → text after the keyword

---

## Multi-Step Reasoning and Output Chaining

Tasks can be chained across multiple tools using `"then"` or `"and then"`:

```
"<step 1> then <step 2>"
```

The agent splits the input into segments, routes each to its own tool, and **pipes the output
of each step into the next**. Chaining works in two ways:

**Explicit back-reference** — use `the result`, `the output`, `it`, or `that`:

```
"weather in Chicago then uppercase the result"
"calculate 3 * 7 then reverse the result"
```

**Implicit chaining** — just name the operation; if the prior step produced output and only a
text operation follows, the prior output is used automatically:

```
"weather in Chicago then uppercase"
"calculate 100 / 4 then reverse"
```

The execution trace records a `"Chaining prior output"` step so you can see exactly what was
substituted. When chaining is active, the final output is the last step's result — intermediate
outputs are visible in the trace but not repeated in the answer.

### Example flows

| Input | Tools used | Output |
|---|---|---|
| `3 + 5` | CalculatorTool | `8` |
| `weather in Chicago` | WeatherMockTool | `Chicago: 79°F, Clear, 69% humidity` |
| `hello world` | TextProcessorTool | `HELLO WORLD` |
| `uppercase: hello world` | TextProcessorTool | `HELLO WORLD` |
| `reverse: racecar` | TextProcessorTool | `racecar` |
| `word count: the quick brown fox` | TextProcessorTool | `4` |
| `weather in Toronto then uppercase` | WeatherMockTool → TextProcessorTool | `TORONTO: 58°F, CLOUDY, 52% HUMIDITY` |
| `calculate 6 * 9 then reverse the result` | CalculatorTool → TextProcessorTool | `45` |
| `weather in NYC then word count` | WeatherMockTool → TextProcessorTool | `6` |

---

## RBAC

All API requests require an `x-role` header with one of two values:

| Role | Can do |
|---|---|
| `user` | Submit tasks (`POST /api/tasks`) |
| `admin` | Submit tasks + view history (`GET /api/tasks`, `GET /api/tasks/{id}`) |

Requests with a missing or invalid role default to `user`. Requests to admin-only endpoints without the admin role return `403 Forbidden`.

The frontend exposes a role switcher in the header — toggling to `user` hides the history panel; toggling to `admin` reveals it.

**curl examples:**

```bash
# Submit a task as a user
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "x-role: user" \
  -d '{"task": "3 + 5"}'

# Fetch history as admin
curl http://localhost:8000/api/tasks -H "x-role: admin"

# Fetch history as user — returns 403
curl http://localhost:8000/api/tasks -H "x-role: user"
```

---

## API

| Method | Path | Role required | Description |
|---|---|---|---|
| `POST` | `/api/tasks` | `user` or `admin` | Submit a task; returns output + trace |
| `GET` | `/api/tasks` | `admin` only | List task history, most recent first |
| `GET` | `/api/tasks/{id}` | `admin` only | Fetch a single task record |
| `GET` | `/api/tools` | any | List registered tools and their descriptions |
| `GET` | `/api/health` | any | Health check |

**Example request:**

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "x-role: user" \
  -d '{"task": "weather in Chicago then uppercase"}'
```

**Example response:**

```json
{
  "id": "28c3e644-...",
  "task": "weather in Chicago then uppercase",
  "final_output": "CHICAGO: 79°F, CLEAR, 69% HUMIDITY",
  "steps": [
    {"step_number": 1, "description": "Received input \"weather in Chicago then uppercase\""},
    {"step_number": 2, "description": "Detected 2 sub-tasks: ['weather in Chicago', 'uppercase']"},
    {"step_number": 3, "description": "Selected tool: WeatherMockTool"},
    {"step_number": 4, "description": "Tool result: Chicago: 79°F, Clear, 69% humidity"},
    {"step_number": 5, "description": "Implicitly chaining prior output — resolved segment: \"uppercase: \\\"Chicago: 79°F, Clear, 69% humidity\\\"\""},
    {"step_number": 6, "description": "Selected tool: TextProcessorTool"},
    {"step_number": 7, "description": "Tool result: CHICAGO: 79°F, CLEAR, 69% HUMIDITY"},
    {"step_number": 8, "description": "Returning result to user"}
  ],
  "tools_used": ["WeatherMockTool", "TextProcessorTool"],
  "timestamp": "2026-07-13T15:39:33.026200+00:00",
  "error": null
}
```

---

## Assumptions & Tradeoffs

- **Tool selection is deterministic/rule-based (regex + keyword matching), not an LLM call.**
  Keeps behavior predictable and fully unit-testable without an API key. Mirrors the same
  parse → select → execute → trace loop a real LLM-backed agent would follow. A production
  version would likely swap the router for a LangGraph-style LLM call while keeping the same
  `BaseTool` interface.
- **`TextProcessorTool` is the catch-all.** Any input that isn't math or weather falls to it,
  defaulting to uppercase. This avoids dead-end "no tool matched" failures for plain text.
- **Output chaining is implicit when unambiguous.** If the next segment has no extractable
  target text and only a text operation follows, the prior output is injected automatically —
  no need to say "the result" every time.
- **Multi-step splitting triggers only on `"then"` / `"and then"`**, not every `"and"`, to
  avoid incorrectly splitting single tasks like `"uppercase and reverse"`.
- **JSON-file persistence** rather than SQLite — trivial to inspect by hand, no schema
  overhead for a project this size.
- **CORS is wide open (`*`)** since this runs locally; a real deployment would restrict to the
  actual frontend origin.
- **RBAC uses a header claim (`x-role`) rather than signed tokens.** This is intentionally
  simple — it demonstrates the role-gating pattern without requiring a full auth server. A
  production version would verify a signed JWT and extract the role from its claims.

## What I'd Improve With More Time

- Real-time streaming of execution steps via SSE/WebSocket so the trace fills in live.
- Swap the keyword-based tool selector for an LLM-based router (e.g. LangGraph) with the
  existing tools as callable nodes — the `BaseTool` interface was designed with this swap in mind.
- SQLite instead of the JSON file once concurrent writes matter.
- Pagination on `/api/tasks` once history grows large.
- Deep-linkable `/tasks/:id` route in the frontend.

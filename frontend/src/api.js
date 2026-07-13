const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function handleResponse(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed with status ${response.status}`)
  }
  return response.json()
}

export async function submitTask(task) {
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  })
  return handleResponse(response)
}

export async function fetchHistory() {
  const response = await fetch(`${API_BASE}/api/tasks`)
  return handleResponse(response)
}

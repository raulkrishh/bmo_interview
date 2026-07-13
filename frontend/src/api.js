const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function handleResponse(response) {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed with status ${response.status}`)
  }
  return response.json()
}

function roleHeaders(role) {
  return { 'Content-Type': 'application/json', 'x-role': role }
}

export async function submitTask(task, role) {
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: roleHeaders(role),
    body: JSON.stringify({ task }),
  })
  return handleResponse(response)
}

export async function fetchHistory(role) {
  const response = await fetch(`${API_BASE}/api/tasks`, {
    headers: { 'x-role': role },
  })
  return handleResponse(response)
}

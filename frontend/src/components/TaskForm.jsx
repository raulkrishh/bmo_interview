import { useState } from 'react'

export default function TaskForm({ onSubmit, isLoading }) {
  const [task, setTask] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!task.trim()) return
    onSubmit(task.trim())
    setTask('')
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <input
        type="text"
        value={task}
        onChange={(e) => setTask(e.target.value)}
        placeholder='Try: "3 + 5", "uppercase: hello world", "weather in Chicago"'
        disabled={isLoading}
        aria-label="Task input"
      />
      <button type="submit" disabled={isLoading || !task.trim()}>
        {isLoading ? 'Running…' : 'Submit'}
      </button>
    </form>
  )
}

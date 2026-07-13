import { useEffect, useState } from 'react'
import TaskForm from './components/TaskForm.jsx'
import ResultPanel from './components/ResultPanel.jsx'
import HistoryList from './components/HistoryList.jsx'
import { submitTask, fetchHistory } from './api.js'

export default function App() {
  const [currentResult, setCurrentResult] = useState(null)
  const [history, setHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)

  useEffect(() => {
    loadHistory()
  }, [])

  async function loadHistory() {
    try {
      const data = await fetchHistory()
      setHistory(data)
    } catch (err) {
      setErrorMessage(err.message)
    }
  }

  async function handleSubmit(task) {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const record = await submitTask(task)
      setCurrentResult(record)
      await loadHistory()
    } catch (err) {
      setErrorMessage(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Agentic Task Runner</h1>
        <p className="subtitle">Enter a task. The agent picks a tool, runs it, and shows its reasoning.</p>
      </header>

      <TaskForm onSubmit={handleSubmit} isLoading={isLoading} />
      {errorMessage && <p className="error-banner">{errorMessage}</p>}

      <ResultPanel record={currentResult} />

      <section className="history-section">
        <h2>History</h2>
        <HistoryList history={history} />
      </section>
    </div>
  )
}

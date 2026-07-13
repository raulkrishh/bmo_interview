import ExecutionTrace from './ExecutionTrace.jsx'

export default function ResultPanel({ record }) {
  if (!record) return null

  return (
    <section className="result-panel">
      <h2>Result</h2>
      {record.error && <p className="error-banner">{record.error}</p>}
      <p className="final-output">{record.final_output}</p>
      <div className="meta">
        <span>Tools used: {record.tools_used.length ? record.tools_used.join(', ') : 'none'}</span>
        <span>{new Date(record.timestamp).toLocaleString()}</span>
      </div>
      <details open>
        <summary>Execution steps</summary>
        <ExecutionTrace steps={record.steps} />
      </details>
    </section>
  )
}

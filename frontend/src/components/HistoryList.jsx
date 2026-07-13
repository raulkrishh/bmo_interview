import { useState } from 'react'
import ExecutionTrace from './ExecutionTrace.jsx'

export default function HistoryList({ history }) {
  const [expandedId, setExpandedId] = useState(null)

  if (history.length === 0) {
    return <p className="empty-state">No tasks yet — submit one above to get started.</p>
  }

  return (
    <ul className="history-list">
      {history.map((record) => {
        const isExpanded = expandedId === record.id
        return (
          <li key={record.id} className="history-item">
            <button
              className="history-row"
              onClick={() => setExpandedId(isExpanded ? null : record.id)}
              aria-expanded={isExpanded}
            >
              <span className="history-task">{record.task}</span>
              <span className="history-tools">{record.tools_used.join(', ') || 'no tool matched'}</span>
              <span className="history-time">{new Date(record.timestamp).toLocaleTimeString()}</span>
            </button>
            {isExpanded && (
              <div className="history-details">
                <p className="final-output">{record.final_output}</p>
                <ExecutionTrace steps={record.steps} />
              </div>
            )}
          </li>
        )
      })}
    </ul>
  )
}

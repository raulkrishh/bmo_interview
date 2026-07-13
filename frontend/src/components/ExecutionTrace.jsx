export default function ExecutionTrace({ steps }) {
  if (!steps || steps.length === 0) return null

  return (
    <ol className="trace-list">
      {steps.map((step) => (
        <li key={step.step_number}>
          <span className="trace-index">Step {step.step_number}</span>
          <span className="trace-description">{step.description}</span>
        </li>
      ))}
    </ol>
  )
}

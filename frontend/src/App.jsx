import { useState } from 'react'

const fields = [
  ['Supplier', 'Supplier', 'Alpha_Inc'],
  ['Item_Category', 'Item category', 'Electronics'],
  ['Quantity', 'Quantity', '10', true],
  ['Unit_Price', 'Unit price', '100', true],
  ['Negotiated_Price', 'Negotiated price', '90', true],
]

export default function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function analyze(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const order = Object.fromEntries(
      fields.map(([key, , , numeric]) => [
        key,
        numeric ? Number(form.get(key)) : form.get(key).trim(),
      ]),
    )

    setBusy(true)
    setResult(null)
    setError('')

    try {
      const response = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      })

      if (response.status === 422) {
        setError('Enter a supplier and category, and use positive numbers for quantity and prices.')
        return
      }
      if (!response.ok) throw new Error('Prediction request failed')
      setResult(await response.json())
    } catch {
      setError('Could not analyze the order. Check that FastAPI is running on port 8000.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main style={{ maxWidth: 680, margin: '2rem auto', padding: '0 1rem', textAlign: 'left' }}>
      <h1>ProcureSight AI</h1>
      <p>Screen a purchase order for compliance risk and unusual purchasing patterns.</p>

      <form onSubmit={analyze} style={{ display: 'grid', gap: '0.75rem' }}>
        {fields.map(([key, label, value, numeric]) => (
          <label key={key} style={{ display: 'grid', gap: '0.25rem' }}>
            {label}
            <input
              name={key}
              type={numeric ? 'number' : 'text'}
              min={numeric ? 0 : undefined}
              step={numeric ? 'any' : undefined}
              defaultValue={value}
              required
            />
          </label>
        ))}
        <button type="submit" disabled={busy}>
          {busy ? 'Analyzing…' : 'Analyze order'}
        </button>
      </form>

      {error && <p role="alert">{error}</p>}

      {result && (
        <section aria-label="Review results" aria-live="polite">
          <h2>Review results</h2>
          <p>
            <strong>Compliance risk:</strong> {result.compliance.risk_score.toFixed(4)}
            {' · '}{result.compliance.review_flag ? 'Flagged for review' : 'Not flagged'}
          </p>
          <p>
            <strong>Anomaly score:</strong> {result.anomaly.score.toFixed(4)}
            {' · '}{result.anomaly.review_flag ? 'Flagged for review' : 'Not flagged'}
          </p>
          <p>Flags help prioritize human review. The anomaly score measures unusualness.</p>
        </section>
      )}
    </main>
  )
}
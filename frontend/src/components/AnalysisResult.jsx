export default function AnalysisResult({ result }) {
  if (!result) return null
  const prediction = result.prediction
  const confidence = typeof result.confidence === 'number' ? Math.round(result.confidence * 100) : null
  const uncertain = typeof result.confidence === 'number' && result.confidence < 0.7

  if (prediction) {
    return (
      <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-5" aria-live="polite">
        <p className="text-sm font-bold uppercase tracking-wider text-sage">Prediction</p>
        <h3 className="mt-2 text-2xl font-semibold text-ink">{prediction.disease}</h3>
        <p className="mt-1 text-slate-700">Confidence: {confidence}%</p>
        {uncertain && <p className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-900">Prediction uncertain. Please consult a qualified dermatologist.</p>}
        {result.alternatives?.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-semibold text-ink">Top alternatives</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-700">
              {result.alternatives.map((item) => (
                <li key={item.disease}>{item.disease}: {Math.round(item.confidence * 100)}%</li>
              ))}
            </ul>
          </div>
        )}
        {result.disease_info && (
          <div className="mt-4 space-y-3 text-sm text-slate-700">
            <p>{result.disease_info.description}</p>
            <p><span className="font-semibold text-ink">Common symptoms:</span> {result.disease_info.symptoms?.join(', ')}</p>
            <p><span className="font-semibold text-ink">Precautions:</span> {result.disease_info.precautions?.join(', ')}</p>
          </div>
        )}
        <p className="mt-4 text-sm font-semibold text-rose-800">{result.disclaimer}</p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-emerald-200 bg-emerald-50 p-5" aria-live="polite">
      <p className="text-sm font-bold uppercase tracking-wider text-sage">Analysis status</p>
      <h3 className="mt-2 text-xl font-semibold text-ink">ML model is not connected yet.</h3>
      <p className="mt-2 leading-6 text-slate-700">The image was successfully received, validated, and processed by the backend.</p>
      {result.image && <p className="mt-2 text-sm text-slate-600">Verified image: {result.image.width} × {result.image.height} px · {result.image.format}</p>}
      <p className="mt-3 text-sm font-semibold text-sage">Phase 3 will connect the trained skin-disease classification model.</p>
    </section>
  )
}

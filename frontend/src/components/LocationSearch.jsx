import { useState } from 'react'
import { findDermatologists } from '../services/api.js'

export default function LocationSearch() {
  const [query, setQuery] = useState('')
  const [state, setState] = useState('idle')
  const [message, setMessage] = useState('')
  const [results, setResults] = useState([])

  const search = async (location) => {
    setState('loading'); setMessage(''); setResults([])
    try {
      const data = await findDermatologists(location)
      setResults(data.results || []); setState('ready')
    } catch (error) {
      setState('error'); setMessage(error.response?.data?.detail || 'Nearby search is unavailable.')
    }
  }

  const useDeviceLocation = () => {
    if (!navigator.geolocation) { setState('error'); setMessage('This browser does not provide location access. Enter a city instead.'); return }
    setState('loading'); setMessage('Requesting your location…')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => search({ latitude: coords.latitude, longitude: coords.longitude }),
      () => { setState('permission-denied'); setMessage('Location permission was denied. Your prediction still works; enter a city to continue.') },
      { enableHighAccuracy: false, maximumAge: 300000, timeout: 10000 },
    )
  }

  return <div className="mt-5 rounded-xl border border-slate-200 bg-white/70 p-4">
    <h4 className="font-semibold text-ink">Find nearby dermatologists</h4>
    <p className="mt-1 text-sm text-slate-600">Location is used only when you request this search and is not stored.</p>
    <div className="mt-3 flex flex-col gap-2 sm:flex-row">
      <button type="button" onClick={useDeviceLocation} className="rounded-lg bg-ink px-3 py-2 text-sm font-semibold text-white">Use my location</button>
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Enter city or location" className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <button type="button" disabled={!query.trim() || state === 'loading'} onClick={() => search({ query: query.trim() })} className="rounded-lg border border-ink px-3 py-2 text-sm font-semibold text-ink disabled:opacity-50">Search city</button>
    </div>
    {state === 'loading' && <p className="mt-3 text-sm text-slate-600" role="status">Searching…</p>}
    {(state === 'error' || state === 'permission-denied') && <p className="mt-3 text-sm text-amber-800" role="alert">{message}</p>}
    {state === 'ready' && results.length === 0 && <p className="mt-3 text-sm text-slate-600">No provider results were returned.</p>}
    {results.length > 0 && <ul className="mt-3 space-y-2">{results.map((item) => <li key={item.id} className="rounded-lg border p-3 text-sm"><a className="font-semibold underline" href={item.map_url} target="_blank" rel="noreferrer">{item.name}</a><p>{item.address}</p></li>)}</ul>}
  </div>
}

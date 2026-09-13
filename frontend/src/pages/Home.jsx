import { useEffect, useMemo, useState } from 'react'
import ApiStatus from '../components/ApiStatus.jsx'
import AnalysisResult from '../components/AnalysisResult.jsx'
import CameraCapture from '../components/CameraCapture.jsx'
import Disclaimer from '../components/Disclaimer.jsx'
import ImagePreview from '../components/ImagePreview.jsx'
import ImageUploader from '../components/ImageUploader.jsx'
import { getHealth, predictImage } from '../services/api.js'
import { readImageDimensions, validateImageFile } from '../utils/imageValidation.js'

export default function Home() {
  const [file, setFile] = useState(null)
  const [source, setSource] = useState('upload')
  const [dimensions, setDimensions] = useState(null)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [cameraRequest, setCameraRequest] = useState(0)
  const [apiStatus, setApiStatus] = useState('checking')
  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ''), [file])

  useEffect(() => {
    getHealth().then(() => setApiStatus('online')).catch(() => setApiStatus('offline'))
  }, [])

  useEffect(() => () => previewUrl && URL.revokeObjectURL(previewUrl), [previewUrl])

  const selectImage = async (nextFile, nextSource = 'upload') => {
    setError('')
    setResult(null)
    if (!nextFile) return

    const validationError = validateImageFile(nextFile)
    if (validationError) {
      setError(validationError)
      return
    }

    try {
      const nextDimensions = await readImageDimensions(nextFile)
      setFile(nextFile)
      setSource(nextSource)
      setDimensions(nextDimensions)
    } catch (decodeError) {
      setError(decodeError.message)
    }
  }

  const clearImage = () => {
    setFile(null)
    setDimensions(null)
    setResult(null)
    setError('')
  }

  const analyzeImage = async () => {
    if (!file || isAnalyzing) return
    setIsAnalyzing(true)
    setError('')
    setResult(null)
    try {
      setResult(await predictImage(file))
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      if (detail) setError(typeof detail === 'string' ? detail : 'The backend rejected this image.')
      else if (requestError.code === 'ECONNABORTED') setError('The analysis request timed out. Please retry.')
      else if (!requestError.response) setError('The backend is unavailable. Start it and try again.')
      else setError('The server could not process the image. Please retry.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-mint via-white to-orange-50 px-4 py-10 text-ink sm:py-16">
      <div className="mx-auto max-w-5xl">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="mb-2 text-sm font-bold uppercase tracking-[0.2em] text-sage">SkinScope AI</p>
            <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">Skin condition classification, designed responsibly.</h1>
          </div>
          <ApiStatus status={apiStatus} />
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
          <div className="rounded-3xl border border-white bg-white/90 p-6 shadow-xl shadow-emerald-950/10 sm:p-8">
            <h2 className="text-2xl font-semibold">Add an image</h2>
            <p className="mt-2 text-slate-600">Choose a clear, well-lit image or use your device camera.</p>

            <div className="mt-7 grid gap-3 sm:grid-cols-[1fr_auto_1fr] sm:items-start">
              <ImageUploader file={file} onFileChange={(nextFile) => selectImage(nextFile, 'upload')} />
              <span className="pt-3 text-center text-xs font-bold uppercase tracking-widest text-slate-400">or</span>
              <CameraCapture openRequest={cameraRequest} onCapture={(nextFile) => selectImage(nextFile, 'camera')} />
            </div>

            {error && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800" role="alert">{error}</div>}

            <div className="mt-7">
              {previewUrl ? (
                <ImagePreview
                  previewUrl={previewUrl}
                  file={file}
                  dimensions={dimensions}
                  source={source}
                  onRemove={clearImage}
                  onRetake={() => { clearImage(); setCameraRequest((value) => value + 1) }}
                />
              ) : (
                <div className="grid h-56 place-items-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 text-center text-sm text-slate-500">
                  Image preview will appear here
                </div>
              )}
            </div>

            <button
              className="mt-5 w-full rounded-xl bg-coral px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
              disabled={!file || isAnalyzing}
              type="button"
              onClick={analyzeImage}
            >
              {isAnalyzing ? 'Analyzing image…' : 'Analyze image'}
            </button>
            <div className="mt-5"><AnalysisResult result={result} /></div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl bg-ink p-6 text-white shadow-xl shadow-emerald-950/10">
              <p className="text-sm font-semibold text-emerald-200">Phase 1 foundation</p>
              <h2 className="mt-2 text-2xl font-semibold">A clear path from image to insight</h2>
              <ol className="mt-5 space-y-4 text-sm text-emerald-50">
                <li><strong>01</strong> &nbsp; Select or capture an image</li>
                <li><strong>02</strong> &nbsp; Validate and normalize securely</li>
                <li><strong>03</strong> &nbsp; Process without permanent storage</li>
                <li><strong>04</strong> &nbsp; Connect the model in Phase 3</li>
              </ol>
            </div>
            <Disclaimer />
          </div>
        </section>
      </div>
    </main>
  )
}

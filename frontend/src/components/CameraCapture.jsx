import { useCallback, useEffect, useRef, useState } from 'react'

const CAMERA_MESSAGES = {
  NotAllowedError: 'Camera permission was denied. Allow access in browser settings or upload an image.',
  NotFoundError: 'No camera was found on this device. You can upload an image instead.',
  NotReadableError: 'The camera is already in use or unavailable. Close other camera apps and retry.',
  SecurityError: 'Camera access requires a secure browser context (HTTPS or localhost).',
}

export default function CameraCapture({ onCapture, openRequest = 0 }) {
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [isOpen, setIsOpen] = useState(false)
  const [error, setError] = useState('')

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setIsOpen(false)
  }, [])

  const openCamera = useCallback(async () => {
    setError('')
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera access is not supported by this browser. Please upload an image.')
      return
    }

    stopCamera()
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      })
      streamRef.current = stream
      setIsOpen(true)
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(() => setError('The live camera preview could not start.'))
        }
      })
    } catch (cameraError) {
      setError(CAMERA_MESSAGES[cameraError.name] || 'Camera access failed. Please retry or upload an image.')
    }
  }, [stopCamera])

  useEffect(() => () => stopCamera(), [stopCamera])
  useEffect(() => { if (openRequest > 0) openCamera() }, [openRequest, openCamera])

  const captureImage = () => {
    const video = videoRef.current
    if (!video?.videoWidth || !video?.videoHeight) {
      setError('The camera is not ready yet. Wait a moment and retry.')
      return
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    canvas.toBlob((blob) => {
      if (!blob) {
        setError('The photograph could not be captured. Please retry.')
        return
      }
      onCapture(new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' }))
      stopCamera()
    }, 'image/jpeg', 0.92)
  }

  return (
    <div className="text-center">
      {!isOpen && (
        <button className="w-full rounded-xl border border-sage bg-white px-5 py-3 font-semibold text-sage transition hover:bg-mint" type="button" onClick={openCamera}>
          Open camera
        </button>
      )}
      {isOpen && (
        <div className="rounded-2xl bg-ink p-3">
          <video ref={videoRef} className="aspect-video w-full rounded-xl bg-black object-cover" autoPlay muted playsInline />
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button className="rounded-xl bg-coral px-4 py-2 font-semibold text-white" type="button" onClick={captureImage}>Capture</button>
            <button className="rounded-xl border border-white/40 px-4 py-2 font-semibold text-white" type="button" onClick={stopCamera}>Cancel</button>
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-rose-700" role="alert">{error}</p>}
      {!isOpen && !error && <p className="mt-2 text-xs text-slate-500">Uses the rear camera when available</p>}
    </div>
  )
}

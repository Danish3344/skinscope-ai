import { useState } from 'react'

export default function ImageUploader({ file, onFileChange }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    onFileChange(event.dataTransfer.files?.[0] ?? null)
  }

  return (
    <div
      className={`rounded-2xl border-2 border-dashed p-3 transition ${
        isDragging ? 'border-sage bg-mint scale-[1.01]' : 'border-slate-200 bg-slate-50'
      }`}
      onDragEnter={(event) => { event.preventDefault(); setIsDragging(true) }}
      onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }}
      onDragLeave={(event) => { event.preventDefault(); setIsDragging(false) }}
      onDrop={handleDrop}
    >
      <input
        id="skin-image"
        className="sr-only"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={(event) => {
          onFileChange(event.target.files?.[0] ?? null)
          event.target.value = ''
        }}
      />
      <label
        htmlFor="skin-image"
        className="flex cursor-pointer items-center justify-center rounded-xl bg-sage px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-ink focus-within:ring-2 focus-within:ring-sage"
      >
        {isDragging ? 'Drop image here' : file ? 'Choose another image' : 'Browse or drop image'}
      </label>
      <p className="mt-2 text-center text-xs text-slate-500">JPG, PNG or WEBP · maximum 10 MB</p>
    </div>
  )
}

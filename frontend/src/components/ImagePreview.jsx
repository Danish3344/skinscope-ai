function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export default function ImagePreview({ previewUrl, file, dimensions, source, onRemove, onRetake }) {
  if (!previewUrl) return null

  return (
    <figure className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <img className="h-64 w-full rounded-xl object-cover" src={previewUrl} alt="Selected skin image preview" />
      <figcaption className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 text-sm text-slate-600">
          <p className="truncate font-semibold text-ink">{source === 'camera' ? 'Camera capture' : file.name}</p>
          <p>{dimensions ? `${dimensions.width} × ${dimensions.height} px · ` : ''}{formatFileSize(file.size)}</p>
        </div>
        <div className="flex gap-2">
          {source === 'camera' && <button className="rounded-lg border border-sage px-3 py-2 text-sm font-semibold text-sage" type="button" onClick={onRetake}>Retake</button>}
          <button className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700" type="button" onClick={onRemove}>Remove</button>
        </div>
      </figcaption>
    </figure>
  )
}

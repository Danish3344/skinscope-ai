export default function ApiStatus({ status }) {
  const styles = {
    checking: 'bg-slate-100 text-slate-600',
    online: 'bg-emerald-100 text-emerald-800',
    offline: 'bg-rose-100 text-rose-800',
  }

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${styles[status]}`}>
      <span className="mr-2 h-2 w-2 rounded-full bg-current" />
      API {status}
    </span>
  )
}


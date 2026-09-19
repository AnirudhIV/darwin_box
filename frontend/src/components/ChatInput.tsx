import { ArrowUp } from '@phosphor-icons/react'
import { useState } from 'react'

export function ChatInput({
  disabled,
  loading,
  onSubmit,
}: {
  disabled: boolean
  loading: boolean
  onSubmit: (question: string) => void
}) {
  const [value, setValue] = useState('')

  const submit = () => {
    const q = value.trim()
    if (!q || disabled || loading) return
    onSubmit(q)
    setValue('')
  }

  return (
    <div className="flex items-center gap-2 border border-neutral-200 dark:border-neutral-700 rounded-full bg-white/90 dark:bg-neutral-900/90 backdrop-blur px-4 py-2 shadow-sm">
      <input
        className="flex-1 text-sm outline-none disabled:cursor-not-allowed placeholder:text-neutral-400 dark:placeholder:text-neutral-500 text-neutral-900 dark:text-neutral-100 bg-transparent"
        placeholder={disabled ? 'Upload a file to get started...' : 'Ask a question about your data...'}
        value={value}
        disabled={disabled || loading}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') submit()
        }}
      />
      <button
        className="w-8 h-8 flex items-center justify-center rounded-full bg-blue-600 dark:bg-blue-500 text-white disabled:bg-neutral-200 dark:disabled:bg-neutral-700 disabled:text-neutral-400 dark:disabled:text-neutral-500"
        disabled={disabled || loading || !value.trim()}
        onClick={submit}
      >
        {loading ? (
          <span className="w-3 h-3 border-2 border-white/60 border-t-transparent rounded-full animate-spin" />
        ) : (
          <ArrowUp size={16} weight="bold" />
        )}
      </button>
    </div>
  )
}

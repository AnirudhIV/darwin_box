import { UploadSimple } from '@phosphor-icons/react'
import { useRef, useState } from 'react'

export function FileUploader({
  onFiles,
  disabled,
}: {
  onFiles: (files: File[]) => void
  disabled?: boolean
}) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return
    onFiles(Array.from(fileList))
  }

  return (
    <div
      className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
        dragOver
          ? 'border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/40'
          : 'border-neutral-300 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800'
      } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        handleFiles(e.dataTransfer.files)
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".csv,.xlsx"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          handleFiles(e.target.files)
          e.target.value = ''
        }}
      />
      <UploadSimple size={22} className="mx-auto mb-2 text-neutral-400 dark:text-neutral-500" />
      <p className="text-sm font-medium text-neutral-700 dark:text-neutral-200">Drop CSV or Excel files here</p>
      <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">
        or click to browse — multiple files supported
      </p>
    </div>
  )
}

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
        dragOver ? 'border-blue-400 bg-blue-50' : 'border-neutral-300 bg-neutral-50 hover:bg-neutral-100'
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
      <p className="text-sm font-medium text-neutral-700">Drop CSV or Excel files here</p>
      <p className="text-xs text-neutral-400 mt-1">or click to browse — multiple files supported</p>
    </div>
  )
}

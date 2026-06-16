import { CheckCircle2, Copy } from 'lucide-react'
import { useState } from 'react'

interface Props {
  answer: string
  taskStatus: string
}

export function ResultPanel({ answer, taskStatus }: Props) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(answer)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-gray-900 border border-emerald-800 rounded-xl p-6 mt-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-emerald-400" />
          <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">
            Final Answer
          </h2>
        </div>
        <button
          onClick={handleCopy}
          className="text-xs text-gray-500 hover:text-gray-300 flex items-center gap-1.5 transition-colors"
        >
          <Copy size={12} />
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <div className="prose prose-invert prose-sm max-w-none">
        <pre className="whitespace-pre-wrap text-sm text-gray-300 leading-relaxed font-sans">
          {answer}
        </pre>
      </div>
    </div>
  )
}

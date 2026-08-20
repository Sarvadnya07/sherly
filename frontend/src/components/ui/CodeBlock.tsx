import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'python',
  filename,
  className = '',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.warn('Failed to copy code:', e);
    }
  };

  return (
    <div className={`my-2.5 rounded-xl border border-white/[0.08] bg-zinc-950 overflow-hidden font-mono text-xs shadow-subtle ${className}`}>
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-zinc-900/60 border-b border-white/[0.06] select-none">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">
            {language}
          </span>
          {filename && (
            <span className="text-[11px] text-zinc-400 font-sans">{filename}</span>
          )}
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] text-zinc-400 hover:text-zinc-100 transition bg-zinc-800/60 hover:bg-zinc-800 px-2 py-0.5 rounded-md border border-white/[0.06] focus-visible:outline-2 focus-visible:outline-indigo-500 cursor-pointer"
          title="Copy code to clipboard"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content Area with Native Selection */}
      <div className="p-3.5 overflow-x-auto leading-relaxed text-zinc-200 select-text">
        <pre className="font-mono text-xs whitespace-pre select-text">
          <code className="select-text">{code}</code>
        </pre>
      </div>
    </div>
  );
};

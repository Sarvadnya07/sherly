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
    <div className={`my-3 rounded-lg border border-white/[0.08] bg-[#09090f] overflow-hidden font-mono text-xs shadow-subtle ${className}`}>
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-white/[0.03] border-b border-white/[0.06] select-none">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">
            {language}
          </span>
          {filename && (
            <span className="text-[11px] text-gray-400 font-sans">{filename}</span>
          )}
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[11px] text-gray-400 hover:text-gray-100 transition bg-white/[0.04] hover:bg-white/[0.08] px-2.5 py-0.5 rounded border border-white/[0.08] focus-visible:outline-2 focus-visible:outline-brand cursor-pointer"
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
      <div className="p-3.5 overflow-x-auto leading-relaxed text-gray-200 select-text">
        <pre className="font-mono text-xs whitespace-pre select-text">
          <code className="select-text">{code}</code>
        </pre>
      </div>
    </div>
  );
};

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
    <div className={`my-2.5 rounded-lg border border-border-subtle bg-canvas overflow-hidden font-mono text-xs shadow-subtle ${className}`}>
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-sidebar border-b border-border-subtle select-none">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[10px] font-semibold text-txt-muted uppercase tracking-wider shrink-0">
            {language}
          </span>
          {filename && (
            <span className="text-xs text-txt-secondary font-sans truncate">{filename}</span>
          )}
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-txt-secondary hover:text-txt-primary transition bg-card hover:bg-card-hover px-2 py-0.5 rounded border border-border-subtle focus-visible:outline-2 focus-visible:outline-brand cursor-pointer shrink-0"
          title="Copy code to clipboard"
          aria-label="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-status-success font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content Area with Native Text Selection */}
      <div className="p-3.5 overflow-x-auto leading-relaxed text-txt-primary select-text">
        <pre className="font-mono text-xs whitespace-pre select-text">
          <code className="select-text">{code}</code>
        </pre>
      </div>
    </div>
  );
};

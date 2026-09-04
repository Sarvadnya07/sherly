import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import {
  Sparkles,
  Paperclip,
  Mic,
  ArrowUp,
  Square,
  FileText,
  Loader2,
  Copy,
  Check,
  RotateCw,
  Edit3,
  Search,
  ChevronUp,
  ChevronDown,
  X,
  ArrowDown,
  ExternalLink,
  Wrench,
  AlertCircle,
} from 'lucide-react';
import { CodeBlock } from '../components/ui/CodeBlock';
import { IconButton } from '../components/ui/Button';

// ── Markdown Content Parser & Renderer ───────────────────────────────────────

interface MarkdownRendererProps {
  content: string;
  searchQuery?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = React.memo(({ content, searchQuery }) => {
  const highlightText = useCallback(
    (text: string) => {
      if (!searchQuery || !searchQuery.trim()) return text;
      const query = searchQuery.trim();
      const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
      return parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={i} className="bg-status-warning/30 text-status-warning px-0.5 rounded">
            {part}
          </mark>
        ) : (
          part
        )
      );
    },
    [searchQuery]
  );

  const renderInline = useCallback(
    (text: string) => {
      const codeParts = text.split(/(`[^`]+`)/g);
      return codeParts.map((cp, cIdx) => {
        if (cp.startsWith('`') && cp.endsWith('`') && cp.length > 2) {
          return (
            <code
              key={cIdx}
              className="bg-card text-txt-primary font-mono text-xs px-1.5 py-0.5 rounded border border-border-subtle select-text"
            >
              {highlightText(cp.slice(1, -1))}
            </code>
          );
        }

        const boldParts = cp.split(/(\*\*[^*]+\*\*)/g);
        return boldParts.map((bp, bIdx) => {
          if (bp.startsWith('**') && bp.endsWith('**') && bp.length > 4) {
            return (
              <strong key={bIdx} className="font-semibold text-txt-primary">
                {highlightText(bp.slice(2, -2))}
              </strong>
            );
          }

          const linkParts = bp.split(/(\[[^\]]+\]\([^)]+\))/g);
          return linkParts.map((lp, lIdx) => {
            const match = /\[([^\]]+)\]\(([^)]+)\)/.exec(lp);
            if (match) {
              const [, label, url] = match;
              return (
                <a
                  key={lIdx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-hover underline underline-offset-2 inline-flex items-center gap-0.5 focus-visible:outline-2 focus-visible:outline-brand"
                >
                  <span>{highlightText(label)}</span>
                  <ExternalLink className="w-3 h-3 inline shrink-0" />
                </a>
              );
            }

            return highlightText(lp);
          });
        });
      });
    },
    [highlightText]
  );

  if (content.includes('```')) {
    const parts = content.split(/(```[\s\S]*?```)/g);
    return (
      <div className="flex flex-col gap-2.5 select-text">
        {parts.map((part, idx) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const firstLineBreak = part.indexOf('\n');
            const lang = firstLineBreak !== -1 ? part.slice(3, firstLineBreak).trim() : '';
            const code = firstLineBreak !== -1 ? part.slice(firstLineBreak + 1, -3) : part.slice(3, -3);
            return <CodeBlock key={idx} language={lang || 'python'} code={code.trim()} />;
          }

          if (!part.trim()) return null;
          return <MarkdownRenderer key={idx} content={part} searchQuery={searchQuery} />;
        })}
      </div>
    );
  }

  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = () => {
    if (inList && listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc pl-5 my-1.5 space-y-1 text-txt-secondary">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h4 key={idx} className="text-xs font-semibold text-txt-primary mt-2 mb-1">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={idx} className="text-sm font-semibold text-txt-primary mt-2.5 mb-1">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h2 key={idx} className="text-base font-bold text-txt-primary mt-3 mb-1.5">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      listItems.push(
        <li key={idx} className="text-xs leading-relaxed text-txt-secondary">
          {renderInline(trimmed.slice(2))}
        </li>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      flushList();
      elements.push(
        <div key={idx} className="text-xs leading-relaxed text-txt-secondary pl-4 relative my-0.5">
          <span className="absolute left-0 text-txt-muted font-mono text-[11px]">
            {trimmed.match(/^\d+\./)?.[0]}
          </span>
          {renderInline(trimmed.replace(/^\d+\.\s*/, ''))}
        </div>
      );
    } else if (trimmed.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote
          key={idx}
          className="border-l-2 border-brand bg-card px-3 py-1.5 rounded-r my-1.5 text-xs text-txt-secondary italic"
        >
          {renderInline(trimmed.slice(2))}
        </blockquote>
      );
    } else if (!trimmed) {
      flushList();
    } else {
      flushList();
      elements.push(
        <p key={idx} className="text-xs leading-relaxed text-txt-primary my-1">
          {renderInline(line)}
        </p>
      );
    }
  });

  flushList();

  return <div className="flex flex-col select-text">{elements}</div>;
});

// ── Assistant Main View Component ────────────────────────────────────────────

export const AssistantView: React.FC = () => {
  const {
    chatHistory,
    isThinking,
    statusText,
    composerPrompt,
    setComposerPrompt,
    sendChatMessage,
    cancelGeneration,
    regenerateMessage,
    fetchChatHistory,
  } = useSherlyStore();

  const [prompt, setPrompt] = useState(composerPrompt);
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [userCopiedIndex, setUserCopiedIndex] = useState<number | null>(null);

  // Synchronize composer prompt from store when editing an old message
  useEffect(() => {
    if (composerPrompt !== prompt) {
      setPrompt(composerPrompt);
      textareaRef.current?.focus();
    }
  }, [composerPrompt]);

  // In-conversation search state
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentMatchIdx, setCurrentMatchIdx] = useState(0);

  // Auto-scroll tracking
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  const scrollToBottom = useCallback((smooth = true) => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      });
    }
  }, []);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 80;
    setShowScrollBottom(!isNearBottom);
  };

  useEffect(() => {
    if (!showScrollBottom) {
      scrollToBottom(false);
    }
  }, [chatHistory, isThinking, showScrollBottom, scrollToBottom]);

  // Auto-expand textarea height (44px min to 140px max)
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(140, Math.max(44, textareaRef.current.scrollHeight))}px`;
    }
  }, [prompt]);

  // Context-Aware Global Shortcuts (Ctrl+F, Ctrl+A, Esc)
  useEffect(() => {
    const handleGlobalKeys = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInputFocused =
        activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');

      // Scoped Ctrl+F: open search only if not typing inside an active selection
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
        if (!isInputFocused) {
          e.preventDefault();
          setSearchOpen(true);
          setTimeout(() => searchInputRef.current?.focus(), 50);
        }
      } else if (e.key === 'Escape') {
        if (searchOpen) {
          setSearchOpen(false);
          setSearchQuery('');
        } else if (isThinking) {
          cancelGeneration();
        }
      }
    };

    window.addEventListener('keydown', handleGlobalKeys);
    return () => window.removeEventListener('keydown', handleGlobalKeys);
  }, [searchOpen, isThinking, cancelGeneration]);

  // Canonical Message State Search Calculation
  const totalMatches = useMemo(() => {
    if (!searchQuery.trim()) return 0;
    const q = searchQuery.toLowerCase();
    let count = 0;
    chatHistory.forEach((msg) => {
      const pMatches = (msg.user_prompt.toLowerCase().match(new RegExp(q, 'g')) || []).length;
      const aMatches = (msg.assistant_response.toLowerCase().match(new RegExp(q, 'g')) || []).length;
      count += pMatches + aMatches;
    });
    return count;
  }, [searchQuery, chatHistory]);

  useEffect(() => {
    if (totalMatches > 0 && currentMatchIdx === 0) {
      setCurrentMatchIdx(1);
    } else if (totalMatches === 0) {
      setCurrentMatchIdx(0);
    }
  }, [totalMatches, currentMatchIdx]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isThinking) return;

    const currentPrompt = prompt.trim();
    const currentAtt = attachedFile || undefined;
    setPrompt('');
    setComposerPrompt('');
    setAttachedFile(null);

    sendChatMessage(currentPrompt, currentAtt);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileAttach = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = (e: any) => {
      const file = e.target.files?.[0];
      if (file) {
        setAttachedFile(file.name);
      }
    };
    input.click();
  };

  const handleCopy = async (text: string, index: number, isUser = false) => {
    try {
      await navigator.clipboard.writeText(text);
      if (isUser) {
        setUserCopiedIndex(index);
        setTimeout(() => setUserCopiedIndex(null), 1500);
      } else {
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 1500);
      }
    } catch (e) {
      console.warn('Failed to copy text:', e);
    }
  };

  const handleEditUserPrompt = (text: string) => {
    setPrompt(text);
    setComposerPrompt(text);
    textareaRef.current?.focus();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas overflow-hidden relative">
      {/* Floating In-Conversation Search Bar */}
      {searchOpen && (
        <div className="absolute top-3 right-6 z-30 bg-card border border-border-medium rounded-lg p-2 shadow-elevated flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-150 select-none">
          <Search className="w-3.5 h-3.5 text-brand ml-1 shrink-0" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversation..."
            className="bg-transparent text-xs text-txt-primary placeholder-txt-muted focus:outline-none w-56 font-sans select-text"
          />

          <span className="text-[10px] text-txt-muted font-mono select-none">
            {totalMatches > 0 ? `${currentMatchIdx} of ${totalMatches}` : 'No matches'}
          </span>

          <div className="flex items-center gap-0.5">
            <IconButton
              icon={<ChevronUp className="w-3 h-3" />}
              aria-label="Previous match"
              size="sm"
              onClick={() => setCurrentMatchIdx((prev) => (prev > 1 ? prev - 1 : totalMatches))}
              disabled={totalMatches === 0}
            />
            <IconButton
              icon={<ChevronDown className="w-3 h-3" />}
              aria-label="Next match"
              size="sm"
              onClick={() => setCurrentMatchIdx((prev) => (prev < totalMatches ? prev + 1 : 1))}
              disabled={totalMatches === 0}
            />
            <IconButton
              icon={<X className="w-3 h-3" />}
              aria-label="Close search"
              size="sm"
              onClick={() => {
                setSearchOpen(false);
                setSearchQuery('');
              }}
            />
          </div>
        </div>
      )}

      {/* Conversation Timeline Stream (Clamped Reading Width: 760px-840px, Native Selection Enabled) */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 flex flex-col gap-6 max-w-3xl w-full mx-auto select-text"
      >
        {chatHistory.length === 0 && !isThinking && (
          <div className="flex flex-col items-center justify-center h-full text-center text-txt-muted my-auto select-none py-16">
            <div className="w-10 h-10 rounded-lg bg-card border border-border-subtle flex items-center justify-center text-brand mb-3 shadow-subtle">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-txt-primary">How can I help you today?</h3>
            <p className="text-xs text-txt-muted max-w-xs mt-1 leading-relaxed">
              Ask questions, inspect workspace files, run developer commands, or execute code tools.
            </p>
          </div>
        )}

        {chatHistory.map((msg, index) => (
          <div key={msg.id || index} className="flex flex-col gap-4">
            {/* User Prompt (Right aligned sleek bubble) */}
            <div className="flex items-start gap-2.5 justify-end group">
              {/* User Hover Action Toolbar */}
              <div className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity flex items-center gap-1 self-center select-none">
                <button
                  type="button"
                  onClick={() => handleCopy(msg.user_prompt, index, true)}
                  className="p-1 rounded text-txt-muted hover:text-txt-primary hover:bg-card transition cursor-pointer"
                  title="Copy prompt"
                  aria-label="Copy prompt text"
                >
                  {userCopiedIndex === index ? (
                    <Check className="w-3.5 h-3.5 text-status-success" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => handleEditUserPrompt(msg.user_prompt)}
                  className="p-1 rounded text-txt-muted hover:text-txt-primary hover:bg-card transition cursor-pointer"
                  title="Edit prompt"
                  aria-label="Edit prompt in composer"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="bg-card border border-border-subtle rounded-2xl px-4 py-2.5 max-w-xl flex flex-col gap-1.5 shadow-subtle select-text">
                <p className="text-xs font-normal text-txt-primary leading-relaxed whitespace-pre-wrap select-text">
                  {msg.user_prompt}
                </p>
                {msg.attached_file && (
                  <div className="inline-flex items-center gap-1.5 bg-canvas border border-border-subtle rounded px-2 py-0.5 text-[11px] font-mono text-txt-secondary w-fit select-none">
                    <FileText className="w-3 h-3 text-brand" />
                    <span>{msg.attached_file}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Assistant Response */}
            {msg.assistant_response && (
              <div className="flex items-start gap-3 group">
                <div className="w-6 h-6 rounded-md bg-brand flex items-center justify-center text-white text-[10px] font-bold shrink-0 mt-0.5 shadow-subtle select-none">
                  S
                </div>

                <div className="flex flex-col gap-2 flex-1 min-w-0">
                  {/* Assistant Content */}
                  <div className="text-xs text-txt-primary leading-relaxed select-text">
                    <MarkdownRenderer content={msg.assistant_response} searchQuery={searchQuery} />
                  </div>

                  {/* Status / Error indicator */}
                  {msg.status === 'cancelled' && (
                    <div className="inline-flex items-center gap-1 text-[11px] text-txt-muted font-mono select-none">
                      <span>[Stopped]</span>
                    </div>
                  )}

                  {msg.status === 'error' && (
                    <div className="inline-flex items-center gap-1 text-[11px] text-status-danger font-mono select-none">
                      <AlertCircle className="w-3 h-3" />
                      <span>{msg.error || 'Request failed'}</span>
                    </div>
                  )}

                  {/* Subtle Hover Action Toolbar */}
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity pt-1 select-none">
                    <button
                      type="button"
                      onClick={() => handleCopy(msg.assistant_response, index, false)}
                      className="flex items-center gap-1 text-[11px] font-medium text-txt-muted hover:text-txt-primary transition px-1.5 py-0.5 rounded hover:bg-card cursor-pointer"
                      title="Copy response"
                      aria-label="Copy response"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-status-success" />
                          <span className="text-status-success">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => regenerateMessage(index)}
                      className="flex items-center gap-1 text-[11px] font-medium text-txt-muted hover:text-txt-primary transition px-1.5 py-0.5 rounded hover:bg-card cursor-pointer"
                      title="Regenerate response"
                      aria-label="Regenerate response"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      <span>Retry</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Task / Canonical Tool Execution Activity Status */}
        {isThinking && (
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-3 animate-in fade-in duration-150 select-none py-1"
          >
            <div className="w-6 h-6 rounded-md bg-card border border-border-subtle flex items-center justify-center text-brand text-xs shrink-0">
              {statusText.startsWith('tool:') ? (
                <Wrench className="w-3.5 h-3.5 text-status-info animate-pulse" aria-hidden="true" />
              ) : (
                <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-txt-secondary font-medium">
              <span>
                {statusText.startsWith('tool:')
                  ? `Executing ${statusText.replace('tool:', '')}...`
                  : 'Thinking...'}
              </span>
              <button
                type="button"
                onClick={cancelGeneration}
                className="text-[11px] text-status-danger hover:underline cursor-pointer ml-1"
                aria-label="Cancel generation"
              >
                (Stop)
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating "Scroll to Bottom" Button */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-20 left-1/2 -translate-x-1/2 bg-card/90 backdrop-blur border border-border-medium hover:border-txt-muted text-txt-secondary hover:text-txt-primary px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 shadow-elevated transition active:scale-95 z-20 select-none cursor-pointer"
          title="Scroll to latest messages"
          aria-label="Scroll to latest messages"
        >
          <ArrowDown className="w-3.5 h-3.5 text-brand" />
          <span>Scroll to latest</span>
        </button>
      )}

      {/* Docked Floating Composer Bar (44px min to 140px max height) */}
      <div className="p-4 bg-canvas/80 backdrop-blur-md select-none shrink-0 border-t border-border-subtle">
        <form onSubmit={handleSubmit} className="flex flex-col gap-1.5 max-w-3xl mx-auto">
          {/* File Attachment Pill */}
          {attachedFile && (
            <div className="flex items-center gap-2 text-xs text-txt-secondary font-mono font-medium px-1 select-none">
              <FileText className="w-3.5 h-3.5 text-brand" />
              <span>Attached: {attachedFile}</span>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                className="text-txt-muted hover:text-status-danger ml-1 text-xs cursor-pointer"
                title="Remove attachment"
                aria-label="Remove attachment"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          <div className="bg-card border border-border-subtle focus-within:border-border-medium rounded-xl p-2 flex items-end gap-1.5 transition shadow-elevated">
            <IconButton
              icon={<Paperclip className="w-4 h-4" />}
              aria-label="Attach File"
              onClick={handleFileAttach}
              size="md"
            />

            <textarea
              ref={textareaRef}
              rows={1}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask Sherly anything (Enter to send, Shift+Enter for newline)..."
              className="flex-1 bg-transparent text-xs text-txt-primary placeholder-txt-muted focus:outline-none px-2 resize-none max-h-36 leading-relaxed py-2 select-text"
            />

            <IconButton
              icon={<Search className="w-4 h-4" />}
              aria-label="Search conversation"
              onClick={() => {
                setSearchOpen((prev) => !prev);
                setTimeout(() => searchInputRef.current?.focus(), 50);
              }}
              size="md"
            />

            <IconButton
              icon={<Mic className="w-4 h-4" />}
              aria-label="Voice Input (Ctrl+Shift+L)"
              onClick={() => useSherlyStore.getState().setActiveView('voice')}
              size="md"
            />

            {/* Submit or Stop Generation Button */}
            {isThinking ? (
              <button
                type="button"
                onClick={cancelGeneration}
                className="w-7 h-7 bg-status-danger hover:bg-status-danger/80 text-white rounded-full flex items-center justify-center font-bold transition shrink-0 shadow-subtle focus-visible:outline-2 focus-visible:outline-brand active:scale-95 cursor-pointer mb-0.5"
                title="Stop generation (Esc)"
                aria-label="Stop generation"
              >
                <Square className="w-3 h-3 fill-white" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!prompt.trim()}
                className="w-7 h-7 bg-txt-primary hover:bg-white disabled:opacity-20 text-canvas rounded-full flex items-center justify-center font-bold transition shrink-0 shadow-subtle focus-visible:outline-2 focus-visible:outline-brand active:scale-95 cursor-pointer mb-0.5"
                title="Send Prompt (Enter)"
                aria-label="Send Prompt"
              >
                <ArrowUp className="w-4 h-4 text-canvas" />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

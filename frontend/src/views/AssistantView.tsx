import React, { useState, useEffect, useRef, useCallback } from 'react';
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
} from 'lucide-react';
import { CodeBlock } from '../components/ui/CodeBlock';
import { Badge } from '../components/ui/Badge';
import { IconButton } from '../components/ui/Button';

// ── Markdown Content Parser & Renderer ───────────────────────────────────────

interface MarkdownRendererProps {
  content: string;
  searchQuery?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, searchQuery }) => {
  const highlightText = (text: string) => {
    if (!searchQuery || !searchQuery.trim()) return text;
    const query = searchQuery.trim();
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-amber-400/30 text-amber-200 px-0.5 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const renderInline = (text: string) => {
    const processParagraph = (raw: string): React.ReactNode => {
      const codeParts = raw.split(/(`[^`]+`)/g);
      return codeParts.map((cp, cIdx) => {
        if (cp.startsWith('`') && cp.endsWith('`') && cp.length > 2) {
          return (
            <code
              key={cIdx}
              className="bg-white/[0.08] text-purple-300 font-mono text-[11px] px-1.5 py-0.5 rounded border border-white/[0.08] select-text"
            >
              {highlightText(cp.slice(1, -1))}
            </code>
          );
        }

        const boldParts = cp.split(/(\*\*[^*]+\*\*)/g);
        return boldParts.map((bp, bIdx) => {
          if (bp.startsWith('**') && bp.endsWith('**') && bp.length > 4) {
            return (
              <strong key={bIdx} className="font-semibold text-gray-100">
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
                  className="text-purple-400 hover:text-purple-300 underline underline-offset-2 inline-flex items-center gap-0.5 focus-visible:outline-2 focus-visible:outline-brand"
                >
                  <span>{highlightText(label)}</span>
                  <ExternalLink className="w-2.5 h-2.5 inline shrink-0" />
                </a>
              );
            }

            return highlightText(lp);
          });
        });
      });
    };

    return processParagraph(text);
  };

  if (content.includes('```')) {
    const parts = content.split(/(```[\s\S]*?```)/g);
    return (
      <div className="flex flex-col gap-2 select-text">
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
        <ul key={`list-${elements.length}`} className="list-disc pl-5 my-1 space-y-1 text-gray-200">
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
        <h4 key={idx} className="text-xs font-bold text-purple-300 mt-2 mb-1">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={idx} className="text-sm font-bold text-gray-100 mt-2.5 mb-1">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h2 key={idx} className="text-base font-bold text-gray-100 mt-3 mb-1.5">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      inList = true;
      listItems.push(
        <li key={idx} className="text-xs leading-relaxed text-gray-200">
          {renderInline(trimmed.slice(2))}
        </li>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      flushList();
      elements.push(
        <div key={idx} className="text-xs leading-relaxed text-gray-200 pl-4 relative my-0.5">
          <span className="absolute left-0 text-gray-500 font-mono text-[11px]">
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
          className="border-l-2 border-brand bg-brand-surface/30 px-3 py-1.5 rounded-r my-1.5 text-xs text-gray-300 italic"
        >
          {renderInline(trimmed.slice(2))}
        </blockquote>
      );
    } else if (!trimmed) {
      flushList();
    } else {
      flushList();
      elements.push(
        <p key={idx} className="text-xs leading-relaxed text-gray-200 my-1">
          {renderInline(line)}
        </p>
      );
    }
  });

  flushList();

  return <div className="flex flex-col select-text">{elements}</div>;
};

// ── Assistant Main View Component ────────────────────────────────────────────

export const AssistantView: React.FC = () => {
  const {
    chatHistory,
    isThinking,
    sendChatMessage,
    cancelGeneration,
    regenerateMessage,
    fetchChatHistory,
  } = useSherlyStore();

  const [prompt, setPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [userCopiedIndex, setUserCopiedIndex] = useState<number | null>(null);

  // In-conversation search state
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [matchCount, setMatchCount] = useState(0);
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

  // Auto-expand textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(140, Math.max(38, textareaRef.current.scrollHeight))}px`;
    }
  }, [prompt]);

  // Global Keyboard Shortcuts (Ctrl+F, Esc)
  useEffect(() => {
    const handleGlobalKeys = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => searchInputRef.current?.focus(), 50);
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

  // Search match computation
  useEffect(() => {
    if (!searchQuery.trim()) {
      setMatchCount(0);
      setCurrentMatchIdx(0);
      return;
    }

    const q = searchQuery.toLowerCase();
    let total = 0;
    chatHistory.forEach((msg) => {
      const pMatches = (msg.user_prompt.toLowerCase().match(new RegExp(q, 'g')) || []).length;
      const aMatches = (msg.assistant_response.toLowerCase().match(new RegExp(q, 'g')) || []).length;
      total += pMatches + aMatches;
    });

    setMatchCount(total);
    setCurrentMatchIdx(total > 0 ? 1 : 0);
  }, [searchQuery, chatHistory]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isThinking) return;

    const currentPrompt = prompt.trim();
    const currentAtt = attachedFile || undefined;
    setPrompt('');
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
    textareaRef.current?.focus();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-surface overflow-hidden relative">
      {/* Floating In-Conversation Search Bar */}
      {searchOpen && (
        <div className="absolute top-3 right-6 z-30 bg-card border border-white/[0.12] rounded-xl p-2 shadow-elevated flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-150">
          <Search className="w-3.5 h-3.5 text-purple-400 ml-1 shrink-0" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversation (Ctrl+F)..."
            className="bg-transparent text-xs text-gray-100 placeholder-gray-500 focus:outline-none w-56 font-sans"
          />

          <span className="text-[10px] text-gray-400 font-mono select-none">
            {matchCount > 0 ? `${currentMatchIdx} of ${matchCount}` : 'No matches'}
          </span>

          <div className="flex items-center gap-0.5">
            <IconButton
              icon={<ChevronUp className="w-3 h-3" />}
              aria-label="Previous match"
              size="sm"
              onClick={() => setCurrentMatchIdx((prev) => (prev > 1 ? prev - 1 : matchCount))}
              disabled={matchCount === 0}
            />
            <IconButton
              icon={<ChevronDown className="w-3 h-3" />}
              aria-label="Next match"
              size="sm"
              onClick={() => setCurrentMatchIdx((prev) => (prev < matchCount ? prev + 1 : 1))}
              disabled={matchCount === 0}
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

      {/* Conversation Timeline Stream */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-5 max-w-3xl w-full mx-auto select-text"
      >
        {chatHistory.length === 0 && !isThinking && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 my-auto select-none py-12">
            <div className="w-11 h-11 rounded-2xl bg-brand-surface border border-brand-border flex items-center justify-center text-purple-400 mb-3 shadow-subtle">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-gray-200">Sherly Assistant</h3>
            <p className="text-xs text-gray-400 max-w-sm mt-1.5 leading-relaxed">
              Ask coding questions, refactor source files, execute workspace tasks, or inspect local models.
            </p>
          </div>
        )}

        {chatHistory.map((msg, index) => (
          <React.Fragment key={index}>
            {/* User Message Card */}
            <div className="flex items-start gap-3 justify-end group">
              {/* User Hover Action Toolbar */}
              <div className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity flex items-center gap-1 self-center mr-1 select-none">
                <button
                  type="button"
                  onClick={() => handleCopy(msg.user_prompt, index, true)}
                  className="p-1 rounded text-gray-400 hover:text-gray-200 hover:bg-white/[0.06] transition cursor-pointer"
                  title="Copy prompt"
                  aria-label="Copy prompt text"
                >
                  {userCopiedIndex === index ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => handleEditUserPrompt(msg.user_prompt)}
                  className="p-1 rounded text-gray-400 hover:text-gray-200 hover:bg-white/[0.06] transition cursor-pointer"
                  title="Edit prompt"
                  aria-label="Edit prompt in composer"
                >
                  <Edit3 className="w-3 h-3" />
                </button>
              </div>

              <div className="bg-[#151622] border border-white/[0.08] rounded-xl px-3.5 py-3 max-w-2xl flex flex-col gap-1.5 shadow-subtle select-text">
                <p className="text-xs font-normal text-gray-100 leading-relaxed whitespace-pre-wrap select-text">
                  {msg.user_prompt}
                </p>
                {msg.attached_file && (
                  <div className="inline-flex items-center gap-1.5 bg-brand-surface border border-brand-border rounded px-2 py-0.5 text-[11px] font-mono text-purple-300 w-fit select-none">
                    <FileText className="w-3 h-3 text-purple-400" />
                    <span>{msg.attached_file}</span>
                  </div>
                )}
              </div>

              <div className="w-6 h-6 rounded-full bg-white/[0.08] border border-white/10 flex items-center justify-center text-gray-200 text-[10px] font-bold shrink-0 mt-0.5 select-none">
                U
              </div>
            </div>

            {/* Assistant Response Card */}
            <div className="flex items-start gap-3 group">
              <div className="w-6 h-6 rounded-full bg-brand flex items-center justify-center text-white text-[10px] font-bold shrink-0 mt-0.5 shadow-subtle select-none">
                S
              </div>

              <div className="bg-card border border-white/[0.07] rounded-xl p-4 max-w-2xl text-xs text-gray-200 leading-relaxed flex flex-col gap-2.5 flex-1 shadow-subtle select-text">
                {/* Header with Title, Badge, and Action Toolbar */}
                <div className="flex items-center justify-between border-b border-white/[0.06] pb-2 select-none">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-purple-300">Sherly Assistant</span>
                    <Badge variant="brand" size="sm">Copilot</Badge>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Regenerate Action */}
                    <button
                      type="button"
                      onClick={() => regenerateMessage(index)}
                      className="flex items-center gap-1 text-[10px] font-medium text-gray-400 hover:text-gray-200 transition bg-white/[0.04] hover:bg-white/[0.08] px-2 py-0.5 rounded border border-white/[0.06] focus-visible:outline-2 focus-visible:outline-brand cursor-pointer"
                      title="Regenerate response"
                      aria-label="Regenerate response"
                    >
                      <RotateCw className="w-3 h-3" />
                      <span>Retry</span>
                    </button>

                    {/* Copy Response Action */}
                    <button
                      type="button"
                      onClick={() => handleCopy(msg.assistant_response, index, false)}
                      className="flex items-center gap-1 text-[10px] font-medium text-gray-400 hover:text-gray-200 transition bg-white/[0.04] hover:bg-white/[0.08] px-2 py-0.5 rounded border border-white/[0.06] focus-visible:outline-2 focus-visible:outline-brand cursor-pointer"
                      title="Copy response to clipboard"
                      aria-label="Copy assistant response"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400 font-medium">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Structured Markdown Render Area */}
                <MarkdownRenderer content={msg.assistant_response} searchQuery={searchQuery} />
              </div>
            </div>
          </React.Fragment>
        ))}

        {/* Task Status Node (Thinking State) */}
        {isThinking && (
          <div className="flex items-center gap-3 animate-in fade-in duration-150 select-none py-1">
            <div className="w-6 h-6 rounded-full bg-brand-surface border border-brand-border flex items-center justify-center text-purple-400 text-xs shrink-0">
              <Loader2 className="w-3 h-3 animate-spin" />
            </div>
            <span className="text-xs text-gray-400 font-medium">
              Thinking and generating response...
            </span>
          </div>
        )}
      </div>

      {/* Floating "Scroll to Bottom" Pill Button */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-20 left-1/2 -translate-x-1/2 bg-card/95 backdrop-blur border border-white/[0.12] hover:border-brand text-gray-300 hover:text-white px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 shadow-elevated transition active:scale-95 z-20 select-none cursor-pointer"
          title="Scroll to latest messages"
          aria-label="Scroll to latest messages"
        >
          <ArrowDown className="w-3.5 h-3.5 text-purple-400" />
          <span>Scroll to latest</span>
        </button>
      )}

      {/* Docked Composer Bar */}
      <div className="p-3.5 bg-surface border-t border-white/[0.07] select-none shrink-0">
        <form onSubmit={handleSubmit} className="flex flex-col gap-1.5 max-w-3xl mx-auto">
          {/* File Attachment Pill */}
          {attachedFile && (
            <div className="flex items-center gap-2 text-xs text-purple-300 font-mono font-medium px-1 select-none">
              <FileText className="w-3.5 h-3.5 text-purple-400" />
              <span>Attached: {attachedFile}</span>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                className="text-gray-500 hover:text-rose-400 ml-1 text-xs cursor-pointer"
                title="Remove attachment"
                aria-label="Remove attachment"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          <div className="bg-input border border-white/[0.10] focus-within:border-brand rounded-xl p-2 flex items-end gap-2 transition shadow-subtle">
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
              placeholder="Ask Sherly anything (Enter to send, Shift+Enter for newline, Ctrl+F to search)..."
              className="flex-1 bg-transparent text-xs text-gray-100 placeholder-gray-500 focus:outline-none px-2 resize-none max-h-36 leading-relaxed py-1 select-text"
            />

            <IconButton
              icon={<Search className="w-4 h-4" />}
              aria-label="Search conversation (Ctrl+F)"
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
                className="w-7 h-7 bg-rose-600/80 hover:bg-rose-600 text-white rounded-lg flex items-center justify-center font-bold transition shrink-0 shadow-subtle focus-visible:outline-2 focus-visible:outline-brand active:scale-95 cursor-pointer"
                title="Stop generation (Esc)"
                aria-label="Stop generation"
              >
                <Square className="w-3 h-3 fill-white" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!prompt.trim()}
                className="w-7 h-7 bg-brand hover:bg-brand-hover disabled:opacity-30 text-white rounded-lg flex items-center justify-center font-bold transition shrink-0 shadow-subtle focus-visible:outline-2 focus-visible:outline-brand active:scale-95 cursor-pointer"
                title="Send Prompt (Enter)"
                aria-label="Send Prompt"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

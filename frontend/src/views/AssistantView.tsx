import React, { useState, useEffect, useRef } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Sparkles, Paperclip, Mic, ArrowUp, FileText, Loader2, Copy, Check, X } from 'lucide-react';
import { CodeBlock } from '../components/ui/CodeBlock';
import { Badge } from '../components/ui/Badge';
import { IconButton } from '../components/ui/Button';

export const AssistantView: React.FC = () => {
  const {
    chatHistory,
    isThinking,
    sendChatMessage,
    fetchChatHistory,
  } = useSherlyStore();

  const [prompt, setPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isThinking]);

  // Auto-expand textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(140, Math.max(38, textareaRef.current.scrollHeight))}px`;
    }
  }, [prompt]);

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

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 1500);
    } catch (e) {
      console.warn('Failed to copy message:', e);
    }
  };

  // Helper to parse markdown code blocks
  const renderMessageContent = (text: string) => {
    if (!text.includes('```')) {
      return (
        <div className="whitespace-pre-wrap font-sans text-xs text-gray-200 leading-relaxed">
          {text}
        </div>
      );
    }

    const parts = text.split(/(```[\s\S]*?```)/g);
    return (
      <div className="flex flex-col gap-2">
        {parts.map((part, idx) => {
          if (part.startsWith('```') && part.endsWith('```')) {
            const firstLineBreak = part.indexOf('\n');
            const lang = firstLineBreak !== -1 ? part.slice(3, firstLineBreak).trim() : '';
            const code = firstLineBreak !== -1 ? part.slice(firstLineBreak + 1, -3) : part.slice(3, -3);
            return <CodeBlock key={idx} language={lang || 'python'} code={code.trim()} />;
          }
          if (!part.trim()) return null;
          return (
            <div key={idx} className="whitespace-pre-wrap font-sans text-xs text-gray-200 leading-relaxed">
              {part}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-surface overflow-hidden">
      {/* Conversation Timeline Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 max-w-4xl w-full mx-auto">
        {chatHistory.length === 0 && !isThinking && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 my-auto">
            <div className="w-10 h-10 rounded-xl bg-brand-surface border border-brand-border flex items-center justify-center text-purple-400 mb-3 shadow-sm shadow-brand/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-gray-200">Sherly Assistant Stream</h3>
            <p className="text-xs text-gray-400 max-w-sm mt-1 leading-relaxed">
              Ask questions, generate and optimize code, run workspace tasks, or inspect models.
            </p>
          </div>
        )}

        {chatHistory.map((msg, index) => (
          <React.Fragment key={index}>
            {/* User Message Card */}
            <div className="flex items-start gap-3 justify-end">
              <div className="bg-card border border-white/[0.06] rounded-xl p-3.5 max-w-2xl flex flex-col gap-2 shadow-sm">
                <p className="text-xs font-medium text-gray-100 leading-relaxed whitespace-pre-wrap">{msg.user_prompt}</p>
                {msg.attached_file && (
                  <div className="inline-flex items-center gap-1.5 bg-brand-surface border border-brand-border rounded px-2 py-0.5 text-[11px] font-mono text-purple-300 w-fit">
                    <FileText className="w-3 h-3 text-purple-400" />
                    <span>{msg.attached_file}</span>
                  </div>
                )}
              </div>
              <div className="w-7 h-7 rounded-full bg-white/[0.08] border border-white/10 flex items-center justify-center text-gray-200 text-xs font-bold shrink-0 mt-0.5">
                U
              </div>
            </div>

            {/* Assistant Response Card */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-brand flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5 shadow-sm shadow-brand/40">
                S
              </div>
              <div className="bg-card border border-white/[0.08] rounded-xl p-4 max-w-3xl text-xs text-gray-200 leading-relaxed flex flex-col gap-2 flex-1 shadow-sm">
                <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-purple-300">Sherly Assistant</span>
                    <Badge variant="brand" size="sm">Copilot</Badge>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCopy(msg.assistant_response, index)}
                    className="flex items-center gap-1 text-[10px] font-medium text-gray-400 hover:text-gray-200 transition bg-white/[0.04] hover:bg-white/[0.08] px-2 py-0.5 rounded border border-white/[0.06] focus-visible:outline-2 focus-visible:outline-brand"
                    title="Copy response"
                    aria-label="Copy assistant response"
                  >
                    {copiedIndex === index ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                {renderMessageContent(msg.assistant_response)}
              </div>
            </div>
          </React.Fragment>
        ))}

        {/* Task Status Indicator Node */}
        {isThinking && (
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-brand-surface border border-brand-border flex items-center justify-center text-purple-400 text-xs shrink-0">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            </div>
            <span className="text-xs text-gray-400 font-medium">Thinking and generating response...</span>
          </div>
        )}
      </div>

      {/* Docked Composer Bar */}
      <div className="p-4 bg-surface border-t border-white/[0.06]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-2 max-w-4xl mx-auto">
          {attachedFile && (
            <div className="flex items-center gap-2 text-xs text-purple-300 font-mono font-medium px-1">
              <FileText className="w-3.5 h-3.5 text-purple-400" />
              <span>Attached: {attachedFile}</span>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                className="text-gray-500 hover:text-rose-400 ml-1 text-xs"
                title="Remove attachment"
                aria-label="Remove attachment"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          )}

          <div className="bg-input border border-white/[0.10] focus-within:border-brand rounded-xl p-2.5 flex items-end gap-2 transition shadow-inner">
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
              className="flex-1 bg-transparent text-xs text-gray-100 placeholder-gray-500 focus:outline-none px-2 resize-none max-h-36 leading-relaxed py-1"
            />

            <IconButton
              icon={<Mic className="w-4 h-4" />}
              aria-label="Voice Input (Ctrl+Shift+L)"
              onClick={() => useSherlyStore.getState().setActiveView('voice')}
              size="md"
            />

            <button
              type="submit"
              disabled={!prompt.trim() || isThinking}
              className="w-7 h-7 bg-brand hover:bg-brand-hover disabled:opacity-30 text-white rounded-lg flex items-center justify-center font-bold transition shrink-0 shadow-sm shadow-brand/30 focus-visible:outline-2 focus-visible:outline-brand active:scale-95"
              title="Send Prompt"
              aria-label="Send Prompt"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

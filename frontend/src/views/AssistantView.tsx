import React, { useState, useEffect, useRef } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { User, Sparkles, Paperclip, Mic, Send, FileText, Loader2 } from 'lucide-react';

export const AssistantView: React.FC = () => {
  const {
    chatHistory,
    isThinking,
    sendChatMessage,
    fetchChatHistory,
  } = useSherlyStore();

  const [prompt, setPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory, isThinking]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim()) return;

    const currentPrompt = prompt;
    const currentAtt = attachedFile || undefined;
    setPrompt('');
    setAttachedFile(null);

    sendChatMessage(currentPrompt, currentAtt);
  };

  const handleFileAttach = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = (e: any) => {
      const file = e.target.files[0];
      if (file) {
        setAttachedFile(file.name);
      }
    };
    input.click();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0e0e15] overflow-hidden">
      {/* Conversation Timeline Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
        {chatHistory.length === 0 && !isThinking && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <div className="w-12 h-12 rounded-2xl bg-purple-900/30 border border-purple-500/30 flex items-center justify-center text-purple-400 mb-3">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-gray-300">Sherly Assistant Stream</h3>
            <p className="text-xs text-gray-500 max-w-sm mt-1">
              Ask questions, optimize code, run system tasks, or attach workspace files.
            </p>
          </div>
        )}

        {chatHistory.map((msg, index) => (
          <React.Fragment key={index}>
            {/* User Node */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center text-gray-300 text-xs shrink-0 mt-1">
                <User className="w-3.5 h-3.5" />
              </div>
              <div className="bg-[#13131e] border border-white/10 rounded-xl p-3.5 max-w-2xl flex flex-col gap-2">
                <p className="text-xs font-semibold text-gray-100">{msg.user_prompt}</p>
                {msg.attached_file && (
                  <div className="inline-flex items-center gap-1.5 bg-white/5 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-gray-400 w-fit">
                    <FileText className="w-3 h-3 text-purple-400" />
                    <span>{msg.attached_file}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Assistant Node */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center text-white text-xs font-extrabold shrink-0 mt-1">
                S
              </div>
              <div className="bg-[#13131e] border border-purple-500/30 rounded-xl p-4 max-w-2xl text-xs text-gray-200 leading-relaxed">
                {msg.assistant_response}
              </div>
            </div>
          </React.Fragment>
        ))}

        {/* Thinking Indicator Node */}
        {isThinking && (
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-purple-900/30 border border-purple-500/30 flex items-center justify-center text-purple-400 text-xs shrink-0">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            </div>
            <span className="text-xs text-gray-400 font-medium">Thinking & analyzing...</span>
          </div>
        )}
      </div>

      {/* Floating Prompt Bar */}
      <div className="p-4 bg-[#0e0e15] border-t border-white/5">
        <form onSubmit={handleSubmit} className="flex flex-col gap-2 max-w-4xl mx-auto">
          {attachedFile && (
            <div className="flex items-center gap-2 text-xs text-purple-300 font-semibold px-2">
              <FileText className="w-3.5 h-3.5" />
              <span>Attached: {attachedFile}</span>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                className="text-gray-500 hover:text-red-400 ml-1"
              >
                ✕
              </button>
            </div>
          )}

          <div className="bg-[#11111a] border border-white/10 focus-within:border-purple-500/50 rounded-2xl p-2 flex items-center gap-2">
            <button
              type="button"
              onClick={handleFileAttach}
              className="p-1.5 text-gray-400 hover:text-gray-200 transition"
              title="Attach File"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask Sherly anything..."
              className="flex-1 bg-transparent text-xs text-gray-100 placeholder-gray-500 focus:outline-none px-2"
            />

            <button
              type="button"
              onClick={() => useSherlyStore.getState().setActiveView('voice')}
              className="p-1.5 text-gray-400 hover:text-gray-200 transition"
              title="Voice Input"
            >
              <Mic className="w-4 h-4" />
            </button>

            <button
              type="submit"
              disabled={!prompt.trim()}
              className="w-8 h-8 bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white rounded-xl flex items-center justify-center font-bold transition shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

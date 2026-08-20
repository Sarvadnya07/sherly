import React from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Settings2, Minus, Square, X } from 'lucide-react';
import { IconButton } from './ui/Button';

export const HeaderBar: React.FC = () => {
  const { currentTitle, currentModel, setActiveView } = useSherlyStore();

  const handleMinimize = () => {
    if (typeof window !== 'undefined' && (window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().minimize();
    }
  };

  const handleMaximize = () => {
    if (typeof window !== 'undefined' && (window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().toggleMaximize();
    }
  };

  const handleClose = () => {
    if (typeof window !== 'undefined' && (window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().close();
    }
  };

  const titleParts = currentTitle.includes('—')
    ? currentTitle.split('—').map((s) => s.trim())
    : [currentTitle];

  return (
    <header className="h-10 bg-sidebar border-b border-white/[0.06] px-3 flex items-center justify-between select-none data-tauri-drag-region shrink-0">
      {/* Brand Logo & Breadcrumb */}
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 rounded bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-subtle shrink-0">
          <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
          </svg>
        </div>
        <span className="text-[13px] font-semibold text-zinc-200 tracking-tight">Sherly</span>
        {titleParts.length > 1 && (
          <>
            <span className="text-zinc-600 text-xs">/</span>
            <span className="text-xs font-normal text-zinc-400 truncate max-w-[200px]">{titleParts[1]}</span>
          </>
        )}
      </div>

      {/* Right Actions & Model Status Badge */}
      <div className="flex items-center gap-1.5">
        {/* Model Status Pill */}
        <button
          type="button"
          onClick={() => setActiveView('models')}
          className="h-6 px-2 rounded-md bg-zinc-900/90 hover:bg-zinc-800 border border-white/[0.08] text-zinc-300 text-[11px] font-mono inline-flex items-center gap-1.5 transition active:scale-95 focus-visible:outline-2 focus-visible:outline-indigo-500 cursor-pointer"
          title="Current Model (Click to Configure)"
          aria-label={`Current Model: ${currentModel || 'No Model Active'}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_5px_rgba(52,211,153,0.7)]" />
          <span className="truncate max-w-[160px]">{currentModel ? `${currentModel}` : 'Select Model'}</span>
        </button>

        {/* Settings Action */}
        <IconButton
          icon={<Settings2 className="w-3.5 h-3.5" />}
          aria-label="Settings and Model Management"
          onClick={() => setActiveView('models')}
          size="sm"
        />

        {/* Window Controls */}
        <div className="flex items-center gap-0.5 ml-1 pl-1 border-l border-white/[0.06]">
          <IconButton
            icon={<Minus className="w-3 h-3" />}
            aria-label="Minimize Window"
            onClick={handleMinimize}
            size="sm"
          />
          <IconButton
            icon={<Square className="w-2.5 h-2.5" />}
            aria-label="Maximize Window"
            onClick={handleMaximize}
            size="sm"
          />
          <IconButton
            icon={<X className="w-3 h-3" />}
            aria-label="Close Window"
            onClick={handleClose}
            variant="danger"
            size="sm"
          />
        </div>
      </div>
    </header>
  );
};

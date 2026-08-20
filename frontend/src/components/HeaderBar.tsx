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
    <header className="h-[42px] bg-canvas border-b border-white/[0.07] px-3.5 flex items-center justify-between select-none data-tauri-drag-region shrink-0">
      {/* Brand Logo & Breadcrumb */}
      <div className="flex items-center gap-2.5">
        <div className="w-5 h-5 rounded bg-brand flex items-center justify-center shadow-subtle shrink-0">
          <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
          </svg>
        </div>
        <span className="text-xs font-semibold text-gray-100 tracking-tight">Sherly</span>
        {titleParts.length > 1 && (
          <>
            <span className="text-xs text-gray-600">/</span>
            <span className="text-xs font-medium text-purple-300/90 truncate max-w-[200px]">{titleParts[1]}</span>
          </>
        )}
      </div>

      {/* Right Actions & Status Badge */}
      <div className="flex items-center gap-2">
        {/* Model Status Pill Badge */}
        <button
          type="button"
          onClick={() => setActiveView('models')}
          className="h-6 px-2.5 rounded-full bg-brand-surface hover:bg-brand/20 border border-brand-border text-purple-300 text-[11px] font-mono font-medium inline-flex items-center gap-1.5 transition active:scale-95 focus-visible:outline-2 focus-visible:outline-brand cursor-pointer"
          title="Current Model (Click to Configure)"
          aria-label={`Current Model: ${currentModel || 'No Model Active'}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]" />
          <span className="truncate max-w-[180px]">{currentModel ? `${currentModel} • Local` : 'No Model Active'}</span>
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

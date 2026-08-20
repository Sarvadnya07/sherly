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
    <header className="h-11 bg-sidebar border-b border-border-subtle px-3.5 flex items-center justify-between select-none data-tauri-drag-region shrink-0">
      {/* Brand Logo & Breadcrumb */}
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="w-5 h-5 rounded-md bg-brand flex items-center justify-center shadow-subtle shrink-0">
          <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
          </svg>
        </div>
        <span className="text-sm font-semibold text-txt-primary tracking-tight shrink-0">Sherly</span>
        {titleParts.length > 1 && (
          <>
            <span className="text-txt-muted text-xs">/</span>
            <span className="text-xs font-normal text-txt-secondary truncate max-w-[200px]">{titleParts[1]}</span>
          </>
        )}
      </div>

      {/* Right Actions & Model Status Badge */}
      <div className="flex items-center gap-2">
        {/* Model Status Pill */}
        <button
          type="button"
          onClick={() => setActiveView('models')}
          className="h-7 px-2.5 rounded-md bg-card hover:bg-card-hover border border-border-subtle text-txt-secondary hover:text-txt-primary text-xs font-mono inline-flex items-center gap-1.5 transition active:scale-95 focus-visible:outline-2 focus-visible:outline-brand cursor-pointer"
          title="Current Model (Click to Configure)"
          aria-label={`Current Model: ${currentModel || 'No Model Selected'}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-status-success shadow-[0_0_5px_rgba(16,185,129,0.7)] shrink-0" />
          <span className="truncate max-w-[180px]">{currentModel || 'Select Model'}</span>
        </button>

        {/* Settings Action */}
        <IconButton
          icon={<Settings2 className="w-4 h-4" />}
          aria-label="Settings and Model Management"
          onClick={() => setActiveView('models')}
          size="md"
        />

        {/* Window Controls */}
        <div className="flex items-center gap-1 ml-1 pl-1.5 border-l border-border-subtle">
          <IconButton
            icon={<Minus className="w-3.5 h-3.5" />}
            aria-label="Minimize Window"
            onClick={handleMinimize}
            size="sm"
          />
          <IconButton
            icon={<Square className="w-3 h-3" />}
            aria-label="Maximize Window"
            onClick={handleMaximize}
            size="sm"
          />
          <IconButton
            icon={<X className="w-3.5 h-3.5" />}
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

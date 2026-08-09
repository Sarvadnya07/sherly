import React from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Settings, Minus, Square, X } from 'lucide-react';

export const HeaderBar: React.FC = () => {
  const { currentTitle, currentModel, setActiveView } = useSherlyStore();

  const handleMinimize = () => {
    if ((window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().minimize();
    }
  };

  const handleMaximize = () => {
    if ((window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().toggleMaximize();
    }
  };

  const handleClose = () => {
    if ((window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().close();
    }
  };

  return (
    <header className="h-12 bg-[#09090d] border-b border-white/10 px-4 flex items-center justify-between select-none data-tauri-drag-region">
      {/* Title & Dot Pattern */}
      <div className="flex items-center gap-3">
        <span className="text-lg">🌁</span>
        <h1 className="text-sm font-bold text-gray-100 tracking-wide">{currentTitle}</h1>
        <span className="text-xs text-white/15 tracking-[4px] font-mono hidden md:inline-block">
          • • • • • • • • • • • •
        </span>
      </div>

      {/* Right Actions & Badge */}
      <div className="flex items-center gap-3">
        {/* Model Badge */}
        <button
          onClick={() => setActiveView('models')}
          className="bg-purple-900/30 text-purple-300 border border-purple-500/30 hover:bg-purple-900/50 hover:text-purple-200 px-3 py-1 rounded-full text-xs font-semibold transition"
        >
          {currentModel ? `${currentModel} • Local` : 'No Model Selected'}
        </button>

        {/* Settings Gear */}
        <button
          onClick={() => setActiveView('models')}
          className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-white/10 rounded-md transition"
          title="Settings / Models"
        >
          <Settings className="w-4 h-4" />
        </button>

        {/* Window Controls */}
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={handleMinimize}
            className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-white/10 rounded-md transition"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleMaximize}
            className="p-1.5 text-gray-400 hover:text-gray-100 hover:bg-white/10 rounded-md transition"
          >
            <Square className="w-3 h-3" />
          </button>
          <button
            onClick={handleClose}
            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/20 rounded-md transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};

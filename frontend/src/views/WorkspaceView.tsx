import React, { useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Check, X, Trash2, GitBranch, Terminal as TerminalIcon, FileCode2 } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';

export const WorkspaceView: React.FC = () => {
  const {
    activeFilePath,
    activeFileContent,
    currentModel,
    diffMode,
  } = useSherlyStore();

  const [localDiffMode, setLocalDiffMode] = useState(diffMode);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    'Sherly Workspace Terminal [Ready]',
  ]);
  const [terminalCmd, setTerminalCmd] = useState('');
  const [isExec, setIsExec] = useState(false);

  const handleRunCommand = async (cmd: string) => {
    if (!cmd.trim()) return;
    setTerminalOutput((prev) => [...prev, `➔ $ ${cmd}`]);
    setIsExec(true);
    try {
      const res = await api.runTerminal(cmd);
      setTerminalOutput((prev) => [
        ...prev,
        res.output || '[No Output]',
        `[Process exited with code ${res.exit_code}]`,
      ]);
    } catch (e: any) {
      setTerminalOutput((prev) => [...prev, `[Error: ${e.message}]`]);
    } finally {
      setIsExec(false);
    }
  };

  const handleTerminalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (terminalCmd.trim()) {
      const c = terminalCmd;
      setTerminalCmd('');
      handleRunCommand(c);
    }
  };

  const lines = (activeFileContent || '').split('\n');

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas overflow-hidden">
      {/* Editor & Diff Section */}
      <div className="flex-1 flex flex-col p-3 gap-2 overflow-hidden">
        {/* File Tabs & Actions Bar */}
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-1 select-none shrink-0">
          <div className="flex items-center gap-1">
            {activeFilePath ? (
              <div className="bg-zinc-900 text-zinc-200 border border-white/[0.08] border-b-0 rounded-t-md px-3 py-1 text-xs font-mono flex items-center gap-2 shadow-subtle">
                <FileCode2 className="w-3.5 h-3.5 text-sky-400" />
                <span className="font-medium">{activeFilePath}</span>
                <button
                  type="button"
                  onClick={() => useSherlyStore.setState({ activeFilePath: null, activeFileContent: '' })}
                  className="text-zinc-500 hover:text-zinc-300 text-xs p-0.5 rounded focus-visible:outline-1 cursor-pointer"
                  title="Close file"
                  aria-label="Close file"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <span className="text-xs text-zinc-500 italic px-1">No file open</span>
            )}
          </div>

          {localDiffMode && (
            <div className="flex items-center gap-1.5">
              <Button
                variant="primary"
                size="sm"
                onClick={async () => {
                  try {
                    await api.approveAction('preview_last');
                  } catch (e) {
                    console.warn(e);
                  }
                  setLocalDiffMode(false);
                }}
                icon={<Check className="w-3 h-3" />}
              >
                Accept
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  try {
                    await api.rejectAction('preview_last');
                  } catch (e) {
                    console.warn(e);
                  }
                  setLocalDiffMode(false);
                }}
                icon={<X className="w-3 h-3" />}
              >
                Reject
              </Button>
            </div>
          )}
        </div>

        {/* Code Canvas */}
        <div className="flex-1 bg-zinc-950 border border-white/[0.06] rounded-lg overflow-hidden flex flex-col font-mono text-xs shadow-inner">
          <div className="flex-1 overflow-auto p-3 leading-relaxed">
            {lines.length > 0 && activeFilePath ? (
              lines.map((line, idx) => (
                <div key={idx} className="flex items-center hover:bg-white/[0.02] group">
                  <span className="w-10 text-right pr-3 text-zinc-600 group-hover:text-zinc-400 select-none text-[11px]">
                    {idx + 1}
                  </span>
                  <pre className="text-zinc-300 font-mono text-xs whitespace-pre">{line || ' '}</pre>
                </div>
              ))
            ) : (
              <div className="text-zinc-600 italic p-8 text-center my-auto">
                Select a file from Explorer to inspect or edit code.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Integrated Terminal Panel */}
      <div className="h-44 bg-zinc-950 border-t border-white/[0.06] flex flex-col font-mono shrink-0">
        {/* Terminal Header */}
        <div className="bg-zinc-900/50 border-b border-white/[0.04] px-3 py-1 flex items-center justify-between select-none">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-zinc-400">
            <TerminalIcon className="w-3.5 h-3.5 text-zinc-400" />
            <span>TERMINAL</span>
          </div>
          <button
            type="button"
            onClick={() => setTerminalOutput([])}
            className="text-zinc-500 hover:text-zinc-300 text-[11px] flex items-center gap-1 transition focus-visible:outline-1 cursor-pointer"
            title="Clear output"
            aria-label="Clear terminal output"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        </div>

        {/* Terminal Output Stream */}
        <div className="flex-1 p-3 overflow-y-auto text-xs text-emerald-400 flex flex-col gap-0.5">
          {terminalOutput.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap">{line}</div>
          ))}
        </div>

        {/* Command Input Prompt */}
        <form onSubmit={handleTerminalSubmit} className="bg-zinc-900/40 border-t border-white/[0.04] px-3 py-1.5 flex items-center gap-2">
          <span className="text-emerald-400 font-bold text-xs">➔ $</span>
          <input
            type="text"
            value={terminalCmd}
            disabled={isExec}
            onChange={(e) => setTerminalCmd(e.target.value)}
            placeholder="Type command (e.g. pytest tests/ -q)..."
            className="flex-1 bg-transparent text-xs text-zinc-200 focus:outline-none font-mono placeholder-zinc-600 disabled:opacity-50"
          />
        </form>
      </div>

      {/* Status Bar Footer */}
      <footer className="h-6 bg-sidebar border-t border-white/[0.06] px-3 flex items-center justify-between text-[10px] text-zinc-500 font-mono select-none shrink-0">
        <div className="flex items-center gap-1.5">
          <GitBranch className="w-3 h-3 text-zinc-400" />
          <span>main</span>
        </div>
        <div>
          <span>UTF-8   Python 3.13   [{currentModel || 'qwen2.5-coder:3b'}]</span>
        </div>
      </footer>
    </div>
  );
};

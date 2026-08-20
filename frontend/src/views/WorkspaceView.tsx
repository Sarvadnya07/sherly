import React, { useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Check, X, Trash2, GitBranch, Terminal as TerminalIcon, FileCode } from 'lucide-react';
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
    <div className="flex-1 flex flex-col h-full bg-surface overflow-hidden">
      {/* Editor & Diff Section */}
      <div className="flex-1 flex flex-col p-3.5 gap-2.5 overflow-hidden">
        {/* File Tabs & Actions Bar */}
        <div className="flex items-center justify-between border-b border-white/[0.07] pb-1.5 select-none shrink-0">
          <div className="flex items-center gap-2">
            {activeFilePath ? (
              <div className="bg-canvas text-purple-300 border border-white/[0.08] border-b-0 rounded-t-md px-3 py-1 text-xs font-mono font-medium flex items-center gap-2 shadow-subtle">
                <FileCode className="w-3.5 h-3.5 text-sky-400" />
                <span>{activeFilePath}</span>
                <button
                  type="button"
                  onClick={() => useSherlyStore.setState({ activeFilePath: null, activeFileContent: '' })}
                  className="text-gray-500 hover:text-gray-300 text-xs p-0.5 rounded focus-visible:outline-1 cursor-pointer"
                  title="Close file"
                  aria-label="Close file"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <span className="text-xs text-gray-500 italic">No file open</span>
            )}
          </div>

          {localDiffMode && (
            <div className="flex items-center gap-2">
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
                icon={<Check className="w-3.5 h-3.5" />}
              >
                Accept (Ctrl+Enter)
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
                icon={<X className="w-3.5 h-3.5" />}
              >
                Reject (Esc)
              </Button>
            </div>
          )}
        </div>

        {/* Code Canvas */}
        <div className="flex-1 bg-canvas border border-white/[0.08] rounded-lg overflow-hidden flex flex-col font-mono text-xs shadow-inner">
          <div className="flex-1 overflow-auto p-3 leading-relaxed">
            {lines.length > 0 && activeFilePath ? (
              lines.map((line, idx) => (
                <div key={idx} className="flex items-center hover:bg-white/[0.02] group">
                  <span className="w-10 text-right pr-3 text-gray-600 group-hover:text-gray-400 select-none text-[11px]">
                    {idx + 1}
                  </span>
                  <pre className="text-gray-300 font-mono text-xs whitespace-pre">{line || ' '}</pre>
                </div>
              ))
            ) : (
              <div className="text-gray-500 italic p-6 text-center my-auto">
                Select a file from Project Explorer to inspect or edit source code.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Integrated Terminal Panel */}
      <div className="h-44 bg-canvas border-t border-white/[0.08] flex flex-col font-mono shrink-0">
        {/* Terminal Header */}
        <div className="bg-white/[0.02] border-b border-white/[0.04] px-3.5 py-1.5 flex items-center justify-between select-none">
          <div className="flex items-center gap-2 text-[11px] font-bold">
            <span className="text-purple-400 inline-flex items-center gap-1.5">
              <TerminalIcon className="w-3.5 h-3.5" />
              <span>TERMINAL</span>
            </span>
          </div>
          <button
            type="button"
            onClick={() => setTerminalOutput([])}
            className="text-gray-500 hover:text-gray-300 text-[11px] flex items-center gap-1 transition focus-visible:outline-1 cursor-pointer"
            title="Clear output"
            aria-label="Clear terminal output"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        </div>

        {/* Terminal Output Stream */}
        <div className="flex-1 p-3 overflow-y-auto text-xs text-emerald-400 flex flex-col gap-1">
          {terminalOutput.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap">{line}</div>
          ))}
        </div>

        {/* Command Input Prompt */}
        <form onSubmit={handleTerminalSubmit} className="bg-white/[0.02] border-t border-white/[0.04] px-3 py-1.5 flex items-center gap-2">
          <span className="text-sky-400 font-bold text-xs">➔ $</span>
          <input
            type="text"
            value={terminalCmd}
            disabled={isExec}
            onChange={(e) => setTerminalCmd(e.target.value)}
            placeholder="Type command (e.g. python main.py)..."
            className="flex-1 bg-transparent text-xs text-gray-200 focus:outline-none font-mono placeholder-gray-600 disabled:opacity-50"
          />
        </form>
      </div>

      {/* Status Bar Footer */}
      <footer className="h-6 bg-canvas border-t border-white/[0.07] px-3 flex items-center justify-between text-[10px] text-gray-500 font-mono select-none shrink-0">
        <div className="flex items-center gap-2">
          <GitBranch className="w-3 h-3 text-purple-400" />
          <span>git: main</span>
        </div>
        <div>
          <span>UTF-8   Python 3.13   ● Sherly Active [{currentModel || 'Qwen2.5-Coder'}]</span>
        </div>
      </footer>
    </div>
  );
};

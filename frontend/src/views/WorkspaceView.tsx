import React, { useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Check, X, Trash2, Terminal as TerminalIcon, FileCode2 } from 'lucide-react';
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
        <div className="flex items-center justify-between border-b border-border-subtle pb-1 select-none shrink-0">
          <div className="flex items-center gap-1 min-w-0">
            {activeFilePath ? (
              <div className="bg-card text-txt-primary border border-border-subtle border-b-0 rounded-t-md px-3 py-1 text-xs font-mono flex items-center gap-2 shadow-subtle">
                <FileCode2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                <span className="font-medium truncate max-w-xs">{activeFilePath}</span>
                <button
                  type="button"
                  onClick={() => useSherlyStore.setState({ activeFilePath: null, activeFileContent: '' })}
                  className="text-txt-muted hover:text-txt-primary text-xs p-0.5 rounded focus-visible:outline-1 cursor-pointer shrink-0"
                  title="Close file"
                  aria-label="Close file"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <span className="text-xs text-txt-muted italic px-1">No file open</span>
            )}
          </div>

          {localDiffMode && (
            <div className="flex items-center gap-1.5 shrink-0">
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
                icon={<X className="w-3 h-3" />}
              >
                Reject (Esc)
              </Button>
            </div>
          )}
        </div>

        {/* Code Canvas with Native Text Selection */}
        <div className="flex-1 bg-canvas border border-border-subtle rounded-lg overflow-hidden flex flex-col font-mono text-xs shadow-inner select-text">
          <div className="flex-1 overflow-auto p-3 leading-relaxed select-text">
            {lines.length > 0 && activeFilePath ? (
              lines.map((line, idx) => (
                <div key={idx} className="flex items-center hover:bg-white/[0.02] group select-text">
                  <span className="w-10 text-right pr-3 text-txt-muted group-hover:text-txt-secondary select-none text-[11px]">
                    {idx + 1}
                  </span>
                  <pre className="text-txt-primary font-mono text-xs whitespace-pre select-text">{line || ' '}</pre>
                </div>
              ))
            ) : (
              <div className="text-txt-muted italic p-8 text-center my-auto select-none">
                Select a file from Explorer to inspect or edit code.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Integrated Terminal Panel */}
      <div className="h-44 bg-surface border-t border-border-subtle flex flex-col font-mono shrink-0">
        {/* Terminal Header */}
        <div className="bg-card border-b border-border-subtle px-3 py-1 flex items-center justify-between select-none">
          <div className="flex items-center gap-1.5 text-xs font-medium text-txt-secondary">
            <TerminalIcon className="w-3.5 h-3.5 text-txt-muted" />
            <span>TERMINAL</span>
          </div>
          <button
            type="button"
            onClick={() => setTerminalOutput([])}
            className="text-txt-muted hover:text-txt-primary text-xs flex items-center gap-1 transition focus-visible:outline-1 cursor-pointer"
            title="Clear output"
            aria-label="Clear terminal output"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        </div>

        {/* Terminal Output Stream (Native Text Selection) */}
        <div className="flex-1 p-3 overflow-y-auto text-xs text-status-success flex flex-col gap-0.5 select-text font-mono">
          {terminalOutput.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap select-text">{line}</div>
          ))}
        </div>

        {/* Command Input Prompt */}
        <form onSubmit={handleTerminalSubmit} className="bg-canvas border-t border-border-subtle px-3 py-1.5 flex items-center gap-2">
          <span className="text-status-success font-bold text-xs font-mono">➔ $</span>
          <input
            type="text"
            value={terminalCmd}
            disabled={isExec}
            onChange={(e) => setTerminalCmd(e.target.value)}
            placeholder="Type command (e.g. pytest tests/ -q)..."
            className="flex-1 bg-transparent text-xs text-txt-primary focus:outline-none font-mono placeholder-txt-muted disabled:opacity-50 select-text"
          />
        </form>
      </div>

      {/* Status Bar Footer (Real backend metadata only) */}
      <footer className="h-6 bg-sidebar border-t border-border-subtle px-3 flex items-center justify-between text-[11px] text-txt-muted font-mono select-none shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
          <span>UTF-8</span>
        </div>
        <div>
          <span>Model: [{currentModel || 'No Model Active'}]</span>
        </div>
      </footer>
    </div>
  );
};

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import {
  Check,
  X,
  Trash2,
  Terminal as TerminalIcon,
  FileCode2,
  Save,
  RotateCcw,
  GitBranch,
  SplitSquareVertical,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import { Button, IconButton } from '../components/ui/Button';

export const WorkspaceView: React.FC = () => {
  const {
    openTabs,
    activeFilePath,
    activeFileContent,
    isDirty,
    diffMode,
    diffOldCode,
    diffNewCode,
    activeActionId,
    openFile,
    closeTab,
    updateActiveContent,
    saveActiveFile,
    setDiffMode,
    undoLastAction,
  } = useSherlyStore();

  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    'Sherly Workspace Terminal [Ready]',
  ]);
  const [terminalCmd, setTerminalCmd] = useState('');
  const [isExec, setIsExec] = useState(false);
  const [cmdHistory, setCmdHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [cursorPos, setCursorPos] = useState({ line: 1, col: 1 });
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal to bottom
  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [terminalOutput]);

  // Global Workspace Shortcuts (Ctrl+S, Ctrl+W, Ctrl+Enter, Esc)
  useEffect(() => {
    const handleKeys = async (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (activeFilePath && isDirty) {
          setSaveStatus('saving');
          const ok = await saveActiveFile();
          setSaveStatus(ok ? 'saved' : 'error');
          setTimeout(() => setSaveStatus('idle'), 2000);
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'w') {
        e.preventDefault();
        if (activeFilePath) {
          closeTab(activeFilePath);
        }
      } else if (diffMode && (e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleAcceptDiff();
      } else if (diffMode && e.key === 'Escape') {
        e.preventDefault();
        handleRejectDiff();
      }
    };

    window.addEventListener('keydown', handleKeys);
    return () => window.removeEventListener('keydown', handleKeys);
  }, [activeFilePath, isDirty, diffMode, saveActiveFile, closeTab]);

  const handleRunCommand = async (cmd: string) => {
    if (!cmd.trim()) return;
    setTerminalOutput((prev) => [...prev.slice(-400), `➔ $ ${cmd}`]);
    setCmdHistory((prev) => [...prev, cmd]);
    setHistoryIdx(-1);
    setIsExec(true);
    try {
      const res = await api.runTerminal(cmd);
      setTerminalOutput((prev) => [
        ...prev.slice(-400),
        res.output || '[No Output]',
        `[Process exited with code ${res.exit_code}]`,
      ]);
    } catch (e: any) {
      setTerminalOutput((prev) => [...prev.slice(-400), `[Error: ${e.message}]`]);
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

  const handleTerminalKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (cmdHistory.length > 0) {
        const nextIdx = historyIdx === -1 ? cmdHistory.length - 1 : Math.max(0, historyIdx - 1);
        setHistoryIdx(nextIdx);
        setTerminalCmd(cmdHistory[nextIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx !== -1) {
        const nextIdx = historyIdx + 1;
        if (nextIdx < cmdHistory.length) {
          setHistoryIdx(nextIdx);
          setTerminalCmd(cmdHistory[nextIdx]);
        } else {
          setHistoryIdx(-1);
          setTerminalCmd('');
        }
      }
    }
  };

  const handleAcceptDiff = async () => {
    if (activeActionId) {
      try {
        await api.applyPreview(activeActionId);
        setDiffMode(false);
        if (activeFilePath) openFile(activeFilePath);
      } catch (e) {
        console.error('Error applying preview:', e);
      }
    } else {
      setDiffMode(false);
    }
  };

  const handleRejectDiff = async () => {
    if (activeActionId) {
      try {
        await api.rejectAction(activeActionId);
      } catch (e) {
        console.warn('Error rejecting preview:', e);
      }
    }
    setDiffMode(false);
  };

  const handleUndo = async () => {
    try {
      const msg = await undoLastAction();
      setTerminalOutput((prev) => [...prev, `➔ [Undo Result]: ${msg}`]);
      if (activeFilePath) openFile(activeFilePath);
    } catch (e: any) {
      setTerminalOutput((prev) => [...prev, `➔ [Undo Error]: ${e.message}`]);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateActiveContent(e.target.value);
  };

  const handleSelectionChange = () => {
    if (textareaRef.current) {
      const text = textareaRef.current.value.slice(0, textareaRef.current.selectionStart);
      const lines = text.split('\n');
      const line = lines.length;
      const col = lines[lines.length - 1].length + 1;
      setCursorPos({ line, col });
    }
  };

  const lines = useMemo(() => (activeFileContent || '').split('\n'), [activeFileContent]);

  // Generate simple diff lines
  const diffLines = useMemo(() => {
    if (!diffMode) return [];
    const oldLines = diffOldCode.split('\n');
    const newLines = diffNewCode.split('\n');
    const result: Array<{ type: 'same' | 'added' | 'removed'; text: string }> = [];

    let i = 0;
    let j = 0;
    while (i < oldLines.length || j < newLines.length) {
      if (i < oldLines.length && j < newLines.length && oldLines[i] === newLines[j]) {
        result.push({ type: 'same', text: oldLines[i] });
        i++;
        j++;
      } else {
        if (i < oldLines.length) {
          result.push({ type: 'removed', text: oldLines[i] });
          i++;
        }
        if (j < newLines.length) {
          result.push({ type: 'added', text: newLines[j] });
          j++;
        }
      }
    }
    return result;
  }, [diffMode, diffOldCode, diffNewCode]);

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas overflow-hidden">
      {/* Multi-Tab & Action Header Bar */}
      <div className="bg-sidebar border-b border-border-subtle flex items-center justify-between px-2 pt-1.5 select-none shrink-0 overflow-x-auto">
        {/* Open Tabs List */}
        <div className="flex items-center gap-1 min-w-0 flex-1 overflow-x-auto scrollbar-none">
          {openTabs.length > 0 ? (
            openTabs.map((tab) => {
              const isActive = tab.path === activeFilePath;
              return (
                <div
                  key={tab.path}
                  onClick={() => openFile(tab.path)}
                  className={`group px-3 py-1.5 rounded-t-md text-xs font-mono flex items-center gap-2 cursor-pointer transition border border-b-0 ${
                    isActive
                      ? 'bg-card text-txt-primary border-border-medium font-semibold shadow-subtle'
                      : 'bg-transparent text-txt-muted hover:text-txt-secondary border-transparent'
                  }`}
                >
                  <FileCode2 className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-sky-400' : 'text-txt-muted'}`} />
                  <span className="truncate max-w-[130px]">{tab.name}</span>

                  {tab.isDirty && (
                    <span className="w-1.5 h-1.5 rounded-full bg-status-warning shrink-0" title="Unsaved changes" />
                  )}

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      closeTab(tab.path);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-txt-muted hover:text-txt-primary p-0.5 rounded transition cursor-pointer shrink-0"
                    title="Close tab (Ctrl+W)"
                    aria-label={`Close tab ${tab.name}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              );
            })
          ) : (
            <span className="text-xs text-txt-muted italic px-2 py-1">No tabs open</span>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5 pb-1 shrink-0 ml-2">
          {activeFilePath && (
            <Button
              variant="secondary"
              size="sm"
              onClick={async () => {
                setSaveStatus('saving');
                const ok = await saveActiveFile();
                setSaveStatus(ok ? 'saved' : 'error');
                setTimeout(() => setSaveStatus('idle'), 2000);
              }}
              disabled={!isDirty}
              icon={<Save className="w-3 h-3" />}
            >
              {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved' : 'Save (Ctrl+S)'}
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={handleUndo}
            icon={<RotateCcw className="w-3 h-3" />}
            title="Undo last action"
          >
            Undo
          </Button>

          {diffMode && (
            <div className="flex items-center gap-1 bg-card border border-border-medium rounded px-1.5 py-0.5 shadow-subtle">
              <Button
                variant="primary"
                size="sm"
                onClick={handleAcceptDiff}
                icon={<Check className="w-3 h-3" />}
              >
                Accept (Ctrl+Enter)
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRejectDiff}
                icon={<X className="w-3 h-3" />}
              >
                Reject (Esc)
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Editor & Diff Main Canvas */}
      <div className="flex-1 flex flex-col p-2.5 overflow-hidden gap-2">
        {diffMode ? (
          /* Patch Diff View */
          <div className="flex-1 bg-card border border-border-subtle rounded-lg flex flex-col font-mono text-xs overflow-hidden shadow-inner select-text">
            <div className="bg-sidebar border-b border-border-subtle px-3 py-1.5 flex items-center justify-between text-txt-secondary text-[11px] select-none">
              <div className="flex items-center gap-1.5 font-semibold">
                <SplitSquareVertical className="w-3.5 h-3.5 text-brand" />
                <span>AI Proposed Changes Diff Preview</span>
              </div>
              <span className="text-txt-muted font-sans">Review carefully before accepting</span>
            </div>

            <div className="flex-1 overflow-auto p-3 flex flex-col gap-0.5 select-text leading-relaxed">
              {diffLines.map((dl, idx) => (
                <div
                  key={idx}
                  className={`flex items-start px-2 py-0.5 rounded font-mono text-xs ${
                    dl.type === 'added'
                      ? 'bg-status-success/15 text-emerald-400'
                      : dl.type === 'removed'
                      ? 'bg-status-danger/15 text-rose-400 line-through opacity-80'
                      : 'text-txt-primary hover:bg-white/[0.02]'
                  }`}
                >
                  <span className="w-6 shrink-0 text-txt-muted select-none font-mono text-[11px]">
                    {dl.type === 'added' ? '+' : dl.type === 'removed' ? '-' : ' '}
                  </span>
                  <pre className="whitespace-pre-wrap font-mono text-xs select-text flex-1">{dl.text || ' '}</pre>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Code Viewer & Editor */
          <div className="flex-1 bg-card border border-border-subtle rounded-lg overflow-hidden flex flex-col font-mono text-xs shadow-inner relative">
            {activeFilePath ? (
              <div className="flex-1 flex overflow-hidden">
                {/* Line Gutter */}
                <div className="w-12 bg-sidebar border-r border-border-subtle py-3 pr-2 text-right text-txt-muted select-none font-mono text-xs shrink-0 overflow-hidden leading-relaxed">
                  {lines.map((_, idx) => (
                    <div key={idx} className="h-5 text-[11px] text-txt-muted font-mono leading-5">
                      {idx + 1}
                    </div>
                  ))}
                </div>

                {/* Editable Monospace Textarea */}
                <textarea
                  ref={textareaRef}
                  value={activeFileContent}
                  onChange={handleTextareaChange}
                  onKeyUp={handleSelectionChange}
                  onClick={handleSelectionChange}
                  spellCheck={false}
                  className="flex-1 bg-transparent text-txt-primary font-mono text-xs p-3 leading-5 resize-none focus:outline-none overflow-auto whitespace-pre select-text"
                  placeholder="Type code here..."
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-txt-muted my-auto select-none p-8">
                <FileCode2 className="w-10 h-10 text-txt-muted/50 mb-3" />
                <h4 className="text-xs font-semibold text-txt-secondary">No File Open</h4>
                <p className="text-[11px] text-txt-muted max-w-xs mt-1">
                  Select a file from the Explorer in the sidebar to inspect or edit source code.
                </p>
              </div>
            )}
          </div>
        )}
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

        {/* Terminal Output Stream (Capped Buffer, Native Text Selection) */}
        <div className="flex-1 p-3 overflow-y-auto text-xs text-status-success flex flex-col gap-0.5 select-text font-mono">
          {terminalOutput.map((line, index) => (
            <div key={index} className="whitespace-pre-wrap select-text">{line}</div>
          ))}
          <div ref={terminalEndRef} />
        </div>

        {/* Command Input Prompt */}
        <form onSubmit={handleTerminalSubmit} className="bg-canvas border-t border-border-subtle px-3 py-1.5 flex items-center gap-2">
          <span className="text-status-success font-bold text-xs font-mono">➔ $</span>
          <input
            type="text"
            value={terminalCmd}
            disabled={isExec}
            onChange={(e) => setTerminalCmd(e.target.value)}
            onKeyDown={handleTerminalKeyDown}
            placeholder="Type developer command (e.g. pytest tests/ -q, git status)..."
            className="flex-1 bg-transparent text-xs text-txt-primary focus:outline-none font-mono placeholder-txt-muted disabled:opacity-50 select-text"
          />
        </form>
      </div>

      {/* Status Bar Footer (Honest Local & File State) */}
      <footer className="h-6 bg-sidebar border-t border-border-subtle px-3 flex items-center justify-between text-[11px] text-txt-muted font-mono select-none shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${isDirty ? 'bg-status-warning' : 'bg-status-success'}`} />
            <span>{isDirty ? 'Modified' : 'Clean'}</span>
          </div>
          {activeFilePath && (
            <span>
              Ln {cursorPos.line}, Col {cursorPos.col} ({lines.length} lines)
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <span>UTF-8</span>
          {activeFilePath && <span className="text-txt-secondary font-medium">{activeFilePath}</span>}
        </div>
      </footer>
    </div>
  );
};

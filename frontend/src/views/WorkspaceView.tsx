import React, { useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Check, X, Trash2, GitBranch } from 'lucide-react';
import { api } from '../services/api';

export const WorkspaceView: React.FC = () => {
  const {
    activeFilePath,
    activeFileContent,
    currentModel,
  } = useSherlyStore();

  const [diffMode, setDiffMode] = useState(false);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    'Sherly Interactive Terminal Ready.',
  ]);
  const [terminalCmd, setTerminalCmd] = useState('');
  const [isExec, setIsExec] = useState(false);

  const handleRunCommand = async (cmd: string) => {
    if (!cmd.trim()) return;
    setTerminalOutput((prev) => [...prev, `➔ $ ${cmd}`]);
    setIsExec(true);
    try {
      const res = await api.runTerminal(cmd);
      setTerminalOutput((prev) => [...prev, res.output || '[No Output]', `[Exited with code ${res.exit_code}]`]);
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
    <div className="flex-1 flex flex-col h-full bg-[#0e0e15] overflow-hidden">
      {/* Editor & Diff Section */}
      <div className="flex-1 flex flex-col p-4 gap-3 overflow-hidden">
        {/* File Tabs & Actions Bar */}
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2">
            {activeFilePath ? (
              <div className="bg-[#0d0d15] text-gray-200 border border-white/10 border-b-0 rounded-t-lg px-3 py-1.5 text-xs font-semibold flex items-center gap-2">
                <span>🐍 {activeFilePath}</span>
                <span
                  onClick={() => useSherlyStore.setState({ activeFilePath: null, activeFileContent: '' })}
                  className="text-gray-500 hover:text-gray-300 cursor-pointer"
                >
                  ✕
                </span>
              </div>
            ) : (
              <span className="text-xs text-gray-500 italic">No file open</span>
            )}
          </div>

          {diffMode && (
            <div className="flex items-center gap-2">
              <button
                onClick={async () => {
                  try {
                    await api.approveAction('preview_last');
                  } catch (e) {
                    console.warn(e);
                  }
                  setDiffMode(false);
                }}
                className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30 px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1.5 transition"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Accept Patch</span>
              </button>
              <button
                onClick={async () => {
                  try {
                    await api.rejectAction('preview_last');
                  } catch (e) {
                    console.warn(e);
                  }
                  setDiffMode(false);
                }}
                className="bg-white/5 text-gray-400 border border-white/10 hover:bg-red-500/20 hover:text-red-400 px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1.5 transition"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
            </div>
          )}
        </div>

        {/* Code View Canvas */}
        <div className="flex-1 bg-[#0d0d15] border border-white/10 rounded-xl overflow-hidden flex flex-col font-mono text-xs">
          <div className="flex-1 overflow-auto p-3 leading-relaxed">
            {lines.length > 0 ? (
              lines.map((line, idx) => (
                <div key={idx} className="flex items-center hover:bg-white/[0.03]">
                  <span className="w-10 text-right pr-4 text-gray-600 select-none text-[11px]">
                    {idx + 1}
                  </span>
                  <pre className="text-gray-300 whitespace-pre">{line || ' '}</pre>
                </div>
              ))
            ) : (
              <div className="text-gray-500 italic p-4 text-center">
                Select a file from Project Explorer to view or edit code.
              </div>
            )}
          </div>
        </div>

        {/* AI Performance Optimization Insight Card */}
        <div className="bg-[#13131e] border border-purple-500/30 rounded-xl p-3.5 flex flex-col gap-1.5 shrink-0">
          <div className="flex items-center gap-2">
            <span className="bg-purple-900/30 text-purple-400 p-1 rounded-md text-xs">⚙</span>
            <h4 className="text-xs font-bold text-gray-200">Performance Optimization Identified</h4>
          </div>
          <p className="text-[11px] text-gray-400 leading-normal">
            Sherly active on model <strong className="text-purple-300">{currentModel || 'Qwen2.5-Coder'}</strong>. Real-time system monitoring and code analysis enabled.
          </p>
        </div>
      </div>

      {/* Integrated Terminal Panel */}
      <div className="h-44 bg-[#08080c] border-t border-white/10 flex flex-col font-mono">
        {/* Terminal Header */}
        <div className="bg-white/[0.02] border-b border-white/5 px-4 py-1.5 flex items-center justify-between">
          <div className="flex items-center gap-4 text-xs font-extrabold">
            <span className="text-purple-400 border-b-2 border-purple-500 pb-0.5">TERMINAL</span>
            <span className="text-gray-600">OUTPUT</span>
          </div>
          <button
            onClick={() => setTerminalOutput([])}
            className="text-gray-500 hover:text-gray-300 text-xs flex items-center gap-1"
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
        <form onSubmit={handleTerminalSubmit} className="bg-white/[0.02] border-t border-white/5 px-3 py-1.5 flex items-center gap-2">
          <span className="text-cyan-400 font-bold text-xs">➔ $</span>
          <input
            type="text"
            value={terminalCmd}
            onChange={(e) => setTerminalCmd(e.target.value)}
            placeholder="Type a command (e.g. python main.py)..."
            className="flex-1 bg-transparent text-xs text-gray-200 focus:outline-none font-mono"
          />
        </form>
      </div>

      {/* Status Bar Footer */}
      <footer className="h-6 bg-[#060609] border-t border-white/5 px-3 flex items-center justify-between text-[10px] text-gray-500">
        <div className="flex items-center gap-2">
          <GitBranch className="w-3 h-3 text-purple-400" />
          <span>main*</span>
        </div>
        <div>
          <span>UTF-8   Python 3.13   ● Sherly Active [{currentModel || 'Qwen2.5-Coder'}]</span>
        </div>
      </footer>
    </div>
  );
};

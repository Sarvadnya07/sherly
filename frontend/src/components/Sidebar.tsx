import React, { useEffect } from 'react';
import { useSherlyStore, ViewType } from '../stores/useSherlyStore';
import {
  MessageSquare,
  FolderGit2,
  Settings,
  Mic,
  Play,
  ChevronDown,
  FileCode2,
  FileText,
  FileJson,
  Code2,
  FolderOpen,
} from 'lucide-react';
import { FileNode } from '../types/api';
import { api } from '../services/api';

export const Sidebar: React.FC = () => {
  const {
    activeView,
    setActiveView,
    fileTree,
    fetchFileTree,
    openFile,
    activeFilePath,
  } = useSherlyStore();

  useEffect(() => {
    fetchFileTree();
  }, [fetchFileTree]);

  const workspaceNav: { id: ViewType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'assistant', label: 'Assistant', icon: MessageSquare },
    { id: 'workspace', label: 'Code Workspace', icon: FolderGit2 },
  ];

  const systemNav: { id: ViewType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'models', label: 'Model Settings', icon: Settings },
    { id: 'voice', label: 'Voice HUD', icon: Mic },
  ];

  const handleRunProject = async () => {
    setActiveView('workspace');
    useSherlyStore.getState().openFile('main.py');
    try {
      await api.runTerminal('python main.py');
    } catch (e) {
      console.warn('Failed to trigger project run:', e);
    }
  };

  const renderFileNode = (node: FileNode, level = 0) => {
    if (node.is_dir) {
      return (
        <div key={node.path} className="select-none">
          <div
            className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-medium text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40 rounded-md cursor-pointer transition"
            style={{ paddingLeft: `${level * 10 + 6}px` }}
          >
            <ChevronDown className="w-3 h-3 text-zinc-500 shrink-0" />
            <FolderOpen className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <span className="text-zinc-300 truncate">{node.name}</span>
          </div>
          {node.children && (
            <div className="flex flex-col">
              {node.children.map((child) => renderFileNode(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

    const isActive = activeFilePath === node.path;
    const ext = node.name.slice(node.name.lastIndexOf('.')).toLowerCase();
    const isPython = ext === '.py';
    const isTs = ext === '.ts' || ext === '.tsx' || ext === '.js' || ext === '.jsx';
    const isJson = ext === '.json' || ext === '.toml' || ext === '.yaml' || ext === '.env';

    return (
      <button
        key={node.path}
        type="button"
        onClick={() => {
          setActiveView('workspace');
          openFile(node.path);
        }}
        className={`w-full flex items-center gap-2 px-2 py-1 text-[11px] rounded-md cursor-pointer transition font-mono text-left focus-visible:outline-2 focus-visible:outline-indigo-500 ${
          isActive
            ? 'bg-zinc-800 text-zinc-100 font-medium'
            : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200'
        }`}
        style={{ paddingLeft: `${level * 10 + 16}px` }}
        title={node.path}
      >
        {isPython ? (
          <FileCode2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
        ) : isTs ? (
          <Code2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        ) : isJson ? (
          <FileJson className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        ) : (
          <FileText className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
        )}
        <span className="truncate">{node.name}</span>
      </button>
    );
  };

  return (
    <aside className="w-56 bg-sidebar border-r border-white/[0.06] flex flex-col justify-between p-2.5 select-none shrink-0 h-full overflow-hidden">
      <div className="flex flex-col gap-3 overflow-hidden flex-1">
        {/* Workspace Info Card */}
        <div className="bg-zinc-900/60 border border-white/[0.06] rounded-lg px-2.5 py-2 flex items-center justify-between shadow-subtle">
          <div className="flex items-center gap-2 min-w-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 shadow-[0_0_5px_rgba(52,211,153,0.6)]" />
            <span className="text-xs font-medium text-zinc-200 truncate">Sherly Workspace</span>
          </div>
          <span className="text-[10px] font-mono text-zinc-500 shrink-0">v2.0</span>
        </div>

        {/* Workspace Navigation */}
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold text-zinc-500 tracking-wider px-2 py-0.5 uppercase">WORKSPACE</span>
          {workspaceNav.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveView(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition text-left focus-visible:outline-2 focus-visible:outline-indigo-500 cursor-pointer ${
                  isActive
                    ? 'bg-zinc-800 text-zinc-100 font-medium shadow-subtle'
                    : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0 text-zinc-400" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Runtime & System Navigation */}
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold text-zinc-500 tracking-wider px-2 py-0.5 uppercase">SYSTEM</span>
          {systemNav.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveView(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs transition text-left focus-visible:outline-2 focus-visible:outline-indigo-500 cursor-pointer ${
                  isActive
                    ? 'bg-zinc-800 text-zinc-100 font-medium shadow-subtle'
                    : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0 text-zinc-400" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Project Files Tree */}
        <div className="flex flex-col gap-1 mt-1 flex-1 overflow-hidden">
          <span className="text-[10px] font-semibold text-zinc-500 tracking-wider px-2 uppercase">EXPLORER</span>
          <div className="overflow-y-auto flex-1 flex flex-col gap-0.5 pr-1">
            {fileTree && fileTree.children ? (
              fileTree.children.map((child) => renderFileNode(child))
            ) : (
              <span className="text-xs text-zinc-500 italic px-2">Loading workspace...</span>
            )}
          </div>
        </div>
      </div>

      {/* Run Project Bottom Action Button */}
      <button
        type="button"
        onClick={handleRunProject}
        className="w-full h-8 bg-zinc-800 hover:bg-zinc-700 border border-white/[0.08] text-zinc-200 hover:text-white font-medium text-xs rounded-lg flex items-center justify-center gap-2 shadow-subtle transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-indigo-500 mt-2 shrink-0 cursor-pointer"
      >
        <Play className="w-3 h-3 fill-emerald-400 text-emerald-400" />
        <span>Run main.py</span>
      </button>
    </aside>
  );
};

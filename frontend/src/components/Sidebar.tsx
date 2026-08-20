import React, { useEffect } from 'react';
import { useSherlyStore, ViewType } from '../stores/useSherlyStore';
import {
  MessageSquare,
  Folder,
  Settings,
  Mic,
  Play,
  ChevronDown,
  FileCode,
  FileText,
  FileJson,
  Code2,
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
    { id: 'workspace', label: 'Code Workspace', icon: Folder },
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
            className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-medium text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] rounded cursor-pointer transition"
            style={{ paddingLeft: `${level * 10 + 6}px` }}
          >
            <ChevronDown className="w-3 h-3 text-gray-500 shrink-0" />
            <span className="text-purple-300 font-semibold truncate">{node.name}</span>
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
        className={`w-full flex items-center gap-2 px-2 py-1 text-[11px] rounded cursor-pointer transition font-mono text-left focus-visible:outline-2 focus-visible:outline-brand ${
          isActive
            ? 'bg-brand-surface text-purple-300 font-semibold border-l-2 border-brand'
            : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-200'
        }`}
        style={{ paddingLeft: `${level * 10 + 14}px` }}
        title={node.path}
      >
        {isPython ? (
          <FileCode className="w-3.5 h-3.5 text-sky-400 shrink-0" />
        ) : isTs ? (
          <Code2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        ) : isJson ? (
          <FileJson className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        ) : (
          <FileText className="w-3.5 h-3.5 text-gray-500 shrink-0" />
        )}
        <span className="truncate">{node.name}</span>
      </button>
    );
  };

  return (
    <aside className="w-60 bg-sidebar border-r border-white/[0.07] flex flex-col justify-between p-3 select-none shrink-0 h-full overflow-hidden">
      <div className="flex flex-col gap-3 overflow-hidden flex-1">
        {/* Workspace Info Card */}
        <div className="bg-card border border-white/[0.07] rounded-lg p-2.5 flex flex-col gap-1 shadow-subtle">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <h2 className="text-[10px] font-bold text-gray-400 tracking-wider">PROJECT WORKSPACE</h2>
          </div>
          <p className="text-[11px] font-mono text-gray-300 pl-3.5 truncate">Sherly Workspace</p>
        </div>

        {/* Workspace Navigation */}
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-bold text-gray-500 tracking-wider px-2 py-1">WORKSPACE</span>
          {workspaceNav.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveView(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs transition text-left focus-visible:outline-2 focus-visible:outline-brand cursor-pointer ${
                  isActive
                    ? 'bg-brand-surface text-purple-300 border-l-2 border-brand font-semibold shadow-subtle'
                    : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Runtime & System Navigation */}
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-bold text-gray-500 tracking-wider px-2 py-1">RUNTIME & SYSTEM</span>
          {systemNav.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveView(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs transition text-left focus-visible:outline-2 focus-visible:outline-brand cursor-pointer ${
                  isActive
                    ? 'bg-brand-surface text-purple-300 border-l-2 border-brand font-semibold shadow-subtle'
                    : 'text-gray-400 hover:bg-white/[0.04] hover:text-gray-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Project Files Tree */}
        <div className="flex flex-col gap-1 mt-1 flex-1 overflow-hidden">
          <span className="text-[9px] font-bold text-gray-500 tracking-wider px-2">PROJECT FILES</span>
          <div className="overflow-y-auto flex-1 flex flex-col gap-0.5 pr-1">
            {fileTree && fileTree.children ? (
              fileTree.children.map((child) => renderFileNode(child))
            ) : (
              <span className="text-xs text-gray-500 italic px-2">Loading workspace...</span>
            )}
          </div>
        </div>
      </div>

      {/* Run Project Bottom Action Button */}
      <button
        type="button"
        onClick={handleRunProject}
        className="w-full h-9 bg-brand hover:bg-brand-hover text-white font-semibold text-xs rounded-md flex items-center justify-center gap-2 shadow-subtle transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-brand mt-2 shrink-0 cursor-pointer"
      >
        <Play className="w-3.5 h-3.5 fill-white" />
        <span>Run main.py</span>
      </button>
    </aside>
  );
};

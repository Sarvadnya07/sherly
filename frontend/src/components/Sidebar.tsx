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
        <div key={node.path} role="treeitem" aria-expanded="true" className="select-none">
          <div
            className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-txt-secondary hover:text-txt-primary hover:bg-white/[0.04] rounded-md cursor-pointer transition"
            style={{ paddingLeft: `${level * 12 + 6}px` }}
          >
            <ChevronDown className="w-3.5 h-3.5 text-txt-muted shrink-0" aria-hidden="true" />
            <FolderOpen className="w-3.5 h-3.5 text-txt-muted shrink-0" aria-hidden="true" />
            <span className="truncate">{node.name}</span>
          </div>
          {node.children && (
            <div role="group" className="flex flex-col">
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
      <div key={node.path} role="treeitem" aria-selected={isActive}>
        <button
          type="button"
          onClick={() => {
            setActiveView('workspace');
            openFile(node.path);
          }}
          className={`w-full flex items-center gap-2 px-2 py-1 text-xs rounded-md cursor-pointer transition font-mono text-left focus-visible:outline-2 focus-visible:outline-brand ${
            isActive
              ? 'bg-card text-txt-primary font-medium border border-border-subtle'
              : 'text-txt-secondary hover:bg-white/[0.04] hover:text-txt-primary'
          }`}
          style={{ paddingLeft: `${level * 12 + 18}px` }}
          title={node.path}
          aria-label={`Open file ${node.name}`}
        >
          {isPython ? (
            <FileCode2 className="w-3.5 h-3.5 text-sky-400 shrink-0" aria-hidden="true" />
          ) : isTs ? (
            <Code2 className="w-3.5 h-3.5 text-amber-400 shrink-0" aria-hidden="true" />
          ) : isJson ? (
            <FileJson className="w-3.5 h-3.5 text-emerald-400 shrink-0" aria-hidden="true" />
          ) : (
            <FileText className="w-3.5 h-3.5 text-txt-muted shrink-0" aria-hidden="true" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
      </div>
    );
  };

  return (
    <aside className="w-60 bg-sidebar border-r border-border-subtle flex flex-col justify-between p-3 select-none shrink-0 h-full overflow-hidden">
      <div className="flex flex-col gap-3.5 overflow-hidden flex-1">
        {/* Workspace Info Card */}
        <div className="bg-card border border-border-subtle rounded-lg px-3 py-2 flex items-center justify-between shadow-subtle">
          <div className="flex items-center gap-2 min-w-0">
            <span className="w-2 h-2 rounded-full bg-status-success shrink-0 shadow-[0_0_5px_rgba(16,185,129,0.6)]" />
            <span className="text-xs font-semibold text-txt-primary truncate">Sherly Workspace</span>
          </div>
          <span className="text-[10px] font-mono text-txt-muted shrink-0">v2.0</span>
        </div>

        {/* Workspace Navigation */}
        <nav aria-label="Workspace navigation" className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold text-txt-muted tracking-wider px-2 py-0.5 uppercase">
            WORKSPACE
          </span>
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
                    ? 'bg-card text-txt-primary font-medium border-l-2 border-brand shadow-subtle'
                    : 'text-txt-secondary hover:bg-white/[0.04] hover:text-txt-primary'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-4 h-4 shrink-0 text-txt-muted" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Runtime & System Navigation */}
        <nav aria-label="System navigation" className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold text-txt-muted tracking-wider px-2 py-0.5 uppercase">
            SYSTEM
          </span>
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
                    ? 'bg-card text-txt-primary font-medium border-l-2 border-brand shadow-subtle'
                    : 'text-txt-secondary hover:bg-white/[0.04] hover:text-txt-primary'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="w-4 h-4 shrink-0 text-txt-muted" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Project Files Tree */}
        <div className="flex flex-col gap-1 mt-1 flex-1 overflow-hidden">
          <span className="text-[10px] font-semibold text-txt-muted tracking-wider px-2 uppercase" id="explorer-heading">
            EXPLORER
          </span>
          <div
            role="tree"
            aria-labelledby="explorer-heading"
            className="overflow-y-auto flex-1 flex flex-col gap-0.5 pr-1"
          >
            {fileTree && fileTree.children ? (
              fileTree.children.map((child) => renderFileNode(child))
            ) : (
              <span className="text-xs text-txt-muted italic px-2">Loading workspace files...</span>
            )}
          </div>
        </div>
      </div>

      {/* Run Project Bottom Action Button */}
      <button
        type="button"
        onClick={handleRunProject}
        className="w-full h-8 bg-card hover:bg-card-hover border border-border-subtle text-txt-primary font-medium text-xs rounded-md flex items-center justify-center gap-2 shadow-subtle transition active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-brand mt-2 shrink-0 cursor-pointer"
        aria-label="Run project main.py"
      >
        <Play className="w-3.5 h-3.5 fill-status-success text-status-success" />
        <span>Run main.py</span>
      </button>
    </aside>
  );
};

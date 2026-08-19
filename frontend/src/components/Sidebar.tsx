import React, { useEffect } from 'react';
import { useSherlyStore, ViewType } from '../stores/useSherlyStore';
import { MessageSquare, Folder, Settings, Mic, Play, ChevronDown, FileCode, FileText } from 'lucide-react';
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

  const navItems: { id: ViewType; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'assistant', label: 'Assistant', icon: MessageSquare },
    { id: 'workspace', label: 'Workspace / Code', icon: Folder },
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
            className="flex items-center gap-1.5 px-2 py-1 text-xs font-semibold text-gray-300 hover:bg-white/5 rounded cursor-pointer"
            style={{ paddingLeft: `${level * 12 + 8}px` }}
          >
            <ChevronDown className="w-3 h-3 text-gray-500" />
            <span>📂 {node.name}</span>
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
    const isPython = node.name.endsWith('.py');

    return (
      <div
        key={node.path}
        onClick={() => {
          setActiveView('workspace');
          openFile(node.path);
        }}
        className={`flex items-center gap-2 px-2 py-1 text-xs rounded cursor-pointer transition ${
          isActive
            ? 'bg-purple-900/30 text-purple-300 font-semibold border border-purple-500/30'
            : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
        }`}
        style={{ paddingLeft: `${level * 12 + 16}px` }}
      >
        {isPython ? <FileCode className="w-3.5 h-3.5 text-emerald-400" /> : <FileText className="w-3.5 h-3.5 text-gray-400" />}
        <span className="truncate">{node.name}</span>
      </div>
    );
  };

  return (
    <aside className="w-56 bg-[#0b0b11] border-r border-white/10 flex flex-col justify-between p-3 select-none">
      <div className="flex flex-col gap-4">
        {/* Project Explorer Header */}
        <div className="bg-white/[0.03] border border-white/5 rounded-lg p-2.5">
          <h2 className="text-xs font-bold text-gray-200">Project Explorer</h2>
          <p className="text-[10px] text-gray-500">Python 3.13</p>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition ${
                  isActive
                    ? 'bg-purple-900/30 text-purple-300 border border-purple-500/40 font-semibold'
                    : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Project Files Tree */}
        <div className="flex flex-col gap-2 mt-2">
          <span className="text-[9px] font-extrabold text-gray-500 tracking-widest px-2">
            PROJECT FILES
          </span>
          <div className="overflow-y-auto max-h-[340px] flex flex-col gap-0.5">
            {fileTree && fileTree.children ? (
              fileTree.children.map((child) => renderFileNode(child))
            ) : (
              <span className="text-xs text-gray-500 italic px-2">Loading workspace...</span>
            )}
          </div>
        </div>
      </div>

      {/* Run Project Action Button */}
      <button
        onClick={handleRunProject}
        className="w-full h-10 bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-500 hover:to-purple-700 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-purple-900/30 transition"
      >
        <Play className="w-4 h-4 fill-white" />
        <span>Run main.py</span>
      </button>
    </aside>
  );
};

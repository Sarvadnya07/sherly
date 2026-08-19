import React, { useEffect } from 'react';
import { useSherlyStore } from './stores/useSherlyStore';
import { HeaderBar } from './components/HeaderBar';
import { Sidebar } from './components/Sidebar';
import { AssistantView } from './views/AssistantView';
import { WorkspaceView } from './views/WorkspaceView';
import { ModelsView } from './views/ModelsView';
import { VoiceOverlayView } from './views/VoiceOverlayView';
import { ApprovalDialog } from './components/ui/ApprovalDialog';

export const App: React.FC = () => {
  const {
    activeView,
    fetchModels,
    initWebSocket,
    pendingApprovals,
    approveAction,
    rejectAction,
    fetchApprovals,
  } = useSherlyStore();

  useEffect(() => {
    fetchModels();
    fetchApprovals();
    initWebSocket();
  }, [fetchModels, fetchApprovals, initWebSocket]);

  const currentPending = pendingApprovals[0] || null;

  return (
    <div className="flex flex-col h-screen w-screen bg-canvas text-gray-100 overflow-hidden border border-white/[0.08] rounded-[10px]">
      {/* Top Header */}
      <HeaderBar />

      {/* Main Body Split (Sidebar + View Switcher) */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col h-full overflow-hidden bg-surface">
          {activeView === 'assistant' && <AssistantView />}
          {activeView === 'workspace' && <WorkspaceView />}
          {activeView === 'models' && <ModelsView />}
          {activeView === 'voice' && <VoiceOverlayView />}
        </main>
      </div>

      {/* Operation Approval Modal */}
      {currentPending && (
        <ApprovalDialog
          isOpen={Boolean(currentPending)}
          actionId={currentPending.action_id}
          actionName="Workspace Command"
          target={currentPending.command}
          reason="Safety guard is requesting confirmation before executing this action."
          riskLevel={currentPending.level === 'dangerous' ? 'high' : 'medium'}
          isReversible={false}
          onApprove={approveAction}
          onReject={rejectAction}
          onClose={() => useSherlyStore.setState((s) => ({ pendingApprovals: s.pendingApprovals.slice(1) }))}
        />
      )}
    </div>
  );
};

export default App;

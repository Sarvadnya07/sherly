import React, { useEffect } from 'react';
import { useSherlyStore } from './stores/useSherlyStore';
import { HeaderBar } from './components/HeaderBar';
import { Sidebar } from './components/Sidebar';
import { AssistantView } from './views/AssistantView';
import { WorkspaceView } from './views/WorkspaceView';
import { ModelsView } from './views/ModelsView';
import { VoiceOverlayView } from './views/VoiceOverlayView';

export const App: React.FC = () => {
  const { activeView, fetchModels, initWebSocket } = useSherlyStore();

  useEffect(() => {
    fetchModels();
    initWebSocket();
  }, [fetchModels, initWebSocket]);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#09090d] text-gray-100 overflow-hidden select-none border border-white/10 rounded-xl">
      {/* Top Header */}
      <HeaderBar />

      {/* Main Body Split (Sidebar + View Switcher) */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col h-full overflow-hidden">
          {activeView === 'assistant' && <AssistantView />}
          {activeView === 'workspace' && <WorkspaceView />}
          {activeView === 'models' && <ModelsView />}
          {activeView === 'voice' && <VoiceOverlayView />}
        </main>
      </div>
    </div>
  );
};

export default App;

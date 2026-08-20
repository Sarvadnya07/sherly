/**
 * ZUSTAND STATE STORE — frontend/src/stores/useSherlyStore.ts
 * Central state store managing view switching, chat history, model state,
 * active project file, real-time status, and generation lifecycle.
 */

import { create } from 'zustand';
import { ChatMessage, ModelInfo, FileNode, PendingApproval, ToolActivityInfo } from '../types/api';
import { api } from '../services/api';
import { wsService } from '../services/websocket';

export type ViewType = 'assistant' | 'workspace' | 'models' | 'voice';

interface SherlyState {
  activeView: ViewType;
  currentTitle: string;
  currentModel: string | null;
  modelMode: 'auto' | 'manual';
  pinnedModel: string | null;
  isOllamaRunning: boolean;
  modelsList: ModelInfo[];

  // Chat & Generation Lifecycle
  chatHistory: ChatMessage[];
  isThinking: boolean;
  statusText: string;
  activeToolActivity: ToolActivityInfo | null;
  composerPrompt: string;

  // Workspace
  fileTree: FileNode | null;
  activeFilePath: string | null;
  activeFileContent: string;
  diffMode: boolean;
  diffOldCode: string;
  diffNewCode: string;
  activeActionId: string | null;

  // Actions & Approvals
  pendingApprovals: PendingApproval[];

  // Voice
  audioDevices: string[];
  selectedDevice: string | null;
  isListening: boolean;
  sttText: string;

  // Methods
  setActiveView: (view: ViewType) => void;
  setComposerPrompt: (prompt: string) => void;
  fetchModels: () => Promise<void>;
  selectModel: (modelName: string) => Promise<void>;
  setMode: (mode: 'auto' | 'manual') => Promise<void>;
  fetchChatHistory: () => Promise<void>;
  sendChatMessage: (prompt: string, attachment?: string) => Promise<void>;
  cancelGeneration: () => Promise<void>;
  regenerateMessage: (index: number) => Promise<void>;
  editUserPrompt: (index: number) => void;
  fetchFileTree: () => Promise<void>;
  openFile: (path: string) => Promise<void>;
  saveFileContent: (path: string, content: string) => Promise<void>;
  fetchApprovals: () => Promise<void>;
  approveAction: (id: string) => Promise<void>;
  rejectAction: (id: string) => Promise<void>;
  fetchAudioDevices: () => Promise<void>;
  initWebSocket: () => void;
}

let activeChatAbort: AbortController | null = null;

export const useSherlyStore = create<SherlyState>((set, get) => ({
  activeView: 'workspace',
  currentTitle: 'Sherly — Developer Workspace',
  currentModel: null,
  modelMode: 'auto',
  pinnedModel: null,
  isOllamaRunning: false,
  modelsList: [],

  chatHistory: [],
  isThinking: false,
  statusText: 'Ready',
  activeToolActivity: null,
  composerPrompt: '',

  fileTree: null,
  activeFilePath: null,
  activeFileContent: '',
  diffMode: false,
  diffOldCode: '',
  diffNewCode: '',
  activeActionId: null,

  pendingApprovals: [],

  audioDevices: [],
  selectedDevice: null,
  isListening: false,
  sttText: 'Listening to audio input...',

  setActiveView: (view: ViewType) => {
    let title = 'Sherly — Developer Workspace';
    if (view === 'assistant') title = 'Sherly — Main Assistant';
    if (view === 'models') title = 'Sherly — Model Management';
    if (view === 'voice') title = 'Sherly — Voice Listening';
    set({ activeView: view, currentTitle: title });
  },

  setComposerPrompt: (prompt: string) => set({ composerPrompt: prompt }),

  fetchModels: async () => {
    try {
      const data = await api.getModels();
      set({
        modelMode: data.mode,
        currentModel: data.current_model,
        pinnedModel: data.pinned_model,
        isOllamaRunning: data.is_ollama_running,
        modelsList: data.models,
      });
    } catch (e) {
      console.warn('Error fetching models:', e);
    }
  },

  selectModel: async (modelName: string) => {
    try {
      await api.selectModel(modelName);
      await get().fetchModels();
    } catch (e) {
      console.error('Error selecting model:', e);
    }
  },

  setMode: async (mode: 'auto' | 'manual') => {
    try {
      await api.setModelMode(mode);
      await get().fetchModels();
    } catch (e) {
      console.error('Error setting mode:', e);
    }
  },

  fetchChatHistory: async () => {
    try {
      const data = await api.getHistory();
      set({ chatHistory: data.messages });
    } catch (e) {
      console.warn('Error fetching chat history:', e);
    }
  },

  cancelGeneration: async () => {
    if (activeChatAbort) {
      activeChatAbort.abort();
      activeChatAbort = null;
    }

    // Propagate backend cancellation if supported
    try {
      wsService.send({
        action: 'cancel_generation',
      });
    } catch (e) {
      console.warn('Error broadcasting cancel signal:', e);
    }

    set((state) => {
      // Mark the active generation message as cancelled
      const history = [...state.chatHistory];
      if (history.length > 0) {
        const last = history[history.length - 1];
        if (last.status === 'thinking' || last.status === 'streaming') {
          history[history.length - 1] = {
            ...last,
            status: 'cancelled',
            assistant_response: last.assistant_response || '[Generation stopped by user]',
          };
        }
      }
      return {
        isThinking: false,
        statusText: 'Ready',
        activeToolActivity: null,
        chatHistory: history,
      };
    });
  },

  sendChatMessage: async (prompt: string, attachment?: string) => {
    if (activeChatAbort) {
      activeChatAbort.abort();
    }
    activeChatAbort = new AbortController();

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const pendingMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      user_prompt: prompt,
      assistant_response: '',
      timestamp,
      attached_file: attachment,
      status: 'thinking',
    };

    set((state) => ({
      chatHistory: [...state.chatHistory, pendingMsg],
      isThinking: true,
      statusText: 'thinking',
      activeToolActivity: null,
    }));

    try {
      const response = await api.sendChat(prompt, attachment, activeChatAbort.signal);
      activeChatAbort = null;

      set((state) => {
        const history = [...state.chatHistory];
        const lastIdx = history.length - 1;
        if (lastIdx >= 0 && history[lastIdx].status === 'thinking') {
          history[lastIdx] = {
            ...response,
            status: 'completed',
          };
        } else {
          history.push({ ...response, status: 'completed' });
        }
        return {
          chatHistory: history,
          isThinking: false,
          statusText: 'ready',
          activeToolActivity: null,
        };
      });
    } catch (e: any) {
      if (e.name === 'AbortError') {
        console.log('Chat generation aborted by user.');
        set((state) => {
          const history = [...state.chatHistory];
          const lastIdx = history.length - 1;
          if (lastIdx >= 0 && history[lastIdx].status === 'thinking') {
            history[lastIdx] = {
              ...history[lastIdx],
              status: 'cancelled',
              assistant_response: '[Generation stopped by user]',
            };
          }
          return { chatHistory: history, isThinking: false, statusText: 'ready', activeToolActivity: null };
        });
      } else {
        console.error('Error sending chat:', e);
        set((state) => {
          const history = [...state.chatHistory];
          const lastIdx = history.length - 1;
          if (lastIdx >= 0 && history[lastIdx].status === 'thinking') {
            history[lastIdx] = {
              ...history[lastIdx],
              status: 'error',
              error: e.message || 'Failed to generate response.',
              assistant_response: `Error: ${e.message || 'Unable to complete request. Please check model connection.'}`,
            };
          }
          return { chatHistory: history, isThinking: false, statusText: 'error', activeToolActivity: null };
        });
      }
      activeChatAbort = null;
    }
  },

  regenerateMessage: async (index: number) => {
    const history = get().chatHistory;
    const targetMsg = history[index];
    if (!targetMsg) return;

    // Resend the prompt from that index, updating the message in place
    await get().sendChatMessage(targetMsg.user_prompt, targetMsg.attached_file);
  },

  editUserPrompt: (index: number) => {
    const history = get().chatHistory;
    const targetMsg = history[index];
    if (!targetMsg) return;

    set({ composerPrompt: targetMsg.user_prompt });
  },

  fetchFileTree: async () => {
    try {
      const tree = await api.getFileTree();
      set({ fileTree: tree });
    } catch (e) {
      console.warn('Error fetching file tree:', e);
    }
  },

  openFile: async (path: string) => {
    try {
      const res = await api.readFile(path);
      set({
        activeFilePath: res.path,
        activeFileContent: res.content,
        diffMode: false,
      });
    } catch (e) {
      console.error('Error opening file:', e);
    }
  },

  saveFileContent: async (path: string, content: string) => {
    try {
      await api.writeFile(path, content);
      set({ activeFileContent: content });
    } catch (e) {
      console.error('Error saving file:', e);
    }
  },

  fetchApprovals: async () => {
    try {
      const list = await api.getApprovals();
      set({ pendingApprovals: list });
    } catch (e) {
      console.warn('Error fetching approvals:', e);
    }
  },

  approveAction: async (id: string) => {
    try {
      await api.approveAction(id);
      await get().fetchApprovals();
    } catch (e) {
      console.error('Error approving action:', e);
    }
  },

  rejectAction: async (id: string) => {
    try {
      await api.rejectAction(id);
      await get().fetchApprovals();
    } catch (e) {
      console.error('Error rejecting action:', e);
    }
  },

  fetchAudioDevices: async () => {
    try {
      const res = await api.getAudioDevices();
      set({
        audioDevices: res.devices,
        selectedDevice: res.devices[0] || null,
      });
    } catch (e) {
      console.warn('Error fetching audio devices:', e);
    }
  },

  initWebSocket: () => {
    wsService.connect();
    wsService.subscribe((event) => {
      if (event.event_type === 'status') {
        const st = event.payload.status;
        set({ statusText: st, isThinking: st === 'thinking' });
        if (st === 'listening') {
          get().setActiveView('voice');
        }
      } else if (event.event_type === 'model_changed') {
        set({
          currentModel: event.payload.current_model,
          modelMode: event.payload.mode,
        });
      } else if (event.event_type === 'stt_text') {
        set({ sttText: event.payload.text || 'Listening...' });
      } else if (event.event_type === 'action_update') {
        get().fetchApprovals();
      }
    });
  },
}));

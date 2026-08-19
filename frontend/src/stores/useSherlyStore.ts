/**
 * ZUSTAND STATE STORE — frontend/src/stores/useSherlyStore.ts
 * Central state store managing view switching, chat history, model state,
 * active project file, and real-time status.
 */

import { create } from 'zustand';
import { ChatMessage, ModelInfo, FileNode, PendingApproval } from '../types/api';
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

  // Chat
  chatHistory: ChatMessage[];
  isThinking: boolean;
  statusText: string;

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
  fetchModels: () => Promise<void>;
  selectModel: (modelName: string) => Promise<void>;
  setMode: (mode: 'auto' | 'manual') => Promise<void>;
  fetchChatHistory: () => Promise<void>;
  sendChatMessage: (prompt: string, attachment?: string) => Promise<void>;
  cancelGeneration: () => void;
  regenerateMessage: (index: number) => Promise<void>;
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

  cancelGeneration: () => {
    if (activeChatAbort) {
      activeChatAbort.abort();
      activeChatAbort = null;
    }
    set({ isThinking: false });
  },

  sendChatMessage: async (prompt: string, attachment?: string) => {
    if (activeChatAbort) {
      activeChatAbort.abort();
    }
    activeChatAbort = new AbortController();
    set({ isThinking: true });

    try {
      const response = await api.sendChat(prompt, attachment, activeChatAbort.signal);
      activeChatAbort = null;
      set((state) => ({
        chatHistory: [...state.chatHistory, response],
        isThinking: false,
      }));
    } catch (e: any) {
      if (e.name === 'AbortError') {
        console.log('Chat generation aborted by user.');
      } else {
        console.error('Error sending chat:', e);
      }
      activeChatAbort = null;
      set({ isThinking: false });
    }
  },

  regenerateMessage: async (index: number) => {
    const history = get().chatHistory;
    const targetMsg = history[index];
    if (!targetMsg) return;

    // Resend the prompt from that index
    await get().sendChatMessage(targetMsg.user_prompt, targetMsg.attached_file);
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

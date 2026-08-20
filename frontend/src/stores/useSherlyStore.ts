/**
 * ZUSTAND STATE STORE — frontend/src/stores/useSherlyStore.ts
 * Central state store managing view switching, chat history, model state,
 * workspace tabs, file editing, voice state machine, and real-time status.
 */

import { create } from 'zustand';
import { ChatMessage, ModelInfo, FileNode, PendingApproval, ToolActivityInfo, WorkspaceTab } from '../types/api';
import { api } from '../services/api';
import { wsService } from '../services/websocket';

export type ViewType = 'assistant' | 'workspace' | 'models' | 'voice';

export type VoiceState =
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'thinking'
  | 'tool_running'
  | 'waiting_for_approval'
  | 'speaking'
  | 'stopping'
  | 'stopped'
  | 'cancelled'
  | 'error';

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

  // Workspace & Multi-Tab State
  fileTree: FileNode | null;
  openTabs: WorkspaceTab[];
  activeFilePath: string | null;
  activeFileContent: string;
  activeOriginalContent: string;
  isDirty: boolean;
  diffMode: boolean;
  diffOldCode: string;
  diffNewCode: string;
  activeActionId: string | null;

  // Actions & Approvals
  pendingApprovals: PendingApproval[];

  // Voice State Machine
  voiceState: VoiceState;
  voiceSessionId: string | null;
  lastVoiceEventTs: number;
  audioDevices: string[];
  selectedDevice: string | null;
  isListening: boolean;
  sttText: string;
  voiceErrorMessage: string | null;

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
  closeTab: (path: string) => void;
  updateActiveContent: (content: string) => void;
  saveActiveFile: () => Promise<boolean>;
  setDiffMode: (mode: boolean, oldCode?: string, newCode?: string, actionId?: string) => void;
  undoLastAction: () => Promise<string>;
  fetchApprovals: () => Promise<void>;
  approveAction: (id: string) => Promise<void>;
  rejectAction: (id: string) => Promise<void>;
  fetchAudioDevices: () => Promise<void>;
  startVoiceSession: () => Promise<void>;
  stopVoiceSession: () => Promise<void>;
  cancelVoiceSession: () => Promise<void>;
  stopVoiceSpeaking: () => Promise<void>;
  initWebSocket: () => void;
  appendStreamToken: (token: string, messageId?: string) => void;
  flushStreamBuffer: () => void;
}

let activeChatAbort: AbortController | null = null;

// ── Item 1 (P1): React Token Stream Batching Buffer ────────────────────────
interface TokenBatchBuffer {
  tokensByMessageId: Map<string, string[]>;
  rafHandle: number | null;
}

const streamBuffer: TokenBatchBuffer = {
  tokensByMessageId: new Map(),
  rafHandle: null,
};

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
  openTabs: [],
  activeFilePath: null,
  activeFileContent: '',
  activeOriginalContent: '',
  isDirty: false,
  diffMode: false,
  diffOldCode: '',
  diffNewCode: '',
  activeActionId: null,

  pendingApprovals: [],

  voiceState: 'idle',
  voiceSessionId: null,
  lastVoiceEventTs: 0,
  audioDevices: [],
  selectedDevice: null,
  isListening: false,
  sttText: 'Listening to audio input...',
  voiceErrorMessage: null,

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

    // Flush any pending buffered tokens immediately before cancelling
    get().flushStreamBuffer();

    try {
      wsService.send({
        action: 'cancel_generation',
      });
    } catch (e) {
      console.warn('Error broadcasting cancel signal:', e);
    }

    set((state) => {
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
        voiceState: 'idle',
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
    const state = get();
    const existing = state.openTabs.find((t) => t.path === path);
    if (existing) {
      set({
        activeFilePath: path,
        activeFileContent: existing.content,
        isDirty: existing.isDirty,
        diffMode: false,
      });
      return;
    }

    try {
      const res = await api.readFile(path);
      const fileName = path.split('/').pop() || path.split('\\').pop() || path;
      const newTab: WorkspaceTab = {
        path: res.path,
        name: fileName,
        isDirty: false,
        content: res.content,
      };

      set((s) => ({
        openTabs: [...s.openTabs, newTab],
        activeFilePath: res.path,
        activeFileContent: res.content,
        activeOriginalContent: res.content,
        isDirty: false,
        diffMode: false,
      }));
    } catch (e) {
      console.error('Error opening file:', e);
    }
  },

  closeTab: (path: string) => {
    const state = get();
    const remaining = state.openTabs.filter((t) => t.path !== path);

    let nextActivePath: string | null = state.activeFilePath;
    let nextContent = state.activeFileContent;
    let nextDirty = false;

    if (state.activeFilePath === path) {
      if (remaining.length > 0) {
        const nextTab = remaining[remaining.length - 1];
        nextActivePath = nextTab.path;
        nextContent = nextTab.content;
        nextDirty = nextTab.isDirty;
      } else {
        nextActivePath = null;
        nextContent = '';
        nextDirty = false;
      }
    }

    set({
      openTabs: remaining,
      activeFilePath: nextActivePath,
      activeFileContent: nextContent,
      isDirty: nextDirty,
    });
  },

  updateActiveContent: (content: string) => {
    const state = get();
    if (!state.activeFilePath) return;

    const isModified = content !== state.activeOriginalContent;
    const updatedTabs = state.openTabs.map((t) =>
      t.path === state.activeFilePath ? { ...t, content, isDirty: isModified } : t
    );

    set({
      activeFileContent: content,
      isDirty: isModified,
      openTabs: updatedTabs,
    });
  },

  saveActiveFile: async () => {
    const state = get();
    if (!state.activeFilePath) return false;

    try {
      await api.writeFile(state.activeFilePath, state.activeFileContent);
      const updatedTabs = state.openTabs.map((t) =>
        t.path === state.activeFilePath ? { ...t, isDirty: false } : t
      );
      set({
        isDirty: false,
        activeOriginalContent: state.activeFileContent,
        openTabs: updatedTabs,
      });
      return true;
    } catch (e) {
      console.error('Error saving file:', e);
      return false;
    }
  },

  setDiffMode: (mode: boolean, oldCode = '', newCode = '', actionId = '') => {
    set({
      diffMode: mode,
      diffOldCode: oldCode,
      diffNewCode: newCode,
      activeActionId: actionId || null,
    });
  },

  undoLastAction: async () => {
    try {
      const res = await api.undoLastAction();
      await get().fetchApprovals();
      return res.message;
    } catch (e: any) {
      console.error('Error undoing action:', e);
      throw e;
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

  startVoiceSession: async () => {
    const sid = `vses-${Date.now()}`;
    set({
      voiceState: 'listening',
      voiceSessionId: sid,
      isListening: true,
      sttText: 'Listening to your voice...',
      voiceErrorMessage: null,
    });
    try {
      await api.startVoice();
    } catch (e: any) {
      set({ voiceState: 'error', voiceErrorMessage: e.message || 'Failed to start microphone' });
    }
  },

  stopVoiceSession: async () => {
    const text = get().sttText.replace('Listening to your voice...', '').replace('Listening...', '').trim();
    set({ voiceState: 'transcribing', isListening: false });
    try {
      await api.stopVoice();
    } catch (e) {
      console.warn('Error stopping voice:', e);
    }

    if (text && text.length >= 2 && text !== 'No speech detected.') {
      set({ voiceState: 'thinking' });
      // Converge voice onto canonical assistant chat pipeline
      await get().sendChatMessage(text);
      set({ voiceState: 'idle' });
    } else {
      set({
        sttText: 'No speech detected.',
        voiceState: 'idle',
      });
    }
  },

  cancelVoiceSession: async () => {
    set({
      voiceState: 'cancelled',
      isListening: false,
      sttText: 'Voice cancelled.',
      voiceSessionId: null,
    });
    try {
      await api.stopVoice();
      await api.stopSpeaking();
    } catch (e) {
      console.warn('Error cancelling voice session:', e);
    }
    setTimeout(() => {
      set({ voiceState: 'idle', sttText: 'Listening to audio input...' });
    }, 1000);
  },

  stopVoiceSpeaking: async () => {
    set({ voiceState: 'stopping' });
    try {
      await api.stopSpeaking();
    } catch (e) {
      console.warn('Error stopping speaking:', e);
    }
    set({ voiceState: 'stopped' });
    setTimeout(() => set({ voiceState: 'idle' }), 500);
  },

  appendStreamToken: (token: string, messageId?: string) => {
    const key = messageId || 'latest';
    const existing = streamBuffer.tokensByMessageId.get(key) || [];
    existing.push(token);
    streamBuffer.tokensByMessageId.set(key, existing);

    if (streamBuffer.rafHandle === null) {
      const scheduleRaf = typeof requestAnimationFrame === 'function'
        ? requestAnimationFrame
        : (cb: FrameRequestCallback) => setTimeout(cb, 16);
      streamBuffer.rafHandle = scheduleRaf(() => {
        streamBuffer.rafHandle = null;
        get().flushStreamBuffer();
      });
    }
  },

  flushStreamBuffer: () => {
    if (streamBuffer.rafHandle !== null) {
      if (typeof cancelAnimationFrame === 'function') {
        cancelAnimationFrame(streamBuffer.rafHandle);
      } else {
        clearTimeout(streamBuffer.rafHandle as any);
      }
      streamBuffer.rafHandle = null;
    }
    if (streamBuffer.tokensByMessageId.size === 0) return;

    const snapshot = new Map(streamBuffer.tokensByMessageId);
    streamBuffer.tokensByMessageId.clear();

    set((state) => {
      const history = [...state.chatHistory];
      let mutated = false;

      snapshot.forEach((tokens, msgId) => {
        const appended = tokens.join('');
        if (!appended) return;

        let targetIdx = -1;
        if (msgId && msgId !== 'latest') {
          targetIdx = history.findIndex((m) => m.id === msgId);
        }
        if (targetIdx === -1) {
          targetIdx = history.length - 1;
        }

        if (targetIdx >= 0 && targetIdx < history.length) {
          const target = history[targetIdx];
          history[targetIdx] = {
            ...target,
            status: target.status === 'thinking' ? 'streaming' : target.status,
            assistant_response: (target.assistant_response || '') + appended,
          };
          mutated = true;
        }
      });

      return mutated ? { chatHistory: history } : state;
    });
  },

  initWebSocket: () => {
    wsService.connect();
    wsService.subscribe((event) => {
      const now = event.timestamp || Date.now();
      if (event.event_type === 'status') {
        const st = event.payload.status;
        set((state) => {
          if (now < state.lastVoiceEventTs) return state; // Event ordering guard
          let vs: VoiceState = state.voiceState;
          if (st === 'listening') vs = 'listening';
          else if (st === 'thinking') vs = 'thinking';
          else if (st === 'speaking') vs = 'speaking';
          else if (st === 'ready') vs = 'idle';

          return {
            statusText: st,
            isThinking: st === 'thinking',
            voiceState: vs,
            lastVoiceEventTs: now,
          };
        });

        if (st === 'listening') {
          get().setActiveView('voice');
        }
      } else if (event.event_type === 'token_stream') {
        get().appendStreamToken(event.payload.token, event.payload.message_id);
        if (event.payload.is_final) {
          get().flushStreamBuffer();
        }
      } else if (event.event_type === 'model_changed') {
        set({
          currentModel: event.payload.current_model,
          modelMode: event.payload.mode,
        });
      } else if (event.event_type === 'stt_text') {
        set((state) => {
          if (now < state.lastVoiceEventTs) return state;
          return {
            sttText: event.payload.text || 'Listening...',
            lastVoiceEventTs: now,
          };
        });
      } else if (event.event_type === 'action_update') {
        get().fetchApprovals();
      }
    });
  },
}));

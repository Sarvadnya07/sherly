/**
 * SHERLY API CLIENT SERVICE
 * Handles REST calls to FastAPI backend.
 */

import {
  ChatMessage,
  ModelsListResponse,
  VoiceStatusResponse,
  AudioDevicesResponse,
  FileNode,
  FileReadResponse,
  TerminalRunResponse,
  PendingApproval,
  PreviewChange,
  SettingsResponse,
} from '../types/api';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://127.0.0.1:8000/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'API Request failed');
  }
  return res.json();
}

export const api = {
  // Chat
  sendChat: (prompt: string, fileAttachment?: string, signal?: AbortSignal) =>
    fetchJson<ChatMessage>('/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt, file_attachment: fileAttachment }),
      signal,
    }),
  getHistory: () => fetchJson<{ messages: ChatMessage[] }>('/chat/history'),

  // Models
  getModels: () => fetchJson<ModelsListResponse>('/models'),
  selectModel: (modelName: string) =>
    fetchJson<{ message: string; current_model: string }>('/models/select', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName }),
    }),
  setModelMode: (mode: 'auto' | 'manual') =>
    fetchJson<{ mode: string; current_model: string | null }>('/models/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  refreshModels: () => fetchJson<{ count: number; resolved: string | null }>('/models/refresh', { method: 'POST' }),
  unloadModel: () => fetchJson<{ message: string }>('/models/unload', { method: 'POST' }),
  setApiKey: (provider: string, apiKey: string) =>
    fetchJson<{ message: string }>('/models/key', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),

  // Voice
  getVoiceStatus: () => fetchJson<VoiceStatusResponse>('/voice/status'),
  getAudioDevices: () => fetchJson<AudioDevicesResponse>('/voice/devices'),
  startVoice: () => fetchJson<{ message: string }>('/voice/start', { method: 'POST' }),
  stopVoice: () => fetchJson<{ message: string }>('/voice/stop', { method: 'POST' }),
  stopSpeaking: () => fetchJson<{ message: string }>('/voice/stop_speaking', { method: 'POST' }),

  // Files & Workspace
  getFileTree: () => fetchJson<FileNode>('/files/tree'),
  readFile: (path: string) => fetchJson<FileReadResponse>(`/files/read?path=${encodeURIComponent(path)}`),
  writeFile: (path: string, content: string) =>
    fetchJson<{ message: string }>('/files/write', {
      method: 'POST',
      body: JSON.stringify({ path, content }),
    }),
  runTerminal: (command: string) =>
    fetchJson<TerminalRunResponse>('/files/terminal/run', {
      method: 'POST',
      body: JSON.stringify({ command }),
    }),

  // Actions & Approvals
  getApprovals: () => fetchJson<PendingApproval[]>('/actions/approvals'),
  approveAction: (id: string) => fetchJson<{ message: string }>(`/actions/approvals/${id}/approve`, { method: 'POST' }),
  rejectAction: (id: string) => fetchJson<{ message: string }>(`/actions/approvals/${id}/reject`, { method: 'POST' }),
  undoLastAction: () => fetchJson<{ message: string }>('/actions/undo', { method: 'POST' }),
  getPreview: (id: string) => fetchJson<PreviewChange[]>(`/actions/previews/${id}`),
  applyPreview: (id: string) => fetchJson<{ message: string }>(`/actions/previews/${id}/apply`, { method: 'POST' }),

  // Settings
  getSettings: () => fetchJson<SettingsResponse>('/settings'),
  updateSettings: (updates: { auto_mode?: boolean; model_mode?: string; plugins?: Record<string, boolean> }) =>
    fetchJson<{ message: string }>('/settings', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),
};

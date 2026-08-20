/**
 * SHERLY API CONTRACT TYPES — frontend/src/types/api.ts
 * Strongly-typed contracts matching backend Pydantic schemas.
 */

// ── Error Envelope ────────────────────────────────────────────────────────────
export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id?: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

// ── Chat & Memory ─────────────────────────────────────────────────────────────
export interface ChatRequest {
  prompt: string;
  file_attachment?: string;
}

export interface ToolActivityInfo {
  name: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  duration_ms?: number;
}

export interface ChatMessage {
  id?: string;
  user_prompt: string;
  assistant_response: string;
  timestamp: string;
  attached_file?: string;
  request_id?: string;
  status?: 'sending' | 'thinking' | 'streaming' | 'completed' | 'error' | 'cancelled';
  tool_activity?: ToolActivityInfo;
  error?: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
}

// ── Models & Scanner ──────────────────────────────────────────────────────────
export interface ModelInfo {
  name: string;
  family: string;
  tag: string;
  size: number;
  coding: boolean;
  local: boolean;
}

export interface ModelsListResponse {
  mode: 'auto' | 'manual';
  current_model: string | null;
  pinned_model: string | null;
  is_ollama_running: boolean;
  models: ModelInfo[];
}

export interface ModelSelectRequest {
  model_name: string;
}

export interface ModelModeRequest {
  mode: 'auto' | 'manual';
}

export interface ApiKeyRequest {
  provider: 'openai' | 'gemini' | 'groq';
  api_key: string;
}

// ── Voice ──────────────────────────────────────────────────────────────────────
export interface VoiceStatusResponse {
  is_listening: boolean;
  is_speaking: boolean;
  current_device: string | null;
}

export interface AudioDevicesResponse {
  devices: string[];
}

// ── Files & Workspace ─────────────────────────────────────────────────────────
export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[] | null;
}

export interface FileReadResponse {
  path: string;
  content: string;
}

export interface FileWriteRequest {
  path: string;
  content: string;
}

export interface TerminalRunRequest {
  command: string;
}

export interface TerminalRunResponse {
  output: string;
  exit_code: number;
}

// ── Actions, Approvals & Previews ─────────────────────────────────────────────
export interface PendingApproval {
  action_id: string;
  command: string;
  level: 'confirm' | 'dangerous';
  timestamp: number;
}

export interface ActionEntry {
  action_id: string;
  action: string;
  action_type: string;
  timestamp: string;
  undoable: boolean;
}

export interface PreviewChange {
  action_id: string;
  file_path: string;
  old_code: string;
  new_code: string;
  reason?: string;
}

// ── Settings ──────────────────────────────────────────────────────────────────
export interface SettingsResponse {
  auto_mode: boolean;
  model_mode: 'auto' | 'manual';
  current_model: string | null;
  api_keys_configured: Record<string, boolean>;
  plugins: Record<string, boolean>;
}

export interface SettingsUpdateRequest {
  auto_mode?: boolean;
  model_mode?: 'auto' | 'manual';
  plugins?: Record<string, boolean>;
}

// ── Real-Time WebSocket Discriminated Union ───────────────────────────────────
export interface StatusEvent {
  event_type: 'status';
  payload: {
    status: 'ready' | 'thinking' | 'listening' | 'speaking';
    prompt?: string;
  };
  timestamp?: number;
  request_id?: string;
}

export interface SttTextEvent {
  event_type: 'stt_text';
  payload: {
    text: string;
    is_final?: boolean;
  };
  timestamp?: number;
  request_id?: string;
}

export interface ActionUpdateEvent {
  event_type: 'action_update';
  payload: {
    action_id: string;
    status: 'approved' | 'rejected' | 'preview_applied' | 'preview_rejected';
  };
  timestamp?: number;
  request_id?: string;
}

export interface ModelChangedEvent {
  event_type: 'model_changed';
  payload: {
    current_model: string | null;
    mode: 'auto' | 'manual';
  };
  timestamp?: number;
  request_id?: string;
}

export interface PongEvent {
  event_type: 'pong';
  payload: Record<string, never>;
  timestamp?: number;
  request_id?: string;
}

export type SherlyEvent =
  | StatusEvent
  | SttTextEvent
  | ActionUpdateEvent
  | ModelChangedEvent
  | PongEvent;

/**
 * SHERLY API CONTRACT TYPES
 * Strongly-typed contracts matching backend Pydantic schemas.
 */

export interface ChatMessage {
  id?: string;
  user_prompt: string;
  assistant_response: string;
  timestamp: string;
  attached_file?: string;
}

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

export interface VoiceStatusResponse {
  is_listening: boolean;
  is_speaking: boolean;
  current_device: string | null;
}

export interface AudioDevicesResponse {
  devices: string[];
}

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

export interface TerminalRunResponse {
  output: string;
  exit_code: number;
}

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

export interface SettingsResponse {
  auto_mode: boolean;
  model_mode: 'auto' | 'manual';
  current_model: string | null;
  api_keys_configured: Record<string, boolean>;
  plugins: Record<string, boolean>;
}

export interface SherlyEvent {
  event_type: string;
  payload: Record<string, any>;
}

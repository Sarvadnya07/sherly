import React, { useEffect, useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { RefreshCw, CheckCircle, Package, Zap, Key } from 'lucide-react';
import { api } from '../services/api';

export const ModelsView: React.FC = () => {
  const {
    modelsList,
    currentModel,
    modelMode,
    isOllamaRunning,
    fetchModels,
    selectModel,
    setMode,
  } = useSherlyStore();

  const [apiKeyProvider, setApiKeyProvider] = useState<string | null>(null);
  const [apiKeyValue, setApiKeyValue] = useState('');

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleApiKeySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyProvider || !apiKeyValue.trim()) return;
    try {
      await api.setApiKey(apiKeyProvider, apiKeyValue.trim());
      setApiKeyProvider(null);
      setApiKeyValue('');
      fetchModels();
    } catch (e) {
      console.error('Error setting API key:', e);
    }
  };

  const activeModelInfo = modelsList.find((m) => m.name === currentModel) || modelsList[0];

  return (
    <div className="flex-1 flex h-full bg-[#0e0e15] overflow-hidden">
      {/* Left Repository Section */}
      <div className="flex-1 p-6 flex flex-col gap-5 overflow-y-auto">
        {/* Header & Controls */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-100">Model Repository</h2>
            <p className="text-xs text-gray-400">Manage local Ollama models and remote API endpoints.</p>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs font-semibold text-purple-300 cursor-pointer">
              <input
                type="checkbox"
                checked={modelMode === 'auto'}
                onChange={(e) => setMode(e.target.checked ? 'auto' : 'manual')}
                className="rounded bg-white/10 border-white/20 text-purple-600 focus:ring-0"
              />
              <span>Auto Model Detection</span>
            </label>

            <button
              onClick={() => fetchModels()}
              className="bg-white/5 hover:bg-white/10 text-gray-200 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Local Models Cards */}
        <div className="flex flex-col gap-3">
          <span className="text-[10px] font-extrabold text-gray-500 tracking-wider">
            LOCAL OLLAMA MODELS ({modelsList.length})
          </span>

          {!isOllamaRunning ? (
            <div className="bg-[#13131e] border border-amber-500/30 rounded-xl p-4 text-center flex flex-col gap-1">
              <h4 className="text-xs font-bold text-amber-400">⚠️ Ollama Server Offline</h4>
              <p className="text-xs text-gray-400">
                Start Ollama locally (http://127.0.0.1:11434) to load local LLMs.
              </p>
            </div>
          ) : modelsList.length === 0 ? (
            <div className="bg-[#13131e] border border-white/10 rounded-xl p-4 text-center text-xs text-gray-400">
              No models detected. Run <code className="text-purple-300">ollama pull qwen2.5-coder:3b</code> in terminal.
            </div>
          ) : (
            modelsList.map((m) => {
              const isActive = m.name === currentModel;
              const sizeGb = ((m.size || 0) / (1024 * 1024 * 1024)).toFixed(1);

              return (
                <div
                  key={m.name}
                  className={`bg-[#13131e] border rounded-xl p-3.5 flex flex-col gap-3 transition ${
                    isActive ? 'border-purple-500/60 bg-purple-900/10' : 'border-white/10'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      {isActive ? <Zap className="w-4 h-4 text-purple-400" /> : <Package className="w-4 h-4 text-gray-500" />}
                      <div>
                        <h4 className="text-xs font-bold text-gray-100">{m.name}</h4>
                        <p className="text-[10px] text-gray-400">Local • {sizeGb} GB</p>
                      </div>
                    </div>

                    {isActive ? (
                      <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5" /> Running
                      </span>
                    ) : (
                      <button
                        onClick={() => selectModel(m.name)}
                        className="bg-purple-900/30 hover:bg-purple-900/50 text-purple-300 border border-purple-500/40 px-3 py-1 rounded-lg text-xs font-semibold transition"
                      >
                        Set Active
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {m.coding && (
                      <span className="bg-white/5 text-gray-300 px-2 py-0.5 rounded text-[10px]">Code</span>
                    )}
                    <span className="bg-white/5 text-gray-300 px-2 py-0.5 rounded text-[10px] uppercase">
                      {m.family}
                    </span>
                    {m.tag && m.tag !== 'latest' && (
                      <span className="bg-white/5 text-gray-300 px-2 py-0.5 rounded text-[10px]">{m.tag}</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Remote Providers Section */}
        <div className="flex flex-col gap-3 mt-2">
          <span className="text-[10px] font-extrabold text-gray-500 tracking-wider">
            REMOTE API PROVIDERS
          </span>

          {['openai', 'gemini', 'groq'].map((provider) => (
            <div
              key={provider}
              className="bg-[#13131e] border border-white/10 rounded-xl p-3.5 flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-semibold text-gray-200 capitalize">{provider} (API)</span>
              </div>

              <button
                onClick={() => setApiKeyProvider(provider)}
                className="bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 px-3 py-1 rounded-lg text-xs font-semibold transition"
              >
                Configure Key
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Right Inspector Panel */}
      <div className="w-72 bg-[#0b0b11] border-l border-white/10 p-5 flex flex-col gap-5 overflow-y-auto">
        <h3 className="text-sm font-bold text-gray-100">ⓘ Model Inspector</h3>

        {activeModelInfo ? (
          <div className="flex flex-col gap-4">
            <div>
              <h4 className="text-sm font-bold text-purple-400">{activeModelInfo.name}</h4>
              <p className="text-xs text-gray-400 mt-1">
                Local {activeModelInfo.family} model optimized for desktop execution.
              </p>
            </div>

            {/* Capabilities Grid */}
            <div className="flex flex-col gap-2">
              <span className="text-[9px] font-extrabold text-gray-500 tracking-wider">CAPABILITIES</span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-2 text-center text-purple-300 font-semibold">
                  💻 Code Gen
                </div>
                <div className="bg-white/5 border border-white/5 rounded-lg p-2 text-center text-gray-600">
                  👁 Vision
                </div>
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-2 text-center text-purple-300 font-semibold">
                  🧠 Reasoning
                </div>
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-2 text-center text-purple-300 font-semibold">
                  💬 Instruct
                </div>
              </div>
            </div>

            {/* Resource Allocation */}
            <div className="flex flex-col gap-3">
              <span className="text-[9px] font-extrabold text-gray-500 tracking-wider">RESOURCE ALLOCATION</span>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Disk Size</span>
                <span className="text-gray-200 font-semibold">
                  {(activeModelInfo.size / (1024 * 1024 * 1024)).toFixed(1)} GB
                </span>
              </div>

              <div className="w-full bg-white/10 rounded-full h-1.5">
                <div className="bg-purple-500 h-1.5 rounded-full w-1/3"></div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Host</span>
                <span className="text-gray-200 font-semibold">127.0.0.1:11434</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Provider</span>
                <span className="text-gray-200 font-semibold">Ollama Local</span>
              </div>
            </div>
          </div>
        ) : (
          <span className="text-xs text-gray-500 italic">No model active</span>
        )}
      </div>

      {/* API Key Modal */}
      {apiKeyProvider && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <form onSubmit={handleApiKeySubmit} className="bg-[#13131e] border border-white/10 rounded-2xl p-6 w-96 flex flex-col gap-4">
            <h3 className="text-sm font-bold text-gray-100 capitalize">Configure {apiKeyProvider} API Key</h3>
            <input
              type="password"
              value={apiKeyValue}
              onChange={(e) => setApiKeyValue(e.target.value)}
              placeholder="Enter API key..."
              className="bg-[#161624] border border-white/10 rounded-lg p-2.5 text-xs text-gray-100 focus:outline-none focus:border-purple-500"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setApiKeyProvider(null)}
                className="px-4 py-2 text-xs text-gray-400 hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
              >
                Save Key
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

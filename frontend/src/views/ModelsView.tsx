import React, { useEffect, useState } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { RefreshCw, Key } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

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
    <div className="flex-1 flex h-full bg-canvas overflow-hidden">
      {/* Left Repository Section */}
      <div className="flex-1 p-6 flex flex-col gap-5 overflow-y-auto">
        {/* Header & Controls */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-zinc-100">Model Repository</h2>
            <p className="text-xs text-zinc-400 mt-0.5">Manage local Ollama models and cloud remote API endpoints.</p>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs font-medium text-zinc-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={modelMode === 'auto'}
                onChange={(e) => setMode(e.target.checked ? 'auto' : 'manual')}
                className="rounded bg-zinc-800 border-zinc-700 text-indigo-600 focus:ring-0 cursor-pointer"
              />
              <span>Auto Model Detection</span>
            </label>

            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchModels()}
              icon={<RefreshCw className="w-3 h-3" />}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Local Ollama Models List */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-semibold text-zinc-500 tracking-wider uppercase">
            LOCAL OLLAMA MODELS ({modelsList.length})
          </span>

          {!isOllamaRunning ? (
            <Card variant="default" padding="lg" className="border-amber-500/30 text-center flex flex-col gap-1">
              <h4 className="text-xs font-bold text-amber-400">Ollama Server Offline</h4>
              <p className="text-xs text-zinc-400">
                Start Ollama locally (http://127.0.0.1:11434) to load and execute local LLMs.
              </p>
            </Card>
          ) : modelsList.length === 0 ? (
            <Card variant="default" padding="lg" className="text-center text-xs text-zinc-400">
              No models detected. Run <code className="text-zinc-200 font-mono">ollama pull qwen2.5-coder:3b</code> in terminal.
            </Card>
          ) : (
            modelsList.map((m) => {
              const isActive = m.name === currentModel;
              const sizeGb = ((m.size || 0) / (1024 * 1024 * 1024)).toFixed(1);

              return (
                <div
                  key={m.name}
                  className={`bg-zinc-900/60 border rounded-xl p-4 flex flex-col gap-3 transition shadow-subtle ${
                    isActive
                      ? 'border-indigo-500/40 bg-zinc-900'
                      : 'border-white/[0.06] hover:border-white/[0.12]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-zinc-100">{m.name}</h4>
                      <p className="text-[10px] font-mono text-zinc-400 mt-0.5">Local LLM • {sizeGb} GB Footprint</p>
                    </div>

                    {isActive ? (
                      <Badge variant="success" size="md" pulse>
                        Active in Memory
                      </Badge>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => selectModel(m.name)}
                      >
                        Set Active Model
                      </Button>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5 flex-wrap">
                    {m.coding && (
                      <Badge variant="brand" size="sm">Code Specialist</Badge>
                    )}
                    <Badge variant="neutral" size="sm" className="uppercase">{m.family}</Badge>
                    {m.tag && m.tag !== 'latest' && (
                      <Badge variant="neutral" size="sm">{m.tag}</Badge>
                    )}
                    <Badge variant="neutral" size="sm">Ollama Local</Badge>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Remote Cloud Providers Section */}
        <div className="flex flex-col gap-2.5 mt-2">
          <span className="text-[10px] font-semibold text-zinc-500 tracking-wider uppercase">
            REMOTE CLOUD PROVIDERS
          </span>

          {[
            { id: 'openai', name: 'OpenAI (API)', desc: 'GPT-4o, GPT-4o-mini' },
            { id: 'gemini', name: 'Google Gemini (API)', desc: 'Gemini 1.5 Pro, Flash' },
            { id: 'groq', name: 'Groq (API)', desc: 'Llama 3 70B, Mixtral 8x7B' },
          ].map((provider) => (
            <div
              key={provider.id}
              className="bg-zinc-900/60 border border-white/[0.06] hover:border-white/[0.12] rounded-xl p-3.5 flex items-center justify-between transition shadow-subtle"
            >
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-white/[0.06] flex items-center justify-center text-zinc-300">
                  <Key className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-zinc-200">{provider.name}</h4>
                  <p className="text-[10px] text-zinc-500 font-mono">{provider.desc}</p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setApiKeyProvider(provider.id)}
              >
                Configure Key
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Right Inspector Panel */}
      <div className="w-80 bg-sidebar border-l border-white/[0.06] p-5 flex flex-col gap-4 overflow-y-auto shrink-0">
        <span className="text-[10px] font-semibold text-zinc-500 tracking-wider uppercase">MODEL INSPECTOR</span>

        {activeModelInfo ? (
          <div className="flex flex-col gap-4">
            <div>
              <h4 className="text-sm font-semibold text-zinc-100">{activeModelInfo.name}</h4>
              <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                Local {activeModelInfo.family} model loaded in Ollama engine.
              </p>
            </div>

            {/* Capabilities Badge Grid */}
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-semibold text-zinc-500 tracking-wider uppercase">METADATA</span>
              <div className="flex flex-wrap gap-1.5 text-xs">
                {activeModelInfo.coding && (
                  <Badge variant="brand" size="md">Coding Specialist</Badge>
                )}
                <Badge variant="neutral" size="md" className="uppercase">{activeModelInfo.family}</Badge>
                {activeModelInfo.tag && activeModelInfo.tag !== 'latest' && (
                  <Badge variant="neutral" size="md">{activeModelInfo.tag}</Badge>
                )}
                <Badge variant="neutral" size="md">{activeModelInfo.local ? 'Local Inference' : 'Cloud Endpoint'}</Badge>
              </div>
            </div>

            {/* Resource Allocation */}
            <div className="flex flex-col gap-2.5">
              <span className="text-[10px] font-semibold text-zinc-500 tracking-wider uppercase">RESOURCE ALLOCATION</span>

              {activeModelInfo.size > 0 && (
                <>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-zinc-400">Disk Footprint</span>
                    <span className="text-zinc-100 font-bold">
                      {(activeModelInfo.size / (1024 * 1024 * 1024)).toFixed(2)} GB
                    </span>
                  </div>

                  {/* Memory Visual Bar */}
                  <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{ width: `${Math.min(100, Math.max(15, (activeModelInfo.size / (1024 * 1024 * 1024 * 8)) * 100))}%` }}
                    />
                  </div>
                </>
              )}

              <div className="flex items-center justify-between text-xs font-mono pt-1">
                <span className="text-zinc-400">Provider</span>
                <span className="text-zinc-200 font-medium">{activeModelInfo.local ? 'Ollama' : 'Cloud Provider'}</span>
              </div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-zinc-400">Host</span>
                <span className="text-zinc-200 font-medium">{activeModelInfo.local ? '127.0.0.1:11434' : 'Remote API'}</span>
              </div>
            </div>
          </div>
        ) : (
          <span className="text-xs text-zinc-500 italic">No model selected</span>
        )}
      </div>

      {/* API Key Modal Dialog */}
      {apiKeyProvider && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <form
            onSubmit={handleApiKeySubmit}
            role="dialog"
            aria-modal="true"
            aria-labelledby="api-key-title"
            className="bg-zinc-900 border border-white/[0.12] rounded-xl p-5 w-96 flex flex-col gap-3.5 shadow-elevated"
          >
            <h3 id="api-key-title" className="text-sm font-bold text-zinc-100 capitalize">
              Configure {apiKeyProvider} API Key
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Enter your API secret key to enable remote completions. Keys are stored safely in your local configuration.
            </p>
            <input
              type="password"
              value={apiKeyValue}
              onChange={(e) => setApiKeyValue(e.target.value)}
              placeholder="sk-..."
              className="bg-zinc-950 border border-white/[0.10] focus:border-indigo-500 rounded-lg p-2.5 text-xs font-mono text-zinc-100 focus:outline-none"
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setApiKeyProvider(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
              >
                Save Key
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

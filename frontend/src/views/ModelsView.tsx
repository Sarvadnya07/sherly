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
            <h2 className="text-sm font-semibold text-txt-primary">Model Repository</h2>
            <p className="text-xs text-txt-muted mt-0.5">Manage local Ollama models and cloud remote API endpoints.</p>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs font-medium text-txt-secondary cursor-pointer select-none">
              <input
                type="checkbox"
                checked={modelMode === 'auto'}
                onChange={(e) => setMode(e.target.checked ? 'auto' : 'manual')}
                className="rounded bg-input border-border-subtle text-brand focus:ring-0 cursor-pointer"
              />
              <span>Auto Model Detection</span>
            </label>

            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchModels()}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Local Ollama Models List */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-semibold text-txt-muted tracking-wider uppercase">
            LOCAL OLLAMA MODELS ({modelsList.length})
          </span>

          {!isOllamaRunning ? (
            <Card variant="default" padding="lg" className="border-status-warning/30 text-center flex flex-col gap-1">
              <h4 className="text-xs font-bold text-status-warning">Ollama Server Offline</h4>
              <p className="text-xs text-txt-muted">
                Start Ollama locally (http://127.0.0.1:11434) to scan and execute local models.
              </p>
            </Card>
          ) : modelsList.length === 0 ? (
            <Card variant="default" padding="lg" className="text-center text-xs text-txt-muted">
              No models detected. Run <code className="text-txt-primary font-mono">ollama pull qwen2.5-coder:3b</code> in terminal.
            </Card>
          ) : (
            modelsList.map((m) => {
              const isActive = m.name === currentModel;
              const sizeGb = ((m.size || 0) / (1024 * 1024 * 1024)).toFixed(1);

              return (
                <div
                  key={m.name}
                  className={`bg-card border rounded-lg p-4 flex flex-col gap-3 transition shadow-subtle ${
                    isActive
                      ? 'border-brand/40 bg-card'
                      : 'border-border-subtle hover:border-border-medium'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-txt-primary">{m.name}</h4>
                      <p className="text-[11px] font-mono text-txt-muted mt-0.5">Local LLM • {sizeGb} GB Disk Footprint</p>
                    </div>

                    {isActive ? (
                      <Badge variant="success" size="md" pulse>
                        Running
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
          <span className="text-[10px] font-semibold text-txt-muted tracking-wider uppercase">
            REMOTE CLOUD PROVIDERS
          </span>

          {[
            { id: 'openai', name: 'OpenAI (API)', desc: 'GPT-4o, GPT-4o-mini' },
            { id: 'gemini', name: 'Google Gemini (API)', desc: 'Gemini 1.5 Pro, Flash' },
            { id: 'groq', name: 'Groq (API)', desc: 'Llama 3 70B, Mixtral 8x7B' },
          ].map((provider) => (
            <div
              key={provider.id}
              className="bg-card border border-border-subtle hover:border-border-medium rounded-lg p-3.5 flex items-center justify-between transition shadow-subtle"
            >
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-md bg-surface border border-border-subtle flex items-center justify-center text-txt-secondary">
                  <Key className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-txt-primary">{provider.name}</h4>
                  <p className="text-[11px] text-txt-muted font-mono">{provider.desc}</p>
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
      <div className="w-80 bg-sidebar border-l border-border-subtle p-5 flex flex-col gap-4 overflow-y-auto shrink-0 select-none">
        <span className="text-[10px] font-semibold text-txt-muted tracking-wider uppercase">MODEL METADATA</span>

        {activeModelInfo ? (
          <div className="flex flex-col gap-4">
            <div>
              <h4 className="text-sm font-semibold text-txt-primary">{activeModelInfo.name}</h4>
              <p className="text-xs text-txt-muted mt-1 leading-relaxed">
                Local {activeModelInfo.family} model managed via Ollama.
              </p>
            </div>

            {/* Capabilities Badge Grid */}
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-semibold text-txt-muted tracking-wider uppercase">ATTRIBUTES</span>
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

            {/* Genuine Backend Details */}
            <div className="flex flex-col gap-2 pt-2 border-t border-border-subtle text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-txt-muted font-sans">Disk Size:</span>
                <span className="text-txt-primary font-bold">
                  {(activeModelInfo.size / (1024 * 1024 * 1024)).toFixed(2)} GB
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-txt-muted font-sans">Provider:</span>
                <span className="text-txt-secondary font-medium">{activeModelInfo.local ? 'Ollama' : 'Cloud Provider'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-txt-muted font-sans">Endpoint:</span>
                <span className="text-txt-secondary font-medium">{activeModelInfo.local ? 'http://127.0.0.1:11434' : 'Remote API'}</span>
              </div>
            </div>
          </div>
        ) : (
          <span className="text-xs text-txt-muted italic">No model selected</span>
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
            className="bg-card border border-border-medium rounded-lg p-5 w-96 flex flex-col gap-3.5 shadow-elevated"
          >
            <h3 id="api-key-title" className="text-sm font-bold text-txt-primary capitalize">
              Configure {apiKeyProvider} API Key
            </h3>
            <p className="text-xs text-txt-muted leading-relaxed">
              Enter your API secret key to enable remote completions. Keys are stored safely in your local configuration.
            </p>
            <input
              type="password"
              value={apiKeyValue}
              onChange={(e) => setApiKeyValue(e.target.value)}
              placeholder="sk-..."
              className="bg-input border border-border-subtle focus:border-brand rounded p-2 text-xs font-mono text-txt-primary focus:outline-none"
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

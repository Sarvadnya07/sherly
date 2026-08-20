import React, { useEffect } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Square, X, Mic, Volume2, VolumeX, Loader2, Wrench, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const VoiceOverlayView: React.FC = () => {
  const {
    voiceState,
    audioDevices,
    selectedDevice,
    sttText,
    statusText,
    voiceErrorMessage,
    fetchAudioDevices,
    setActiveView,
    startVoiceSession,
    stopVoiceSession,
    cancelVoiceSession,
    stopVoiceSpeaking,
  } = useSherlyStore();

  useEffect(() => {
    fetchAudioDevices();
  }, [fetchAudioDevices]);

  // Global Keyboard Shortcuts (Esc to Cancel / Stop, Enter to Stop Recording)
  useEffect(() => {
    const handleKeys = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        if (voiceState === 'speaking') {
          stopVoiceSpeaking();
        } else {
          cancelVoiceSession();
          setActiveView('assistant');
        }
      } else if (e.key === 'Enter' && voiceState === 'listening') {
        e.preventDefault();
        stopVoiceSession();
      }
    };

    window.addEventListener('keydown', handleKeys);
    return () => window.removeEventListener('keydown', handleKeys);
  }, [voiceState, stopVoiceSpeaking, cancelVoiceSession, stopVoiceSession, setActiveView]);

  return (
    <div className="flex-1 flex flex-col items-center justify-between p-8 bg-canvas select-none h-full overflow-hidden">
      <div className="flex-1 flex flex-col items-center justify-center gap-6 max-w-xl w-full">
        {/* Pulsing Mic / Speaker Capsule */}
        <div className="relative flex items-center justify-center">
          {voiceState === 'listening' && (
            <>
              <div className="absolute w-28 h-28 rounded-full bg-brand/10 animate-ping" />
              <div className="absolute w-20 h-20 rounded-full bg-brand/20" />
            </>
          )}

          {voiceState === 'speaking' && (
            <>
              <div className="absolute w-28 h-28 rounded-full bg-status-success/10 animate-ping" />
              <div className="absolute w-20 h-20 rounded-full bg-status-success/20" />
            </>
          )}

          <div
            className={`w-14 h-14 rounded-full bg-card border flex items-center justify-center text-txt-primary shadow-elevated z-10 transition-colors ${
              voiceState === 'speaking'
                ? 'border-status-success/50 text-status-success'
                : voiceState === 'error'
                ? 'border-status-danger/50 text-status-danger'
                : 'border-brand/40 text-brand'
            }`}
          >
            {voiceState === 'speaking' ? (
              <Volume2 className="w-6 h-6 text-status-success animate-pulse" />
            ) : voiceState === 'thinking' ? (
              <Loader2 className="w-6 h-6 text-brand animate-spin" />
            ) : (
              <Mic className="w-6 h-6 text-brand" />
            )}
          </div>
        </div>

        {/* Canonical Status Indicator Pill */}
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              voiceState === 'speaking'
                ? 'bg-status-success animate-pulse'
                : voiceState === 'error'
                ? 'bg-status-danger'
                : 'bg-brand animate-pulse'
            }`}
          />
          <span className="text-xs font-semibold text-txt-secondary tracking-wider uppercase">
            {voiceState === 'speaking'
              ? 'SPEAKING'
              : voiceState === 'thinking'
              ? 'THINKING...'
              : voiceState === 'transcribing'
              ? 'TRANSCRIBING...'
              : voiceState === 'error'
              ? 'AUDIO ERROR'
              : 'LISTENING (Ctrl+Shift+L)'}
          </span>
        </div>

        {/* Live Transcription Display */}
        <div className="text-sm font-medium text-txt-primary max-w-md text-center leading-relaxed min-h-[48px] flex items-center justify-center px-4">
          {voiceErrorMessage ? (
            <div className="flex items-center gap-2 text-status-danger text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{voiceErrorMessage}</span>
            </div>
          ) : (
            <p className="italic text-txt-secondary">
              "{sttText}
              {voiceState === 'listening' && (
                <span className="animate-blink font-mono font-bold text-brand">_</span>
              )}
              "
            </p>
          )}
        </div>

        {/* Tool Execution Activity in Voice Mode */}
        {statusText.startsWith('tool:') && (
          <div className="inline-flex items-center gap-2 bg-card border border-border-subtle rounded-full px-3 py-1 text-xs text-txt-secondary shadow-subtle animate-in fade-in">
            <Wrench className="w-3.5 h-3.5 text-status-info animate-pulse" />
            <span>Executing {statusText.replace('tool:', '')}...</span>
          </div>
        )}

        {/* Ambient Activity Bars */}
        <div className="flex items-center gap-1.5 h-6">
          {[35, 65, 25, 85, 45, 75, 35, 90, 50, 70, 30].map((height, idx) => (
            <div
              key={idx}
              className={`w-1 rounded-full transition-all duration-300 ${
                voiceState === 'speaking'
                  ? 'bg-status-success animate-pulse'
                  : voiceState === 'listening'
                  ? 'bg-brand animate-pulse'
                  : 'bg-border-subtle'
              }`}
              style={{
                height: voiceState === 'idle' ? '20%' : `${height}%`,
                animationDelay: `${idx * 80}ms`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Floating Action & Device Bar */}
      <div className="bg-card border border-border-subtle rounded-lg px-4 py-2 flex items-center gap-3 shadow-elevated shrink-0 select-none">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            cancelVoiceSession();
            setActiveView('assistant');
          }}
          icon={<X className="w-3.5 h-3.5" />}
        >
          Cancel
        </Button>

        {voiceState === 'speaking' ? (
          <Button
            variant="secondary"
            size="sm"
            onClick={stopVoiceSpeaking}
            icon={<VolumeX className="w-3.5 h-3.5 text-status-danger" />}
          >
            Stop Speaking
          </Button>
        ) : voiceState === 'listening' ? (
          <Button
            variant="primary"
            size="sm"
            onClick={stopVoiceSession}
            icon={<Square className="w-3 h-3 fill-white" />}
          >
            Stop Listening
          </Button>
        ) : (
          <Button
            variant="primary"
            size="sm"
            onClick={startVoiceSession}
            icon={<Mic className="w-3.5 h-3.5" />}
          >
            Start Listening
          </Button>
        )}

        <select
          value={selectedDevice || ''}
          onChange={(e) => useSherlyStore.setState({ selectedDevice: e.target.value })}
          className="bg-input border border-border-subtle text-txt-secondary text-xs rounded px-2.5 py-1 focus:outline-none focus:border-brand cursor-pointer"
          aria-label="Select Input Microphone"
        >
          {audioDevices.length > 0 ? (
            audioDevices.map((d) => (
              <option key={d} value={d} className="bg-card text-txt-primary">
                {d}
              </option>
            ))
          ) : (
            <option className="bg-card text-txt-primary">Default Microphone</option>
          )}
        </select>
      </div>
    </div>
  );
};

import React, { useEffect } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Square, X, Mic } from 'lucide-react';
import { api } from '../services/api';
import { Button } from '../components/ui/Button';

export const VoiceOverlayView: React.FC = () => {
  const {
    audioDevices,
    selectedDevice,
    sttText,
    fetchAudioDevices,
    setActiveView,
  } = useSherlyStore();

  useEffect(() => {
    fetchAudioDevices();
  }, [fetchAudioDevices]);

  const handleStopRecording = async () => {
    try {
      await api.stopVoice();
    } catch (e) {
      console.warn('Error stopping voice:', e);
    }
    setActiveView('assistant');
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-between p-8 bg-canvas select-none h-full overflow-hidden">
      <div className="flex-1 flex flex-col items-center justify-center gap-6 max-w-xl w-full">
        {/* Pulsing Mic Capsule */}
        <div className="relative flex items-center justify-center">
          <div className="absolute w-28 h-28 rounded-full bg-brand/10 animate-ping" />
          <div className="absolute w-20 h-20 rounded-full bg-brand/20" />
          <div className="w-14 h-14 rounded-full bg-card border border-brand/40 flex items-center justify-center text-txt-primary shadow-elevated z-10">
            <Mic className="w-6 h-6 text-brand" />
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brand animate-pulse" />
          <span className="text-xs font-semibold text-txt-secondary tracking-wider uppercase">
            LISTENING (Ctrl+Shift+L)
          </span>
        </div>

        {/* Live Transcription Display */}
        <div className="text-sm font-medium text-txt-primary max-w-md text-center leading-relaxed min-h-[48px] flex items-center justify-center px-4">
          <p className="italic text-txt-secondary">
            "{sttText}
            <span className="animate-blink font-mono font-bold text-brand">_</span>"
          </p>
        </div>

        {/* Ambient Listening Pulse Bars */}
        <div className="flex items-center gap-1.5 h-6">
          {[35, 65, 25, 85, 45, 75, 35, 90, 50, 70, 30].map((height, idx) => (
            <div
              key={idx}
              className="w-1 bg-brand rounded-full transition-all duration-300 animate-pulse"
              style={{ height: `${height}%`, animationDelay: `${idx * 80}ms` }}
            />
          ))}
        </div>
      </div>

      {/* Floating Controls Bar */}
      <div className="bg-card border border-border-subtle rounded-lg px-4 py-2 flex items-center gap-3 shadow-elevated shrink-0">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setActiveView('workspace')}
          icon={<X className="w-3.5 h-3.5" />}
        >
          Cancel
        </Button>

        <Button
          variant="primary"
          size="sm"
          onClick={handleStopRecording}
          icon={<Square className="w-3 h-3 fill-white" />}
        >
          Stop Recording
        </Button>

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

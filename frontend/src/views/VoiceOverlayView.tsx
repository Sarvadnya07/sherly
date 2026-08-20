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
          <div className="absolute w-32 h-32 rounded-full bg-indigo-500/10 animate-ping" />
          <div className="absolute w-24 h-24 rounded-full bg-indigo-500/20" />
          <div className="w-14 h-14 rounded-full bg-zinc-900 border border-indigo-500/40 flex items-center justify-center text-zinc-100 shadow-elevated z-10">
            <Mic className="w-6 h-6 text-indigo-400" />
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
          <span className="text-xs font-semibold text-zinc-300 tracking-wider uppercase">
            LISTENING (Ctrl+Shift+L)
          </span>
        </div>

        {/* Live Transcription Display */}
        <div className="text-sm font-medium text-zinc-100 max-w-md text-center leading-relaxed min-h-[48px] flex items-center justify-center px-4">
          <p className="italic text-zinc-300">
            "{sttText}
            <span className="animate-blink font-mono font-bold text-indigo-400">_</span>"
          </p>
        </div>

        {/* Audio Equalizer Waveform Bars */}
        <div className="flex items-center gap-1.5 h-6">
          {[35, 65, 25, 85, 45, 75, 35, 90, 50, 70, 30].map((height, idx) => (
            <div
              key={idx}
              className="w-1 bg-indigo-500 rounded-full transition-all duration-300 animate-pulse"
              style={{ height: `${height}%`, animationDelay: `${idx * 80}ms` }}
            />
          ))}
        </div>
      </div>

      {/* Floating Controls Bar */}
      <div className="bg-zinc-900 border border-white/[0.08] rounded-xl px-4 py-2 flex items-center gap-3 shadow-elevated shrink-0">
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
          className="bg-zinc-800 border border-white/[0.08] text-zinc-300 text-xs rounded-md px-2.5 py-1 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          {audioDevices.length > 0 ? (
            audioDevices.map((d) => (
              <option key={d} value={d} className="bg-zinc-900 text-zinc-200">
                {d}
              </option>
            ))
          ) : (
            <option className="bg-zinc-900 text-zinc-200">Default Microphone</option>
          )}
        </select>
      </div>
    </div>
  );
};

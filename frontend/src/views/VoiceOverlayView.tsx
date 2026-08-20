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
          <div className="absolute w-36 h-36 rounded-full bg-brand/15 animate-ping" />
          <div className="absolute w-28 h-28 rounded-full bg-brand/25" />
          <div className="w-16 h-16 rounded-full bg-card border-2 border-brand flex items-center justify-center text-gray-100 shadow-elevated z-10">
            <Mic className="w-7 h-7 text-purple-300" />
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
          <span className="text-xs font-bold text-purple-300 tracking-widest uppercase">
            LISTENING (Ctrl+Shift+L)
          </span>
        </div>

        {/* Live Transcription Display */}
        <div className="text-sm font-medium text-gray-100 max-w-md text-center leading-relaxed min-h-[48px] flex items-center justify-center px-4">
          <p className="italic text-gray-200">
            "{sttText}
            <span className="animate-blink font-mono font-bold text-purple-400">_</span>"
          </p>
        </div>

        {/* Audio Equalizer Waveform Bars */}
        <div className="flex items-center gap-1.5 h-8">
          {[35, 65, 25, 85, 45, 75, 35, 90, 50, 70, 30].map((height, idx) => (
            <div
              key={idx}
              className="w-1.5 bg-brand rounded-full transition-all duration-300 animate-pulse"
              style={{ height: `${height}%`, animationDelay: `${idx * 80}ms` }}
            />
          ))}
        </div>
      </div>

      {/* Floating Controls Bar */}
      <div className="bg-card border border-white/[0.10] rounded-xl px-4 py-2.5 flex items-center gap-3 shadow-elevated shrink-0">
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
          className="bg-white/[0.04] border border-white/[0.08] text-gray-300 text-xs rounded-md px-2.5 py-1 focus:outline-none focus:border-brand cursor-pointer"
        >
          {audioDevices.length > 0 ? (
            audioDevices.map((d) => (
              <option key={d} value={d} className="bg-card text-gray-200">
                {d}
              </option>
            ))
          ) : (
            <option className="bg-card text-gray-200">System Default Mic</option>
          )}
        </select>
      </div>
    </div>
  );
};

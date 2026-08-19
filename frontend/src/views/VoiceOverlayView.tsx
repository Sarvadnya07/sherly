import React, { useEffect } from 'react';
import { useSherlyStore } from '../stores/useSherlyStore';
import { Square, X } from 'lucide-react';
import { api } from '../services/api';

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
    <div className="flex-1 flex flex-col items-center justify-between p-8 bg-[#09090d] select-none h-full">
      <div className="flex-1 flex flex-col items-center justify-center gap-6">
        {/* Pulsing Mic HUD */}
        <div className="relative flex items-center justify-center">
          <div className="absolute w-44 h-44 rounded-full bg-purple-600/20 animate-ping"></div>
          <div className="absolute w-36 h-36 rounded-full bg-purple-700/30"></div>
          <div className="w-20 h-20 rounded-full bg-[#161224] border-2 border-purple-500/60 flex items-center justify-center text-gray-100 text-2xl shadow-xl shadow-purple-900/40 z-10">
            🎙
          </div>
        </div>

        {/* Listening Indicator */}
        <span className="text-xs font-extrabold text-purple-400 tracking-widest">
          ● LISTENING...
        </span>

        {/* Transcription Display */}
        <div className="text-xl font-semibold text-gray-100 max-w-xl text-center">
          "{sttText}
          <span className="animate-blink">_</span>"
        </div>

        {/* Audio Equalizer Visualizer */}
        <div className="flex items-center gap-1.5 h-8">
          {[40, 70, 30, 90, 50, 80, 40].map((height, idx) => (
            <div
              key={idx}
              className="w-2 bg-purple-500 rounded-full transition-all duration-300 animate-pulse"
              style={{ height: `${height}%` }}
            ></div>
          ))}
        </div>
      </div>

      {/* Floating Control Pill Bar */}
      <div className="bg-[#161622]/90 border border-white/10 rounded-2xl px-4 py-2 flex items-center gap-4 shadow-2xl">
        <button
          onClick={() => setActiveView('workspace')}
          className="text-xs text-gray-400 hover:text-gray-200 font-semibold px-2 py-1 flex items-center gap-1 transition"
        >
          <X className="w-3.5 h-3.5" />
          <span>Cancel</span>
        </button>

        <button
          onClick={handleStopRecording}
          className="bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-2 transition"
        >
          <Square className="w-3.5 h-3.5 fill-white" />
          <span>Stop Recording</span>
        </button>

        <select
          value={selectedDevice || ''}
          onChange={(e) => useSherlyStore.setState({ selectedDevice: e.target.value })}
          className="bg-white/5 border border-white/10 text-gray-300 text-xs rounded-xl px-3 py-1.5 focus:outline-none"
        >
          {audioDevices.length > 0 ? (
            audioDevices.map((d) => (
              <option key={d} value={d} className="bg-[#13131e] text-gray-200">
                🎙 {d}
              </option>
            ))
          ) : (
            <option className="bg-[#13131e] text-gray-200">🎙 System Default Mic</option>
          )}
        </select>
      </div>
    </div>
  );
};

import React from 'react';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export const VoiceAssistant = ({
  isListening,
  onStartListening,
  onStopListening,
  transcript,
  isSpeaking,
  onStopSpeaking,
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-gradient-to-b from-emerald-50/50 to-white rounded-2xl border border-emerald-100 shadow-sm my-3">
      {/* Speaking Indicator */}
      {isSpeaking && (
        <div className="flex items-center gap-2 mb-3 px-3 py-1 bg-amber-100 text-amber-900 rounded-full text-xs font-semibold animate-pulse">
          <Volume2 className="w-4 h-4 text-amber-700" />
          <span>ಮಾತನಾಡುತ್ತಿದೆ... (Speaking)</span>
          <button
            onClick={onStopSpeaking}
            className="ml-2 text-xs underline text-amber-800 font-bold hover:text-black"
          >
            ನಿಲ್ಲಿಸಿ (Stop)
          </button>
        </div>
      )}

      {/* Mic Button */}
      <div className="relative">
        {isListening && (
          <div className="absolute -inset-3 rounded-full bg-emerald-400 opacity-75 animate-ping" />
        )}
        <button
          onClick={isListening ? onStopListening : onStartListening}
          className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-95 ${
            isListening
              ? 'bg-red-600 text-white ring-4 ring-red-200'
              : 'bg-saathi-primary hover:bg-saathi-dark text-white ring-4 ring-emerald-100'
          }`}
          aria-label={isListening ? 'Stop recording voice' : 'Start speaking'}
        >
          {isListening ? (
            <MicOff className="w-9 h-9" />
          ) : (
            <Mic className="w-9 h-9" />
          )}
        </button>
      </div>

      {/* Status Label */}
      <p className="mt-3 text-sm font-semibold text-slate-700 text-center">
        {isListening ? (
          <span className="text-emerald-700 font-bold animate-pulse">
            {t.micListening}
          </span>
        ) : (
          <span>{t.micTapToSpeak}</span>
        )}
      </p>

      {/* Interim Transcript Preview */}
      {transcript && isListening && (
        <div className="mt-2 px-4 py-2 bg-white rounded-xl border border-slate-200 text-sm text-slate-800 shadow-inner max-w-md text-center">
          "{transcript}"
        </div>
      )}
    </div>
  );
};

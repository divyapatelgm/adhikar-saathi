import React from 'react';
import { Mic, MicOff, Volume2, Radio } from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export const VoiceAssistant = ({
  isListening,
  onStartListening,
  onStopListening,
  transcript,
  isSpeaking,
  onStopSpeaking,
}) => {
  const { language, t } = useLanguage();

  const speakingText =
    language === 'kn' ? 'ಮಾತನಾಡುತ್ತಿದೆ... (Speaking)' : language === 'hi' ? 'बोल रहा है... (Speaking)' : 'Speaking...';
  const stopText =
    language === 'kn' ? 'ನಿಲ್ಲಿಸಿ (Stop)' : language === 'hi' ? 'रोकें (Stop)' : 'Stop';
  const listeningHint =
    language === 'kn'
      ? 'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕನ್ನಡ, ಹಿಂದಿ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಿ...'
      : language === 'hi'
      ? 'अपना प्रश्न हिंदी, कन्नड़ या अंग्रेजी में बोलें...'
      : 'Ask any scheme or rights question in your natural voice...';

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-gradient-to-b from-emerald-50/60 to-white rounded-2xl border border-emerald-100 shadow-sm my-3 transition-all">
      {/* Speaking Indicator */}
      {isSpeaking && (
        <div className="flex items-center gap-2 mb-3 px-3.5 py-1.5 bg-amber-100/90 text-amber-900 rounded-full text-xs font-semibold shadow-xs animate-pulse">
          <Volume2 className="w-4 h-4 text-amber-700 animate-bounce" />
          <span>{speakingText}</span>
          <button
            onClick={onStopSpeaking}
            className="ml-2 px-2 py-0.5 bg-white/80 rounded-full text-[11px] font-bold text-amber-900 hover:bg-white transition-colors"
          >
            {stopText}
          </button>
        </div>
      )}

      {/* Mic Button with Pulsing Wave */}
      <div className="relative">
        {isListening && (
          <>
            <div className="absolute -inset-4 rounded-full bg-red-400/40 animate-ping" />
            <div className="absolute -inset-2 rounded-full bg-red-500/30 animate-pulse" />
          </>
        )}
        <button
          onClick={isListening ? onStopListening : onStartListening}
          className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-95 ${
            isListening
              ? 'bg-red-600 text-white ring-4 ring-red-200 shadow-red-200'
              : 'bg-saathi-primary hover:bg-saathi-dark text-white ring-4 ring-emerald-100 hover:shadow-xl'
          }`}
          aria-label={isListening ? 'Stop recording voice' : 'Start speaking'}
        >
          {isListening ? (
            <MicOff className="w-9 h-9 animate-pulse" />
          ) : (
            <Mic className="w-9 h-9" />
          )}
        </button>
      </div>

      {/* Status Label */}
      <div className="mt-3 text-center">
        <p className="text-sm font-bold text-slate-800">
          {isListening ? (
            <span className="inline-flex items-center gap-1.5 text-red-600 font-bold animate-pulse">
              <Radio className="w-4 h-4" />
              {t.micListening}
            </span>
          ) : (
            <span>{t.micTapToSpeak}</span>
          )}
        </p>
        <p className="text-xs text-slate-500 mt-1 max-w-xs">
          {isListening ? listeningHint : (language === 'kn' ? 'ಮೈಕ್ ಒತ್ತಿ ನೇರವಾಗಿ ಮಾತನಾಡಿ' : language === 'hi' ? 'माइक दबाकर सीधे बोलें' : 'Tap mic and ask naturally')}
        </p>
      </div>

      {/* Interim Transcript Live Preview */}
      {transcript && isListening && (
        <div className="mt-2.5 px-4 py-2 bg-emerald-50 rounded-xl border border-emerald-200 text-sm text-emerald-900 shadow-inner max-w-md text-center font-medium animate-fadeIn">
          "{transcript}"
        </div>
      )}
    </div>
  );
};

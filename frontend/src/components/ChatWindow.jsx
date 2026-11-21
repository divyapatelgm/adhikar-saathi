import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { useSpeech } from '../hooks/useSpeech';
import { sendChat } from '../services/api';
import { VoiceAssistant } from './VoiceAssistant';
import {
  Send,
  Volume2,
  ExternalLink,
  Shield,
  Trash2,
  Sparkles,
} from 'lucide-react';

export const ChatWindow = () => {
  const { language, t } = useLanguage();
  const {
    isListening,
    transcript,
    setTranscript,
    startListening,
    stopListening,
    isSpeaking,
    speak,
    stopSpeaking,
  } = useSpeech(language);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const getWelcomeText = (lang) => {
    return lang === 'kn'
      ? 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಅಧಿಕಾರ ಸಾಥಿ. ನೀವು ಯಾವುದೇ ಸರ್ಕಾರಿ ಯೋಜನೆ ಅಥವಾ ನಿಮ್ಮ ಹಕ್ಕುಗಳ ಬಗ್ಗೆ ಧ್ವನಿ ಅಥವಾ ಟೈಪ್ ಮಾಡುವ ಮೂಲಕ ಕೇಳಬಹುದು.'
      : lang === 'hi'
      ? 'नमस्ते! मैं आपका अधिकार साथी हूँ। आप किसी भी सरकारी योजना या अपने अधिकारों के बारे में बोलकर या लिखकर पूछ सकते हैं।'
      : 'Hello! I am Adhikar Saathi. You can ask about government welfare schemes or your civic rights using voice or text.';
  };

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: getWelcomeText(language),
      sources: [],
      is_link_out: false,
    },
  ]);

  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === 'welcome') {
        return [{ ...prev[0], text: getWelcomeText(language) }];
      }
      return prev;
    });
  }, [language]);

  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // If transcript completes, update input
  useEffect(() => {
    if (transcript && !isListening) {
      setInput(transcript);
    }
  }, [transcript, isListening]);

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: query.trim(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setTranscript('');
    setLoading(true);

    try {
      const res = await sendChat(query.trim(), language);
      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: res.reply_text,
        sources: res.sources || [],
        is_link_out: res.is_link_out,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Automatically speak the first sentence for high-accessibility voice mode
      speak(res.reply_text, language);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text:
          language === 'kn'
            ? 'ಕ್ಷಮಿಸಿ, ಪ್ರತಿಕ್ರಿಯೆ ಪಡೆಯುವಲ್ಲಿ ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಪ್ರಯತ್ನಿಸಿ.'
            : 'Sorry, could not process request. Please try again.',
        sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    stopSpeaking();
  };

  return (
    <div className="flex flex-col h-[750px] max-h-[85vh] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header bar */}
      <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-saathi-primary" />
          <span className="font-bold text-sm text-slate-800">
            {t.tabChat}
          </span>
        </div>
        <button
          onClick={clearChat}
          className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200/60 transition-colors"
          title={t.clearChat}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Mic Touch Control Bar */}
      <div className="px-4">
        <VoiceAssistant
          isListening={isListening}
          onStartListening={startListening}
          onStopListening={stopListening}
          transcript={transcript}
          isSpeaking={isSpeaking}
          onStopSpeaking={stopSpeaking}
        />
      </div>

      {/* Quick Questions Chips */}
      <div className="px-4 py-2 border-b border-slate-100 flex gap-2 overflow-x-auto text-xs no-scrollbar">
        {((language === 'en')
          ? [
              { text: 'My MGNREGA wages are delayed, what should I do?', label: '🌾 MGNREGA Wage Delay' },
              { text: 'Ration shop dealer is refusing to give rice', label: '🍚 PDS Ration Grievance' },
              { text: 'How do I file an RTI application in Karnataka?', label: '📄 RTI Application' },
              { text: 'Tell me about dairy farmer incentives', label: '🐄 Dairy Grant' },
            ]
          : (language === 'hi')
          ? [
              { text: 'नरेगा मजदूरी नहीं मिली', label: '🌾 मनरेगा मजदूरी (MGNREGA)' },
              { text: 'राशन डीलर राशन नहीं दे रहा', label: '🍚 राशन शिकायत (Ration)' },
              { text: 'आरटीआई आवेदन कैसे करें', label: '📄 आरटीआई अर्जी (RTI)' },
              { text: 'डेरी किसान अनुदान योजना', label: '🐄 डेयरी अनुदान (Dairy)' },
            ]
          : [
              { text: 'ನರೇಗಾ ಕೂಲಿ ವೇತನ ಬಂದಿಲ್ಲ', label: '🌾 ನರೇಗಾ ವೇತನ (MGNREGA Wages)' },
              { text: 'ರೇಷನ್ ಅಂಗಡಿ ಮಾಲೀಕ ಅಕ್ಕಿ ಕೊಡುತ್ತಿಲ್ಲ', label: '🍚 ಪಡಿತರ ಸಮಸ್ಯೆ (Ration Grievance)' },
              { text: 'ಮಾಹಿತಿ ಹಕ್ಕು ಅರ್ಜಿ ಹಾಕುವುದು ಹೇಗೆ', label: '📄 ಮಾಹಿತಿ ಹಕ್ಕು (RTI Filing)' },
              { text: 'ಹೈನುಗಾರಿಕೆ ರೈತರ ಅನುದಾನ ಯೋಜನೆ', label: '🐄 ಡೇರಿ ಅನುದಾನ (Dairy Grant)' },
            ]
        ).map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(chip.text)}
            className="flex-shrink-0 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-full border border-slate-200/80 transition-colors"
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-saathi-primary text-white rounded-br-xs shadow-sm font-medium'
                  : 'bg-slate-100 text-slate-900 rounded-bl-xs border border-slate-200/70 shadow-sm'
              }`}
            >
              {/* Spoken Audio Button for Assistant */}
              {msg.sender === 'assistant' && (
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200">
                  <span className="text-[11px] font-bold text-saathi-primary uppercase tracking-wider flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    {language === 'kn' ? 'ಅಧಿಕಾರ ಸಾಥಿ' : language === 'hi' ? 'अधिकार साथी' : 'Adhikar Saathi'}
                  </span>
                  <button
                    onClick={() => speak(msg.text, language)}
                    className="p-1 rounded-md hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
                    title="Read aloud in regional voice"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Message Content */}
              <div className="whitespace-pre-line">{msg.text}</div>

              {/* Citations & Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-slate-200 text-xs space-y-1">
                  <span className="font-semibold text-slate-600 block text-[11px]">
                    {t.source}:
                  </span>
                  {msg.sources.map((s, idx) => (
                    <a
                      key={idx}
                      href={s.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-saathi-primary hover:text-saathi-dark font-bold underline mr-2"
                    >
                      <span>{s.source_name}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ))}
                </div>
              )}

              {/* Legal Disclaimer */}
              {msg.sender === 'assistant' && (
                <p className="mt-2 text-[10px] text-slate-500 italic">
                  * {t.disclaimer}
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-2xl p-4 text-sm text-slate-500 flex items-center gap-2 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-saathi-primary animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-saathi-primary animate-bounce [animation-delay:0.2s]" />
              <span className="w-2 h-2 rounded-full bg-saathi-primary animate-bounce [animation-delay:0.4s]" />
              <span>
                {language === 'kn' ? 'ಉತ್ತರಿಸಲಾಗುತ್ತಿದೆ...' : language === 'hi' ? 'उत्तर तैयार हो रहा है...' : 'Retrieving & thinking...'}
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="p-3 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t.askAnything}
            className="flex-1 p-3.5 bg-slate-100 rounded-xl border border-transparent focus:border-saathi-primary focus:bg-white text-sm font-medium transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-3.5 bg-saathi-primary hover:bg-saathi-dark disabled:opacity-40 text-white rounded-xl shadow-sm transition-transform active:scale-95"
            aria-label={t.send}
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

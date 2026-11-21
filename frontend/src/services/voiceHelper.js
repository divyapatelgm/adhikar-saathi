/**
 * Voice Helper for Indian Accents & Regional Languages (en-IN, kn-IN, hi-IN)
 */

export const LANG_CODE_MAP = {
  kn: 'kn-IN',
  hi: 'hi-IN',
  en: 'en-IN',
};

/**
 * Searches available browser voices and selects the optimal Indian accent voice.
 */
export const getIndianVoice = (voices, lang = 'en') => {
  if (!voices || voices.length === 0) return null;

  const targetLang = lang.toLowerCase();

  if (targetLang === 'kn') {
    // 1. Prioritize natural Kannada voices
    const knVoice = voices.find(v => {
      const vLang = (v.lang || '').toLowerCase();
      const vName = (v.name || '').toLowerCase();
      return (
        vLang.startsWith('kn') ||
        vName.includes('kannada') ||
        vName.includes('ಕನ್ನಡ') ||
        vName.includes('sapna') ||
        vName.includes('yash') ||
        vName.includes('gagan')
      );
    });
    if (knVoice) return knVoice;
  } else if (targetLang === 'hi') {
    // 2. Prioritize natural Hindi voices
    const hiVoice = voices.find(v => {
      const vLang = (v.lang || '').toLowerCase();
      const vName = (v.name || '').toLowerCase();
      return (
        vLang.startsWith('hi') ||
        vName.includes('hindi') ||
        vName.includes('हिन्दी') ||
        vName.includes('swara') ||
        vName.includes('madhur') ||
        vName.includes('kalpana') ||
        vName.includes('google हिन्दी')
      );
    });
    if (hiVoice) return hiVoice;
  } else {
    // 3. Prioritize English with natural Indian accent (en-IN)
    const indianEnVoice = voices.find(v => {
      const vLang = (v.lang || '').toLowerCase();
      const vName = (v.name || '').toLowerCase();
      const codeMatch = vLang === 'en-in' || vLang === 'en_in';
      const nameMatch = (
        vName.includes('india') ||
        vName.includes('indian') ||
        vName.includes('neerja') ||
        vName.includes('prabhat') ||
        vName.includes('heera') ||
        vName.includes('ravi') ||
        vName.includes('veena') ||
        vName.includes('rishi')
      );
      return codeMatch || nameMatch;
    });
    if (indianEnVoice) return indianEnVoice;
  }

  // Fallback to any voice with -IN or _IN in locale
  const genericIndianVoice = voices.find(v => (v.lang || '').toUpperCase().includes('-IN') || (v.lang || '').toUpperCase().includes('_IN'));
  if (genericIndianVoice) return genericIndianVoice;

  // Otherwise match by language prefix or return null
  const fallback = voices.find(v => (v.lang || '').toLowerCase().startsWith(LANG_CODE_MAP[targetLang]?.substring(0, 2) || 'en'));
  return fallback || null;
};

/**
 * Prepares and configures a SpeechSynthesisUtterance with Indian pronunciation & natural human pacing.
 */
export const prepareIndianUtterance = (text, lang = 'kn', voices = []) => {
  if (!text) return new SpeechSynthesisUtterance('');

  // 1. Strip emojis, bullet markers, markdown headers, and formatting artifacts
  let cleanText = text
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1F018}-\u{1F270}]/gu, '')
    .replace(/[*#_`>]/g, '')
    .replace(/•|\-|\d+\./g, '')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/Checklist.*?:/gi, '')
    .replace(/Overview.*?:/gi, '')
    .replace(/Summary.*?:/gi, '')
    .replace(/\s+/g, ' ')
    .trim();

  // 2. If the text is very long (multiple paragraphs), speak the first 2-3 natural sentences
  // so the citizen hears a warm, conversational briefing without cognitive overload
  const sentences = cleanText.split(/(?<=[.?!।])\s+/);
  if (sentences.length > 3) {
    cleanText = sentences.slice(0, 3).join(' ');
  }

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = LANG_CODE_MAP[lang] || 'en-IN';
  utterance.rate = 0.90; // Natural, conversational cadence tuned for comprehension
  utterance.pitch = 1.05; // Slightly warmer vocal frequency

  const selectedVoice = getIndianVoice(voices, lang);
  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  return utterance;
};

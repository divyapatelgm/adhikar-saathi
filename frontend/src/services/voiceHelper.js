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

  if (targetLang === 'en') {
    // 1. Prioritize English with Indian accent (en-IN)
    const indianEnVoice = voices.find(v => {
      const codeMatch = v.lang === 'en-IN' || v.lang === 'en_IN' || v.lang.toLowerCase() === 'en-in';
      const nameMatch = v.name && (
        v.name.includes('India') ||
        v.name.includes('Indian') ||
        v.name.includes('Heera') ||
        v.name.includes('Ravi') ||
        v.name.includes('Neerja') ||
        v.name.includes('Veena') ||
        v.name.includes('Rishi') ||
        v.name.includes('Prabhat')
      );
      return codeMatch || nameMatch;
    });
    if (indianEnVoice) return indianEnVoice;
  } else if (targetLang === 'kn') {
    // 2. Prioritize Kannada voices
    const knVoice = voices.find(v => {
      return (
        v.lang.toLowerCase().startsWith('kn') ||
        (v.name && (v.name.toLowerCase().includes('kannada') || v.name.includes('ಕನ್ನಡ') || v.name.includes('Sapna') || v.name.includes('Yash')))
      );
    });
    if (knVoice) return knVoice;
  } else if (targetLang === 'hi') {
    // 3. Prioritize Hindi voices
    const hiVoice = voices.find(v => {
      return (
        v.lang.toLowerCase().startsWith('hi') ||
        (v.name && (v.name.toLowerCase().includes('hindi') || v.name.includes('हिन्दी') || v.name.includes('Kalpana') || v.name.includes('Madhur') || v.name.includes('Swara')))
      );
    });
    if (hiVoice) return hiVoice;
  }

  // Fallback to any voice with -IN or _IN in locale
  const genericIndianVoice = voices.find(v => v.lang.includes('-IN') || v.lang.includes('_IN'));
  if (genericIndianVoice) return genericIndianVoice;

  // Otherwise match by prefix or return null to use browser default
  const fallback = voices.find(v => v.lang.toLowerCase().startsWith(LANG_CODE_MAP[targetLang]?.substring(0, 2) || 'en'));
  return fallback || null;
};

/**
 * Prepares and configures a SpeechSynthesisUtterance with Indian pronunciation & pacing.
 */
export const prepareIndianUtterance = (text, lang = 'kn', voices = []) => {
  // Clean markdown syntax, URLs, and multiple spaces for clear speech
  const cleanText = text
    .replace(/[*#_`>]/g, '')
    .replace(/https?:\/\/\S+/g, '')
    .replace(/\n+/g, '. ')
    .trim();

  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.lang = LANG_CODE_MAP[lang] || 'en-IN';
  utterance.rate = 0.92; // Clear, deliberate pace suitable for rural & regional comprehension
  utterance.pitch = 1.0;

  const selectedVoice = getIndianVoice(voices, lang);
  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  return utterance;
};

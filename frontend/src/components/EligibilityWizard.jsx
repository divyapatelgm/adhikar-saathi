import React, { useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { evaluateEligibility } from '../services/api';
import { SchemeCard } from './SchemeCard';
import { CheckCircle2, RotateCcw, ArrowRight, ArrowLeft, UserCheck, AlertTriangle } from 'lucide-react';

export const EligibilityWizard = ({ allSchemes }) => {
  const { language, t } = useLanguage();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  // Profile fields: all default to null/empty
  const [profile, setProfile] = useState({
    state: 'Karnataka',
    occupation: null,
    owns_land: null,
    land_acres: null,
    age: null,
    annual_income: null,
    category: null,
    gender: null,
    bpl: null,
    is_student: null,
    disability: null,
  });

  const updateProfile = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const handleRunEvaluation = async () => {
    setLoading(true);
    try {
      const data = await evaluateEligibility(profile, language);
      setResults(data);
    } catch (e) {
      console.error('Error evaluating eligibility:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setProfile({
      state: 'Karnataka',
      occupation: null,
      owns_land: null,
      land_acres: null,
      age: null,
      annual_income: null,
      category: null,
      gender: null,
      bpl: null,
      is_student: null,
      disability: null,
    });
    setStep(1);
    setResults(null);
  };

  // Language Display Rule:
  // 1. If language === 'en': ONLY English displayed (no other languages).
  // 2. If language === 'kn': Kannada larger (primary font), English smaller below.
  // 3. If language === 'hi': Hindi larger (primary font), English smaller below.
  const renderLang = (kn, hi, en, mode = 'option') => {
    if (language === 'en') {
      if (mode === 'title') {
        return <h3 className="text-base font-bold text-slate-800">{en}</h3>;
      }
      if (mode === 'label') {
        return <span className="text-xs font-semibold text-slate-700 block mb-2">{en}</span>;
      }
      if (mode === 'button') {
        return <span>{en}</span>;
      }
      return <div className="font-bold text-sm text-slate-900">{en}</div>;
    }

    const primary = language === 'hi' ? hi : kn;

    if (mode === 'title') {
      return (
        <h3 className="text-base font-bold text-slate-800">
          <span>{primary}</span>
          <span className="block text-xs font-normal text-slate-500 mt-0.5">{en}</span>
        </h3>
      );
    }

    if (mode === 'label') {
      return (
        <span className="block mb-2">
          <span className="text-xs font-bold text-slate-800 block">{primary}</span>
          <span className="text-[11px] font-normal text-slate-500 block">{en}</span>
        </span>
      );
    }

    if (mode === 'button') {
      return (
        <span className="inline-flex flex-col items-center leading-tight">
          <span className="font-bold">{primary}</span>
          <span className="text-[10px] font-normal opacity-80">{en}</span>
        </span>
      );
    }

    // Default 'option'
    return (
      <div>
        <div className="font-bold text-sm text-slate-900">{primary}</div>
        <div className="text-xs text-slate-500 font-normal">{en}</div>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Questionnaire Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
          <div className="flex items-center gap-2.5">
            <UserCheck className="w-6 h-6 text-saathi-primary" />
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {t.tabEligibility}
              </h2>
              <p className="text-xs text-slate-500">
                {language === 'en'
                  ? `Step ${step} of 4`
                  : language === 'hi'
                  ? `चरण ${step} / 4 (Step ${step} of 4)`
                  : `ಹಂತ ${step} / 4 (Step ${step} of 4)`}
              </p>
            </div>
          </div>
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>{t.resetWizard}</span>
          </button>
        </div>

        {/* Step 1: Occupation */}
        {step === 1 && (
          <div className="space-y-4">
            {renderLang(
              '1. ನಿಮ್ಮ ಮುಖ್ಯ ಉದ್ಯೋಗ ಅಥವಾ ವೃತ್ತಿ ಯಾವುದು?',
              '1. आपका मुख्य व्यवसाय या आजीविका क्या है?',
              '1. What is your primary occupation?',
              'title'
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {[
                { val: 'farmer', kn: 'ರೈತ / ಕೃಷಿ ಕಾರ್ಮಿಕ', hi: 'किसान / कृषि मजदूर', en: 'Farmer / Agri Worker', icon: '🌾' },
                { val: 'worker', kn: 'ದೈನಂದಿನ ಕೂಲಿ ಕಾರ್ಮಿಕ', hi: 'दैनिक वेतन भोगी मजदूर', en: 'Daily Wage Labourer', icon: '⚒️' },
                { val: 'student', kn: 'ವಿದ್ಯಾರ್ಥಿ', hi: 'विद्यार्थी / छात्र', en: 'Student', icon: '🎓' },
                { val: 'artisan', kn: 'ಕುಶಲಕರ್ಮಿ / ನೇಕಾರ', hi: 'कारीगर / बुनकर', en: 'Artisan / Weaver', icon: '🧵' },
                { val: 'other', kn: 'ಇತರೆ / ಗೃಹಿಣಿ', hi: 'गृहणी / अन्य', en: 'Homemaker / Other', icon: '🏠' },
              ].map((item) => (
                <button
                  key={item.val}
                  onClick={() => {
                    updateProfile('occupation', item.val);
                    if (item.val === 'student') updateProfile('is_student', true);
                  }}
                  className={`p-4 rounded-2xl border text-left flex items-center gap-3 transition-all ${
                    profile.occupation === item.val
                      ? 'border-saathi-primary bg-emerald-50/80 ring-2 ring-emerald-600'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <span className="text-2xl">{item.icon}</span>
                  {renderLang(item.kn, item.hi, item.en, 'option')}
                </button>
              ))}
            </div>

            <div className="pt-4 flex justify-end">
              <button
                disabled={!profile.occupation}
                onClick={() => setStep(2)}
                className="px-6 py-3 bg-saathi-primary hover:bg-emerald-700 disabled:opacity-40 text-white font-bold rounded-xl flex items-center gap-2 shadow-sm transition-all"
              >
                {renderLang('ಮುಂದೆ', 'आगे', 'Next', 'button')}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Land & Age */}
        {step === 2 && (
          <div className="space-y-5">
            {renderLang(
              '2. ಕೃಷಿ ಭೂಮಿ ಮತ್ತು ವಯಸ್ಸು',
              '2. कृषि भूमि और आयु',
              '2. Agricultural Land & Citizen Age',
              'title'
            )}

            {/* Owns Land Question */}
            <div>
              {renderLang(
                'ನಿಮಗೆ ಅಥವಾ ನಿಮ್ಮ ಕುಟುಂಬಕ್ಕೆ ಕೃಷಿ ಭೂಮಿ ಇದೆಯೇ?',
                'क्या आपके या आपके परिवार के पास कृषि भूमि है?',
                'Do you or your family own agricultural land?',
                'label'
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => updateProfile('owns_land', true)}
                  className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm border text-center transition-all ${
                    profile.owns_land === true
                      ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {renderLang('ಹೌದು', 'हाँ', 'Yes', 'button')}
                </button>
                <button
                  onClick={() => {
                    updateProfile('owns_land', false);
                    updateProfile('land_acres', 0.0);
                  }}
                  className={`flex-1 py-3 px-4 rounded-xl font-bold text-sm border text-center transition-all ${
                    profile.owns_land === false
                      ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {renderLang('ಇಲ್ಲ', 'नहीं', 'No', 'button')}
                </button>
              </div>
            </div>

            {/* Land Acres if Yes */}
            {profile.owns_land === true && (
              <div>
                {renderLang(
                  'ಭೂಮಿ ವಿಸ್ತೀರ್ಣ (ಎಕರೆಯಲ್ಲಿ):',
                  'भूमि का क्षेत्रफल (एकड़ में):',
                  'Land Ownership (in Acres):',
                  'label'
                )}
                <input
                  type="number"
                  step="0.5"
                  value={profile.land_acres || ''}
                  onChange={(e) => updateProfile('land_acres', parseFloat(e.target.value) || null)}
                  placeholder="e.g. 2.5"
                  className="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-saathi-primary font-semibold text-sm"
                />
              </div>
            )}

            {/* Age */}
            <div>
              {renderLang(
                'ನಿಮ್ಮ ವಯಸ್ಸು (ವರ್ಷಗಳಲ್ಲಿ):',
                'आपकी आयु (वर्षों में):',
                'Your Age (in years):',
                'label'
              )}
              <input
                type="number"
                value={profile.age || ''}
                onChange={(e) => updateProfile('age', parseInt(e.target.value, 10) || null)}
                placeholder="e.g. 45"
                className="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-saathi-primary font-semibold text-sm"
              />
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="px-5 py-2.5 border border-slate-200 font-semibold rounded-xl text-slate-600 hover:bg-slate-50 text-sm flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" />
                {renderLang('ಹಿಂದೆ', 'पीछे', 'Back', 'button')}
              </button>
              <button
                onClick={() => setStep(3)}
                className="px-6 py-3 bg-saathi-primary hover:bg-emerald-700 text-white font-bold rounded-xl flex items-center gap-2 shadow-sm text-sm"
              >
                {renderLang('ಮುಂದೆ', 'आगे', 'Next', 'button')}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Income & BPL Card */}
        {step === 3 && (
          <div className="space-y-5">
            {renderLang(
              '3. ವಾರ್ಷಿಕ ಆದಾಯ ಮತ್ತು ಪಡಿತರ ಚೀಟಿ',
              '3. वार्षिक पारिवारिक आय और राशन कार्ड',
              '3. Annual Family Income & Ration Card',
              'title'
            )}

            {/* Income options */}
            <div>
              {renderLang(
                'ಕುಟುಂಬದ ಅಂದಾಜು ವಾರ್ಷಿಕ ಆದಾಯ:',
                'परिवार की अनुमानित वार्षिक आय:',
                'Estimated Annual Family Income:',
                'label'
              )}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  { kn: '₹1,00,000 ಒಳಗೆ', hi: '₹1,00,000 से कम', en: 'Under ₹1,00,000', val: 90000.0 },
                  { kn: '₹1L - ₹2.5L', hi: '₹1L - ₹2.5L', en: '₹1L - ₹2.5L', val: 180000.0 },
                  { kn: '₹2.5L ಕ್ಕಿಂತ ಹೆಚ್ಚು', hi: '₹2.5L से अधिक', en: 'Above ₹2.5L', val: 350000.0 },
                ].map((inc) => (
                  <button
                    key={inc.val}
                    onClick={() => updateProfile('annual_income', inc.val)}
                    className={`p-3 rounded-xl border text-center text-xs font-bold transition-all ${
                      profile.annual_income === inc.val
                        ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    {renderLang(inc.kn, inc.hi, inc.en, 'button')}
                  </button>
                ))}
              </div>
            </div>

            {/* BPL Card */}
            <div>
              {renderLang(
                'ಬಿಪಿಎಲ್ ಅಥವಾ ಅಂತ್ಯೋದಯ ಪಡಿತರ ಚೀಟಿ ಇದೆಯೇ?',
                'क्या आपके पास बीपीएल या अंत्योदय राशन कार्ड है?',
                'Do you have a BPL or Antyodaya Ration Card?',
                'label'
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => updateProfile('bpl', true)}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm border text-center transition-all ${
                    profile.bpl === true
                      ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {renderLang('ಹೌದು (ಬಿಪಿಎಲ್ ಕಾರ್ಡ್)', 'हाँ (बीपीएल कार्डधारक)', 'Yes (BPL Cardholder)', 'button')}
                </button>
                <button
                  onClick={() => updateProfile('bpl', false)}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm border text-center transition-all ${
                    profile.bpl === false
                      ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {renderLang('ಇಲ್ಲ (ಸಾಮಾನ್ಯ ಕಾರ್ಡ್)', 'नहीं (सामान्य कार्ड)', 'No (General Card)', 'button')}
                </button>
              </div>
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="px-5 py-2.5 border border-slate-200 font-semibold rounded-xl text-slate-600 hover:bg-slate-50 text-sm flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" />
                {renderLang('ಹಿಂದೆ', 'पीछे', 'Back', 'button')}
              </button>
              <button
                onClick={() => setStep(4)}
                className="px-6 py-3 bg-saathi-primary hover:bg-emerald-700 text-white font-bold rounded-xl flex items-center gap-2 shadow-sm text-sm"
              >
                {renderLang('ಮುಂದೆ', 'आगे', 'Next', 'button')}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Social Category & Gender */}
        {step === 4 && (
          <div className="space-y-5">
            {renderLang(
              '4. ಸಾಮಾಜಿಕ ವರ್ಗ ಮತ್ತು ಲಿಂಗ',
              '4. सामाजिक वर्ग और लिंग',
              '4. Social Category & Gender',
              'title'
            )}

            {/* Gender */}
            <div>
              {renderLang('ಲಿಂಗ:', 'लिंग:', 'Gender:', 'label')}
              <div className="flex gap-3">
                {[
                  { val: 'female', kn: 'ಮಹಿಳೆ', hi: 'महिला', en: 'Female' },
                  { val: 'male', kn: 'ಪುರುಷ', hi: 'पुरुष', en: 'Male' },
                  { val: 'other', kn: 'ಇತರೆ', hi: 'अन्य', en: 'Other' },
                ].map((g) => (
                  <button
                    key={g.val}
                    onClick={() => updateProfile('gender', g.val)}
                    className={`flex-1 py-2.5 rounded-xl text-xs font-bold border text-center transition-all ${
                      profile.gender === g.val
                        ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    {renderLang(g.kn, g.hi, g.en, 'button')}
                  </button>
                ))}
              </div>
            </div>

            {/* Social Category */}
            <div>
              {renderLang('ಸಾಮಾಜಿಕ ವರ್ಗ:', 'सामाजिक वर्ग:', 'Social Category:', 'label')}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {['SC', 'ST', 'OBC', 'GEN'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => updateProfile('category', cat)}
                    className={`py-2.5 rounded-xl text-xs font-bold border text-center transition-all ${
                      profile.category === cat
                        ? 'bg-emerald-50 border-emerald-600 text-emerald-900 ring-2 ring-emerald-600'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Action Check Eligibility Button */}
            <div className="pt-4 flex justify-between items-center">
              <button
                onClick={() => setStep(3)}
                className="px-5 py-2.5 border border-slate-200 font-semibold rounded-xl text-slate-600 hover:bg-slate-50 text-sm flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" />
                {renderLang('ಹಿಂದೆ', 'पीछे', 'Back', 'button')}
              </button>

              <button
                onClick={handleRunEvaluation}
                disabled={loading}
                className="px-8 py-3.5 bg-saathi-primary hover:bg-emerald-700 text-white font-extrabold text-sm rounded-xl flex items-center gap-2 shadow-lg transition-transform active:scale-95 disabled:opacity-50"
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>
                  {loading
                    ? language === 'en'
                      ? 'Evaluating schemes...'
                      : language === 'hi'
                      ? 'जांच की जा रही है...'
                      : 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...'
                    : renderLang('ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಿ', 'पात्रता जांचें', 'Check Eligibility', 'button')}
                </span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Recommended Next Question Banner if available */}
      {results && results.next_recommended_question && (
        <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200 flex items-start gap-3 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold text-amber-900">
              {t.nextQuestion}: {results.next_recommended_question.question[language] || results.next_recommended_question.question.en}
            </h4>
            <p className="text-xs text-amber-700 mt-0.5">
              {language === 'en'
                ? `Answering this question resolves eligibility for ${results.next_recommended_question.resolves_maybe_count} more schemes.`
                : language === 'hi'
                ? `इस प्रश्न का उत्तर देने से ${results.next_recommended_question.resolves_maybe_count} और योजनाओं की पात्रता स्पष्ट होगी।`
                : `ಈ ಒಂದು ಪ್ರಶ್ನೆಗೆ ಉತ್ತರಿಸಿದರೆ ಇನ್ನೂ ${results.next_recommended_question.resolves_maybe_count} ಯೋಜನೆಗಳ ಅರ್ಹತೆ ದೃಢವಾಗುತ್ತದೆ.`}
            </p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">
              {language === 'en'
                ? `Ranked Eligible Schemes (${results.ranked_schemes.length})`
                : language === 'hi'
                ? `योग्य योजनाओं की सूची (${results.ranked_schemes.length})`
                : `ಅರ್ಹ ಯೋಜನೆಗಳ ಪಟ್ಟಿ (${results.ranked_schemes.length})`}
            </h3>
            <span className="text-xs font-semibold text-slate-500">
              {language === 'en'
                ? `Total Evaluated: ${results.total_evaluated}`
                : language === 'hi'
                ? `कुल मूल्यांकन: ${results.total_evaluated}`
                : `ಒಟ್ಟು ಮೌಲ್ಯಮಾಪನ: ${results.total_evaluated}`}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.ranked_schemes.map((evalItem) => {
              const matchedScheme = (allSchemes || []).find((s) => s.id === evalItem.scheme_id);
              return (
                <SchemeCard
                  key={evalItem.scheme_id}
                  evaluation={evalItem}
                  schemeData={matchedScheme}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

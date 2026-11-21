import React, { useState, useRef } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { scanNotice } from '../services/api';
import { prepareIndianUtterance } from '../services/voiceHelper';
import {
  FileText,
  Upload,
  Camera,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ListOrdered,
  ExternalLink,
  Volume2,
  VolumeX,
  RotateCcw,
  Sparkles,
  ShieldAlert,
  Building,
  Info
} from 'lucide-react';

const SAMPLE_NOTICES = [
  {
    id: 'ration-kyc',
    titleEn: 'Ration Card e-KYC Notice (Urgent)',
    titleKn: 'ಪಡಿತರ ಚೀಟಿ e-KYC ಗಡುವು ನೋಟಿಸ್',
    titleHi: 'राशन कार्ड ई-केवाईसी समयसीमा नोटिस',
    text: `GOVERNMENT OF KARNATAKA
Department of Food, Civil Supplies and Consumer Affairs
NOTIFICATION - MANDATORY BIOMETRIC e-KYC
It is hereby notified that all Antyodaya Anna Yojana (AAY) and Priority Household (PHH) ration cardholders across Karnataka must complete biometric e-KYC authentication before December 31, 2026.
Every family member listed on the card must visit their registered Fair Price Shop (FPS) with original Aadhaar cards. Failure to complete e-KYC will result in automatic temporary suspension of food grain quota under Anna Bhagya scheme.
Official Portal: https://ahara.kar.nic.in`
  },
  {
    id: 'pm-kisan-seeding',
    titleEn: 'PM-KISAN Land Seeding Alert',
    titleKn: 'ಪಿಎಂ-ಕಿಸಾನ್ ಭೂಮಿ ಲಿಂಕ್ ನೋಟಿಸ್',
    titleHi: 'पीएम-किसान भूमि सीडिंग नोटिस',
    text: `DEPARTMENT OF AGRICULTURE & FARMERS WELFARE
PUBLIC CIRCULAR - MANDATORY LAND SEEDING & e-KYC
All PM-KISAN beneficiary farmers must ensure land record verification and Aadhaar-seeded bank account updates before March 31, 2027 to receive upcoming installments.
Farmers must visit the nearest Raitha Samparka Kendra (RSK) with RTC/Pahani copy.
Portal: https://pmkisan.gov.in`
  },
  {
    id: 'soil-advisory',
    titleEn: 'Kharif Soil Health Advisory (No Deadline)',
    titleKn: 'ಮುಂಗಾರು ಮಣ್ಣು ಪರೀಕ್ಷೆ ಮಾಹಿತಿ (ಗಡುವಿಲ್ಲ)',
    titleHi: 'खरीफ मृदा स्वास्थ्य परामर्श (समयसीमा नहीं)',
    text: `GOVERNMENT OF KARNATAKA - RAITHA SEVA
General Advisory: Farmers are encouraged to test soil health at local Krishi Vigyan Kendras before sowing. Organic fertilizer subsidies are available through local panchayat offices. No mandatory cutoff date applies for testing.`
  }
];

export const NoticeScanner = () => {
  const { language, t } = useLanguage();

  const [inputMode, setInputMode] = useState('upload'); // 'upload' | 'text'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [completedSteps, setCompletedSteps] = useState({});
  const [isSpeaking, setIsSpeaking] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Helper for trilingual rendering
  const renderTrilingual = (primaryText, fallbackEn) => {
    if (language === 'en') {
      return <span>{primaryText || fallbackEn}</span>;
    }
    return (
      <div className="flex flex-col">
        <span className="text-base font-medium">{primaryText}</span>
        {fallbackEn && fallbackEn !== primaryText && (
          <span className="text-xs text-slate-500 font-normal">{fallbackEn}</span>
        )}
      </div>
    );
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setSelectedFile(file);
    setErrorMsg(null);
    setScanResult(null);

    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMsg(null);
      setScanResult(null);
      if (file.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(file));
      } else {
        setPreviewUrl(null);
      }
    }
  };

  const handleSelectSample = (sample) => {
    setInputMode('text');
    setTextInput(sample.text);
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMsg(null);
    setScanResult(null);
  };

  const handleScanSubmit = async (e) => {
    e?.preventDefault();
    setErrorMsg(null);

    if (inputMode === 'upload' && !selectedFile) {
      setErrorMsg('Please select a file or take a photo first.');
      return;
    }
    if (inputMode === 'text' && !textInput.trim()) {
      setErrorMsg('Please paste notice text or select a sample notice.');
      return;
    }

    setIsScanning(true);
    try {
      const formData = new FormData();
      if (inputMode === 'upload' && selectedFile) {
        formData.append('file', selectedFile);
      } else if (inputMode === 'text' && textInput) {
        formData.append('text', textInput);
      }
      formData.append('language', language);

      const result = await scanNotice(formData);
      setScanResult(result);
      setCompletedSteps({});
    } catch (err) {
      console.error('Scan notice error:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to scan document. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const toggleStep = (index) => {
    setCompletedSteps((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const toggleSpeech = () => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-Speech is not supported in this browser.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    if (!scanResult) return;

    const speechText = `${scanResult.issuing_authority}. ${scanResult.summary}. Deadline: ${scanResult.deadline}. Next steps: ${scanResult.next_steps.join('. ')}`;
    const voices = window.speechSynthesis.getVoices() || [];
    const utterance = prepareIndianUtterance(speechText, language, voices);

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  const getUrgencyBadge = (urgency) => {
    switch (urgency?.toLowerCase()) {
      case 'high':
        return {
          bg: 'bg-red-50 border-red-200 text-red-800',
          badge: 'bg-red-600 text-white',
          label: language === 'kn' ? 'ಅತ್ಯಂತ ತುರ್ತು (High Priority)' : language === 'hi' ? 'अत्यंत आवश्यक (High)' : 'High Priority',
          icon: ShieldAlert,
        };
      case 'medium':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-800',
          badge: 'bg-amber-600 text-white',
          label: language === 'kn' ? 'ಮಧ್ಯಮ ತುರ್ತು (Medium)' : language === 'hi' ? 'मध्यम (Medium)' : 'Medium Priority',
          icon: AlertTriangle,
        };
      case 'low':
        return {
          bg: 'bg-blue-50 border-blue-200 text-blue-800',
          badge: 'bg-blue-600 text-white',
          label: language === 'kn' ? 'ಕಡಿಮೆ ತುರ್ತು (Low)' : language === 'hi' ? 'सामान्य (Low)' : 'Low Priority',
          icon: Info,
        };
      default:
        return {
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
          badge: 'bg-emerald-600 text-white',
          label: language === 'kn' ? 'ಮಾಹಿತಿ ಮಾತ್ರ (Informational)' : language === 'hi' ? 'सूचनात्मक (Info)' : 'Informational',
          icon: CheckCircle2,
        };
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-700">
              <FileText className="w-6 h-6" />
            </span>
            {t.noticeScannerTitle}
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            {t.noticeScannerSubtitle}
          </p>
        </div>
      </div>

      {/* Input Mode Selector */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setInputMode('upload')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            inputMode === 'upload'
              ? 'bg-saathi-primary text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Upload className="w-4 h-4" />
          {t.uploadNotice}
        </button>
        <button
          onClick={() => setInputMode('text')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
            inputMode === 'text'
              ? 'bg-saathi-primary text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          {t.pasteNoticeText}
        </button>
      </div>

      {/* Quick Test Samples Bar */}
      <div className="bg-emerald-50/70 border border-emerald-100 rounded-xl p-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-emerald-900 mb-2">
          <Sparkles className="w-4 h-4 text-emerald-600" />
          {t.sampleNotices}:
        </div>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_NOTICES.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelectSample(s)}
              className="text-xs bg-white hover:bg-emerald-100 text-slate-700 hover:text-emerald-900 font-medium px-3 py-1.5 rounded-lg border border-emerald-200 shadow-2xs transition-all text-left"
            >
              {language === 'kn' ? s.titleKn : language === 'hi' ? s.titleHi : s.titleEn}
            </button>
          ))}
        </div>
      </div>

      {/* Scan Input Area */}
      {inputMode === 'upload' ? (
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="bg-white border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-2xl p-8 text-center transition-all shadow-2xs"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*,application/pdf"
            className="hidden"
          />
          <input
            type="file"
            ref={cameraInputRef}
            onChange={handleFileChange}
            accept="image/*"
            capture="environment"
            className="hidden"
          />

          {selectedFile ? (
            <div className="space-y-4">
              {previewUrl ? (
                <div className="max-w-xs mx-auto rounded-xl overflow-hidden shadow-md border border-slate-200">
                  <img src={previewUrl} alt="Notice Preview" className="w-full h-auto max-h-56 object-cover" />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
                  <FileText className="w-8 h-8" />
                </div>
              )}
              <div>
                <p className="font-semibold text-slate-900 text-base">{selectedFile.name}</p>
                <p className="text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
              <div className="flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setPreviewUrl(null);
                  }}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:text-red-600 font-medium flex items-center gap-1 border border-slate-200 rounded-lg"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Remove
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                <Upload className="w-8 h-8" />
              </div>
              <div>
                <p className="text-base font-semibold text-slate-800">
                  {language === 'kn'
                    ? 'ಚಿತ್ರ ಅಥವಾ PDF ದಾಖಲೆ ಎಳೆದು ಹಾಕಿ ಅಥವಾ ಆಯ್ಕೆ ಮಾಡಿ'
                    : language === 'hi'
                    ? 'दस्तावेज खींचकर लाएं या चुनें'
                    : 'Drag and drop your official notice file or photo'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports PNG, JPG, JPEG, WEBP, or PDF up to 10MB
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-2 shadow-xs transition-all"
                >
                  <Upload className="w-4 h-4" />
                  {t.uploadNotice}
                </button>
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold flex items-center gap-2 shadow-xs transition-all"
                >
                  <Camera className="w-4 h-4" />
                  {t.snapPhoto}
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-2xl p-5 shadow-2xs border border-slate-200 space-y-3">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            {language === 'kn' ? 'ನೋಟಿಸ್ ಪಠ್ಯ ಅಥವಾ SMS ವಿವರ' : language === 'hi' ? 'नोटिस टेक्स्ट या संदेश' : 'Notice Text / Circular Details'}
          </label>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            rows={6}
            placeholder={
              language === 'kn'
                ? 'ಸರ್ಕಾರಿ ಸುತ್ತೋಲೆ, ಪಡಿತರ SMS ಅಥವಾ ನೋಟಿಸ್ ಪಠ್ಯವನ್ನು ಇಲ್ಲಿ ಅಂಟಿಸಿ...'
                : language === 'hi'
                ? 'सरकारी आदेश या संदेश यहां पेस्ट करें...'
                : 'Paste official notice text, circular, or government SMS here...'
            }
            className="w-full text-sm p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none text-slate-800 leading-relaxed font-mono"
          />
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Action Scan Button */}
      <div className="flex justify-center">
        <button
          onClick={handleScanSubmit}
          disabled={isScanning || (inputMode === 'upload' && !selectedFile) || (inputMode === 'text' && !textInput.trim())}
          className="w-full md:w-auto min-w-[240px] px-6 py-3.5 rounded-2xl bg-saathi-primary hover:bg-emerald-800 disabled:opacity-50 text-white font-bold text-base shadow-md flex items-center justify-center gap-2 transition-all cursor-pointer"
        >
          {isScanning ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>{t.scanningNotice}</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>{t.scanNoticeBtn}</span>
            </>
          )}
        </button>
      </div>

      {/* Structured Scan Results Breakdown */}
      {scanResult && (
        <div className="bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden animate-fadeIn space-y-0">
          {/* Top Urgency Header */}
          {(() => {
            const urgencyMeta = getUrgencyBadge(scanResult.urgency);
            const UrgencyIcon = urgencyMeta.icon;
            return (
              <div className={`p-5 border-b flex flex-wrap items-center justify-between gap-3 ${urgencyMeta.bg}`}>
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${urgencyMeta.badge}`}>
                    <UrgencyIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      {t.urgencyLevel}
                    </span>
                    <h3 className="text-lg font-bold text-slate-900">{urgencyMeta.label}</h3>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={toggleSpeech}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold shadow-2xs transition-all"
                  >
                    {isSpeaking ? (
                      <>
                        <VolumeX className="w-4 h-4 text-red-600" />
                        <span>Stop Audio</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-4 h-4 text-emerald-700" />
                        <span>{t.audioListenNotice}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })()}

          <div className="p-6 space-y-6">
            {/* Deadline Callout Box */}
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 ${
                scanResult.deadline?.includes('No deadline mentioned')
                  ? 'bg-slate-50 border-slate-200 text-slate-700'
                  : 'bg-red-50/80 border-red-200 text-red-900'
              }`}
            >
              <Clock
                className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                  scanResult.deadline?.includes('No deadline mentioned')
                    ? 'text-slate-500'
                    : 'text-red-600 animate-pulse'
                }`}
              />
              <div>
                <span className="text-xs font-bold uppercase tracking-wider block">
                  {t.deadlineTitle}
                </span>
                <span className="text-base font-bold">
                  {scanResult.deadline}
                </span>
              </div>
            </div>

            {/* Issuing Authority & Purpose */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1 mb-1">
                  <Building className="w-3.5 h-3.5" />
                  {language === 'kn' ? 'ಜಾರಿಗೊಳಿಸಿದ ಇಲಾಖೆ' : language === 'hi' ? 'जारीकर्ता विभाग' : 'Issuing Authority'}
                </span>
                <p className="font-semibold text-slate-900 text-sm">
                  {scanResult.issuing_authority}
                </p>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1 mb-1">
                  <Info className="w-3.5 h-3.5" />
                  {language === 'kn' ? 'ಅಧಿಸೂಚನೆಯ ಉದ್ದೇಶ' : language === 'hi' ? 'नोटिस का उद्देश्य' : 'Notice Purpose'}
                </span>
                <p className="font-semibold text-slate-900 text-sm">
                  {scanResult.purpose}
                </p>
              </div>
            </div>

            {/* Plain-Language 6th Grade Summary */}
            <div className="space-y-2">
              <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                {language === 'kn' ? 'ಸರಳ ಸಾರಾಂಶ (Plain-Language Explanation)' : language === 'hi' ? 'सरल सारांश' : 'Plain-Language Summary'}
              </h4>
              <p className="text-base text-slate-700 leading-relaxed bg-emerald-50/40 p-4 rounded-xl border border-emerald-100/60 font-sans">
                {scanResult.summary}
              </p>
            </div>

            {/* What is demanded / Citizen obligations */}
            {scanResult.citizen_obligations?.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  {t.citizenObligations}
                </h4>
                <ul className="space-y-2">
                  {scanResult.citizen_obligations.map((ob, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-700">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
                      <span>{ob}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Ordered Action Steps Checklist */}
            {scanResult.next_steps?.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                  <ListOrdered className="w-4 h-4 text-emerald-700" />
                  {t.nextSteps}
                </h4>
                <div className="space-y-2">
                  {scanResult.next_steps.map((step, idx) => {
                    const isDone = completedSteps[idx];
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleStep(idx)}
                        className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start gap-3 ${
                          isDone
                            ? 'bg-slate-50 border-slate-200 text-slate-400 line-through'
                            : 'bg-white hover:bg-emerald-50/50 border-slate-200 text-slate-800'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={!!isDone}
                          onChange={() => {}}
                          className="mt-1 w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                        />
                        <span className="text-sm font-medium leading-relaxed">{step}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Official Portal Link */}
            {scanResult.official_portal && (
              <div className="pt-2">
                <a
                  href={scanResult.official_portal}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition-all shadow-xs"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>
                    {language === 'kn' ? 'ಅಧಿಕೃತ ಪೋರ್ಟಲ್‌ಗೆ ಭೇಟಿ ನೀಡಿ' : language === 'hi' ? 'आधिकारिक पोर्टल खोलें' : 'Visit Official Portal'}
                  </span>
                </a>
              </div>
            )}

            {/* Mandatory Legal Disclaimer */}
            <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-900 leading-normal flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
              <span>{scanResult.disclaimer}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

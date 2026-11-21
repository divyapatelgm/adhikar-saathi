import React from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { Scale, Phone, ExternalLink, ArrowRight } from 'lucide-react';

export const RightsDirectory = ({ onSelectQuestion }) => {
  const { language } = useLanguage();

  const content = {
    kn: {
      bannerTitle: "ನಾಗರಿಕ ಶಾಸನಬದ್ಧ ಹಕ್ಕುಗಳ ರಕ್ಷಣೆ (Citizen Statutory Rights)",
      bannerSub: "ಭಾರತದ ಕಾನೂನಿನಡಿಯಲ್ಲಿ ಪ್ರತಿಯೊಬ್ಬ ನಾಗರಿಕನಿಗೆ ಸೌಲಭ್ಯಗಳನ್ನು ಸಕಾಲದಲ್ಲಿ ಪಡೆಯುವ ಸಾಂವಿಧಾನಿಕ ಹಕ್ಕಿದೆ.",
      portalBtn: "ಪೋರ್ಟಲ್",
      askBtn: "ಪ್ರಶ್ನಿಸಿ",
      items: [
        {
          id: 'unpaid-wages-mgnrega',
          topic: 'ನರೇಗಾ ಕೂಲಿ ವೇತನ ವಿಳಂಬ / ಬಾಕಿ (Unpaid MGNREGA Wages)',
          summary: 'ಕೆಲಸ ಮುಗಿದ 15 ದಿನಗಳಲ್ಲಿ ವೇತನ ಪಾವತಿಯಾಗದಿದ್ದರೆ, ದಿನಕ್ಕೆ 0.05% ವಿಳಂಬ ಪರಿಹಾರ ಪಡೆಯಲು ಕಾರ್ಮಿಕರಿಗೆ ಹಕ್ಕಿದೆ.',
          helpline: '1800-425-8666 / ಜಿಲ್ಲಾ ಲೋಕಪಾಲ್',
          portal: 'https://nrega.nic.in',
          sampleQ: 'ನರೇಗಾ ಕೂಲಿ ವೇತನ ಬಂದಿಲ್ಲ ಏನು ಮಾಡಬೇಕು?',
        },
        {
          id: 'right-to-information-karnataka',
          topic: 'ಮಾಹಿತಿ ಹಕ್ಕು ಕಾಯ್ದೆ (Right to Information - RTI)',
          summary: 'ಯಾವುದೇ ಸರ್ಕಾರಿ ಕಚೇರಿಯಿಂದ ದಾಖಲೆಗಳನ್ನು ಪಡೆಯಲು ಕೇವಲ ₹10 ಶುಲ್ಕ (ಬಿಪಿಎಲ್ ಕಾರ್ಡ್‌ದಾರರಿಗೆ ಉಚಿತ). 30 ದಿನಗಳಲ್ಲಿ ಮಾಹಿತಿ ನೀಡಬೇಕು.',
          helpline: '080-22370909 / ಕರ್ನಾಟಕ ಮಾಹಿತಿ ಆಯೋಗ',
          portal: 'https://rtionline.karnataka.gov.in',
          sampleQ: 'ಮಾಹಿತಿ ಹಕ್ಕು ಅರ್ಜಿ ಹಾಕುವುದು ಹೇಗೆ?',
        },
        {
          id: 'consumer-grievance-ration-pds',
          topic: 'ಪಡಿತರ ಚೀಟಿ / ನ್ಯಾಯಬೆಲೆ ಅಂಗಡಿ ಸಮಸ್ಯೆ (PDS Ration Denial)',
          summary: 'ಬಯೋಮೆಟ್ರಿಕ್ ಹೆಬ್ಬೆರಳು ಬಾರದಿದ್ದರೂ ಪಡಿತರ ನಿರಾಕರಿಸುವಂತಿಲ್ಲ. ನಿಗದಿತ ತೂಕ ಮತ್ತು ಬೆಲೆಯಲ್ಲಿ ಆಹಾರ ಧಾನ್ಯ ಪಡೆಯಲು ಅರ್ಹರು.',
          helpline: '1967 ಅಥವಾ 1800-425-9333',
          portal: 'https://ahara.kar.nic.in',
          sampleQ: 'ರೇಷನ್ ಅಂಗಡಿ ಮಾಲೀಕ ಅಕ್ಕಿ ಕೊಡುತ್ತಿಲ್ಲ ದೂರು ನೀಡುವುದು ಹೇಗೆ?',
        },
      ],
    },
    hi: {
      bannerTitle: "नागरिक वैधानिक अधिकार संरक्षण (Citizen Statutory Rights)",
      bannerSub: "भारतीय कानून के तहत प्रत्येक नागरिक को समयबद्ध कल्याणकारी लाभ और पारदर्शी समाधान पाने का संवैधानिक अधिकार है।",
      portalBtn: "पोर्टल",
      askBtn: "पूछें",
      items: [
        {
          id: 'unpaid-wages-mgnrega',
          topic: 'मनरेगा मजदूरी में देरी / विलंब मुआवजा (Unpaid MGNREGA Wages)',
          summary: 'काम पूरा होने के 15 दिनों के भीतर मजदूरी नहीं मिलने पर श्रमिकों को प्रतिदिन 0.05% की दर से विलंब मुआवजा पाने का कानूनी अधिकार है।',
          helpline: 'हेल्पलाइन: 1800-425-8666 / जिला लोकपाल',
          portal: 'https://nrega.nic.in',
          sampleQ: 'नरेगा की मजदूरी नहीं मिली क्या करें?',
        },
        {
          id: 'right-to-information-karnataka',
          topic: 'सूचना का अधिकार (Right to Information - RTI)',
          summary: 'सरकारी रिकॉर्ड देखने या अस्वीकृति का कारण जानने हेतु केवल ₹10 शुल्क (बीपीएल हेतु निःशुल्क)। 30 दिनों में उत्तर अनिवार्य है।',
          helpline: 'कर्नाटक सूचना आयोग: 080-22370909',
          portal: 'https://rtionline.karnataka.gov.in',
          sampleQ: 'कर्नाटक में आरटीआई आवेदन कैसे करें?',
        },
        {
          id: 'consumer-grievance-ration-pds',
          topic: 'राशन न मिलना / उचित मूल्य दुकान शिकायत (PDS Ration Denial)',
          summary: 'बायोमेट्रिक फिंगरप्रिंट न आने पर भी डीलर राशन देने से मना नहीं कर सकता। निर्धारित मात्रा व दर पर राशन पाने का अधिकार है।',
          helpline: 'खाद्य उपभोक्ता हेल्पलाइन: 1967 / 1800-425-9333',
          portal: 'https://ahara.kar.nic.in',
          sampleQ: 'राशन डीलर राशन नहीं दे रहा क्या करें?',
        },
      ],
    },
    en: {
      bannerTitle: "Citizen Statutory Rights Protection",
      bannerSub: "Under Indian and Karnataka law, every citizen has constitutional rights to receive timely welfare benefits and transparent administrative redressal.",
      portalBtn: "Official Portal",
      askBtn: "Ask in Chat",
      items: [
        {
          id: 'unpaid-wages-mgnrega',
          topic: 'Unpaid MGNREGA Wages & Delay Compensation',
          summary: 'If wage payment is delayed beyond 15 days of work completion, workers have a statutory right to receive delay compensation of 0.05% per day until full settlement.',
          helpline: 'Helpline: 1800-425-8666 / District Ombudsman',
          portal: 'https://nrega.nic.in',
          sampleQ: 'My MGNREGA wages are delayed, what should I do?',
        },
        {
          id: 'right-to-information-karnataka',
          topic: 'Right to Information (RTI Act, 2005)',
          summary: 'Every citizen has the legal right to inspect public records or seek reasons for application rejection for a ₹10 fee (free for BPL). Officers must respond within 30 days.',
          helpline: 'Karnataka Information Commission: 080-22370909',
          portal: 'https://rtionline.karnataka.gov.in',
          sampleQ: 'How do I file an RTI application in Karnataka?',
        },
        {
          id: 'consumer-grievance-ration-pds',
          topic: 'PDS Ration Denial & Fair Price Shop Grievances',
          summary: 'FPS dealers cannot deny entitled foodgrains due to biometric fingerprint failure. Provisions exist for OTP authentication or nominee collection at government subsidized rates.',
          helpline: 'Food & Civil Supplies Consumer Helpline: 1967 / 1800-425-9333',
          portal: 'https://ahara.kar.nic.in',
          sampleQ: 'Fair price shop dealer is not giving ration',
        },
      ],
    },
  };

  const current = content[language] || content.en;

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="bg-amber-50/70 p-4 rounded-2xl border border-amber-200/80 mb-4 shadow-sm">
        <h2 className="text-base font-bold text-amber-900 flex items-center gap-2">
          <Scale className="w-5 h-5 text-amber-700" />
          <span>{current.bannerTitle}</span>
        </h2>
        <p className="text-xs text-amber-800 mt-1 leading-relaxed">
          {current.bannerSub}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {current.items.map((item) => (
          <div
            key={item.id}
            className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow"
          >
            <div>
              <h3 className="font-bold text-sm text-slate-900 leading-snug mb-2">
                {item.topic}
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed mb-4">
                {item.summary}
              </p>

              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-xs font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <Phone className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span className="truncate">{item.helpline}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <a
                href={item.portal}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-bold text-saathi-primary hover:underline flex items-center gap-1"
              >
                <span>{current.portalBtn}</span>
                <ExternalLink className="w-3 h-3" />
              </a>

              <button
                onClick={() => onSelectQuestion(item.sampleQ)}
                className="px-3 py-1.5 bg-saathi-primary text-white rounded-lg text-xs font-bold flex items-center gap-1 hover:bg-emerald-700 transition-colors shadow-sm"
              >
                <span>{current.askBtn}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

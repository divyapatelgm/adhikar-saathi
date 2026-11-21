import React, { useState } from 'react';
import {
  CheckCircle,
  HelpCircle,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Building,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { useLanguage } from '../hooks/useLanguage';

export const SchemeCard = ({ evaluation, schemeData }) => {
  const { language, t } = useLanguage();
  const [expanded, setExpanded] = useState(false);
  const [checkedDocs, setCheckedDocs] = useState({});

  const verdict = evaluation ? evaluation.verdict : 'Maybe';
  const reason = evaluation ? evaluation.reason_en : '';
  const scheme = schemeData || {};

  const name =
    (scheme.names && (scheme.names[language] || scheme.names.en)) ||
    (evaluation && evaluation.scheme_name) ||
    'Welfare Scheme';

  const toggleDoc = (doc) => {
    setCheckedDocs((prev) => ({ ...prev, [doc]: !prev[doc] }));
  };

  const getVerdictBadge = () => {
    switch (verdict) {
      case 'Eligible':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded-full text-xs font-bold shadow-sm">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            {t.verdictEligible}
          </span>
        );
      case 'Likely':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-cyan-100 text-cyan-800 border border-cyan-300 rounded-full text-xs font-bold shadow-sm">
            <Sparkles className="w-4 h-4 text-cyan-600" />
            {t.verdictLikely} (Tier 2)
          </span>
        );
      case 'Maybe':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-900 border border-amber-300 rounded-full text-xs font-bold shadow-sm">
            <HelpCircle className="w-4 h-4 text-amber-700" />
            {t.verdictMaybe}
          </span>
        );
      case 'Not eligible':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-100 text-rose-800 border border-rose-300 rounded-full text-xs font-bold shadow-sm">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            {t.verdictNotEligible}
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden p-5">
      {/* Header: Title and Verdict */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            {getVerdictBadge()}
            {scheme.tier === 'extracted' && (
              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[11px] font-medium border border-slate-200">
                Auto-extracted
              </span>
            )}
            {scheme.level && (
              <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px] font-medium uppercase">
                {scheme.level}
              </span>
            )}
          </div>
          <h2 className="text-lg font-bold text-slate-900 leading-snug">
            {name}
          </h2>
          {scheme.department && (
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
              <Building className="w-3.5 h-3.5" />
              {scheme.department}
            </p>
          )}
        </div>
      </div>

      {/* Evaluation Reason */}
      {reason && (
        <div
          className={`mt-3 p-3 rounded-xl text-xs font-medium border ${
            verdict === 'Eligible'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-100'
              : verdict === 'Likely'
              ? 'bg-cyan-50 text-cyan-900 border-cyan-100'
              : verdict === 'Maybe'
              ? 'bg-amber-50 text-amber-900 border-amber-100'
              : 'bg-rose-50 text-rose-900 border-rose-100'
          }`}
        >
          {reason}
        </div>
      )}

      {/* Missing Question for Maybe */}
      {verdict === 'Maybe' && evaluation && evaluation.missing_question && (
        <div className="mt-2 text-xs font-semibold text-amber-800 bg-amber-100/60 p-2.5 rounded-lg border border-amber-200 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 flex-shrink-0 text-amber-700" />
          <span>ಪ್ರಶ್ನೆ / Query: {evaluation.missing_question}</span>
        </div>
      )}

      {/* Benefit Highlight */}
      {scheme.benefit && (
        <div className="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              ಪ್ರಯೋಜನ / Key Benefit
            </span>
            <p className="text-sm font-semibold text-slate-800">
              {scheme.benefit.description}
            </p>
          </div>
          {scheme.benefit.amount_text && (
            <div className="text-right pl-3">
              <span className="text-base font-extrabold text-saathi-primary">
                {scheme.benefit.amount_text}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Expand/Collapse Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full mt-4 py-2 flex items-center justify-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
      >
        <span>{expanded ? t.hideDetails : t.viewDetails}</span>
        {expanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {/* Detailed Section */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-200 space-y-4 text-xs">
          {/* Documents Checklist */}
          {scheme.documents_required && scheme.documents_required.length > 0 && (
            <div>
              <h3 className="font-bold text-slate-800 flex items-center gap-1.5 mb-2 text-sm">
                <FileText className="w-4 h-4 text-emerald-600" />
                {t.documentsNeeded} ({scheme.documents_required.length})
              </h3>
              <div className="space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
                {scheme.documents_required.map((doc, idx) => (
                  <label
                    key={idx}
                    className="flex items-start gap-2.5 cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={!!checkedDocs[doc]}
                      onChange={() => toggleDoc(doc)}
                      className="mt-0.5 rounded text-saathi-primary focus:ring-saathi-primary"
                    />
                    <span
                      className={`${
                        checkedDocs[doc]
                          ? 'line-through text-slate-400 font-normal'
                          : 'text-slate-700 font-medium'
                      }`}
                    >
                      {doc}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* How to Apply */}
          {scheme.how_to_apply && scheme.how_to_apply.steps && (
            <div>
              <h3 className="font-bold text-slate-800 mb-1 text-sm">
                {t.howToApply} ({scheme.how_to_apply.mode || 'both'})
              </h3>
              <ol className="list-decimal list-inside space-y-1 text-slate-700 font-medium bg-slate-50 p-3 rounded-xl border border-slate-200">
                {scheme.how_to_apply.steps.map((step, idx) => (
                  <li key={idx} className="leading-relaxed">
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Source Attribution & Link */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-slate-500 border-t border-slate-100 text-[11px]">
            <div>
              <span>{t.source}: </span>
              <span className="font-semibold text-slate-700">
                {scheme.source_name || (evaluation && evaluation.source_name)}
              </span>
              {scheme.last_verified && (
                <span className="ml-2 inline-flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {scheme.last_verified}
                </span>
              )}
            </div>

            {(scheme.official_url ||
              (evaluation && evaluation.official_url)) && (
              <a
                href={scheme.official_url || evaluation.official_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-saathi-primary hover:text-saathi-dark font-bold underline"
              >
                <span>{t.officialPortal}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

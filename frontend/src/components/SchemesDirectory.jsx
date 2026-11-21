import React, { useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { SchemeCard } from './SchemeCard';
import { Search, Filter } from 'lucide-react';

export const SchemesDirectory = ({ schemes }) => {
  const { language, t } = useLanguage();
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', label: t.allCategories },
    { id: 'agriculture', label: 'ಕೃಷಿ (Agriculture)' },
    { id: 'education', label: 'ಶಿಕ್ಷಣ (Education)' },
    { id: 'women', label: 'ಮಹಿಳೆಯರು (Women)' },
    { id: 'senior_citizen', label: 'ಹಿರಿಯ ನಾಗರಿಕರು (Elderly)' },
    { id: 'disability', label: 'ವಿಕಲಚೇತನರು (Disability)' },
  ];

  const filtered = (schemes || []).filter((s) => {
    const nameMatch =
      (s.names &&
        ((s.names[language] && s.names[language].toLowerCase().includes(search.toLowerCase())) ||
          (s.names.en && s.names.en.toLowerCase().includes(search.toLowerCase())))) ||
      s.id.toLowerCase().includes(search.toLowerCase());

    const catMatch =
      selectedCategory === 'all' || (s.category && s.category.includes(selectedCategory));

    return nameMatch && catMatch;
  });

  return (
    <div className="space-y-5">
      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.searchPlaceholder}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-50 rounded-xl border border-slate-200 text-sm focus:border-saathi-primary font-medium"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-semibold py-1">
          <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl border transition-colors flex-shrink-0 ${
                selectedCategory === cat.id
                  ? 'bg-saathi-primary text-white border-saathi-primary'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Scheme Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((scheme) => (
          <SchemeCard
            key={scheme.id}
            evaluation={{
              verdict: scheme.tier === 'verified' ? 'Eligible' : 'Likely',
              reason_en: scheme.summary_en,
              scheme_name: scheme.names ? (scheme.names[language] || scheme.names.en) : scheme.id,
              official_url: scheme.official_url,
              source_name: scheme.source_name,
            }}
            schemeData={scheme}
          />
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full p-12 text-center text-slate-500 bg-white rounded-2xl border border-dashed border-slate-200">
            ಯಾವುದೇ ಯೋಜನೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ (No matching schemes found).
          </div>
        )}
      </div>
    </div>
  );
};

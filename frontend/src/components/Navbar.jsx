import React, { useState, useEffect } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { ShieldCheck, Database, Globe, User, LogIn, LogOut } from 'lucide-react';
import { AuthModal } from './AuthModal';

export const Navbar = ({ stats }) => {
  const { language, setLanguage, t } = useLanguage();
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [citizenUser, setCitizenUser] = useState(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('adhikar_citizen_user');
    if (stored) {
      try {
        setCitizenUser(JSON.parse(stored));
      } catch (e) {}
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('adhikar_citizen_user');
    localStorage.removeItem('adhikar_citizen_token');
    setCitizenUser(null);
    setShowProfileMenu(false);
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-saathi-primary flex items-center justify-center text-white shadow-md">
            <span className="font-bold text-2xl tracking-tighter">ಅ</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 leading-tight">
              {t.appTitle}
            </h1>
            <p className="text-xs text-slate-500 font-medium hidden sm:block">
              {t.appSubtitle}
            </p>
          </div>
        </div>

        {/* Live Scheme Stats Bar */}
        <div className="hidden md:flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-full text-xs font-semibold text-slate-700">
          <div className="flex items-center gap-1.5 text-emerald-800">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>
              {stats ? stats.verified_schemes_count : '...'} {t.statsVerified}
            </span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1.5 text-amber-800">
            <Database className="w-3.5 h-3.5 text-amber-600" />
            <span>
              {stats ? stats.extracted_schemes_count : '...'} {t.statsExtracted}
            </span>
          </div>
        </div>

        {/* Right Section: Language Switcher & Citizen Auth */}
        <div className="flex items-center gap-2">
          {/* Language Switcher */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
            <Globe className="w-4 h-4 text-slate-500 ml-1 mr-1" />
            <button
              onClick={() => setLanguage('kn')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                language === 'kn'
                  ? 'bg-saathi-primary text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-label="Switch to Kannada"
            >
              ಕನ್ನಡ
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                language === 'hi'
                  ? 'bg-saathi-primary text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-label="Switch to Hindi"
            >
              हिंदी
            </button>
            <button
              onClick={() => setLanguage('en')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                language === 'en'
                  ? 'bg-saathi-primary text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              aria-label="Switch to English"
            >
              EN
            </button>
          </div>

          {/* Citizen Account Button */}
          {citizenUser ? (
            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold hover:bg-emerald-100 transition-colors shadow-sm"
              >
                <div className="w-5 h-5 rounded-full bg-saathi-primary text-white flex items-center justify-center text-[10px]">
                  {citizenUser.name ? citizenUser.name[0].toUpperCase() : 'U'}
                </div>
                <span className="max-w-[100px] truncate">{citizenUser.name}</span>
              </button>

              {/* Profile Dropdown */}
              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-200 p-3 z-50 animate-fade-in">
                  <div className="pb-2 border-b border-slate-100">
                    <p className="text-xs font-bold text-slate-800 truncate">{citizenUser.name}</p>
                    <p className="text-[11px] text-slate-500 font-mono">{citizenUser.contact}</p>
                    {citizenUser.dob && (
                      <p className="text-[11px] text-slate-400 mt-0.5">DOB: {citizenUser.dob}</p>
                    )}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full mt-2 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold text-red-600 hover:bg-red-50 transition-colors text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{t.logout}</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => setIsAuthOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-saathi-primary text-white text-xs font-bold hover:bg-emerald-700 transition-all shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>{t.signIn} / {t.register}</span>
            </button>
          )}
        </div>
      </div>

      {/* Auth Modal for Citizens */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLoginSuccess={(user) => setCitizenUser(user)}
      />
    </header>
  );
};

import React, { useState, useEffect } from 'react';
import { LanguageProvider, useLanguage } from './hooks/useLanguage';
import { AuthScreen } from './components/AuthScreen';
import { SettingsView } from './components/SettingsView';
import { ChatWindow } from './components/ChatWindow';
import { EligibilityWizard } from './components/EligibilityWizard';
import { NoticeScanner } from './components/NoticeScanner';
import { RightsDirectory } from './components/RightsDirectory';
import { SchemesDirectory } from './components/SchemesDirectory';
import { getStats, getSchemes } from './services/api';
import {
  MessageSquare,
  CheckCircle,
  FileSearch,
  Scale,
  BookOpen,
  Settings,
  ShieldCheck,
  Database,
  Globe,
  LogOut,
  User,
  Menu,
  X
} from 'lucide-react';

const MainApp = () => {
  const { language, setLanguage, t } = useLanguage();

  // Citizen Authentication State
  const [citizenUser, setCitizenUser] = useState(() => {
    try {
      const stored = localStorage.getItem('adhikar_citizen_user');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'eligibility' | 'rights' | 'directory' | 'settings'
  const [stats, setStats] = useState(null);
  const [schemes, setSchemes] = useState([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (citizenUser) {
      loadInitialData();
    }
  }, [citizenUser]);

  const loadInitialData = async () => {
    try {
      const statsData = await getStats();
      setStats(statsData);

      const schemesData = await getSchemes();
      setSchemes(schemesData);
    } catch (e) {
      console.warn('Could not load initial API stats:', e);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adhikar_citizen_user');
    localStorage.removeItem('adhikar_citizen_token');
    setCitizenUser(null);
    setActiveTab('chat');
  };

  const handleSelectRightsQuestion = (questionText) => {
    setActiveTab('chat');
  };

  // 1. GATE: If citizen is not logged in, show Full-Screen Login / Register Screen!
  if (!citizenUser) {
    return <AuthScreen onLoginSuccess={(u) => setCitizenUser(u)} />;
  }

  const navItems = [
    { id: 'chat', label: t.tabChat, icon: MessageSquare },
    { id: 'eligibility', label: t.tabEligibility, icon: CheckCircle },
    { id: 'notice', label: t.tabNoticeScanner, icon: FileSearch },
    { id: 'rights', label: t.tabRights, icon: Scale },
    { id: 'directory', label: t.tabDirectory, icon: BookOpen },
    { id: 'settings', label: t.tabSettings, icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col md:flex-row text-slate-800">
      {/* ============================================================
          SIDEBAR: Visible on Medium, Large, and Extra-Large Screens
          ============================================================ */}
      <aside className="hidden md:flex flex-col w-72 bg-white border-r border-slate-200 flex-shrink-0 min-h-screen sticky top-0 shadow-sm z-30">
        {/* Brand */}
        <div className="p-5 border-b border-slate-100 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-saathi-primary text-white flex items-center justify-center font-bold text-2xl shadow-md">
            ಅ
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 leading-tight">{t.appTitle}</h1>
            <p className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">
              Citizen Portal
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl font-bold text-xs transition-all text-left ${
                  isActive
                    ? 'bg-saathi-primary text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Language Quick Pill */}
        <div className="px-4 py-2 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-semibold flex items-center gap-1">
            <Globe className="w-3.5 h-3.5" /> Language:
          </span>
          <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg">
            <button
              onClick={() => setLanguage('kn')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                language === 'kn' ? 'bg-saathi-primary text-white shadow-xs' : 'text-slate-600'
              }`}
            >
              ಕನ್ನಡ
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                language === 'hi' ? 'bg-saathi-primary text-white shadow-xs' : 'text-slate-600'
              }`}
            >
              हिंदी
            </button>
            <button
              onClick={() => setLanguage('en')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                language === 'en' ? 'bg-saathi-primary text-white shadow-xs' : 'text-slate-600'
              }`}
            >
              EN
            </button>
          </div>
        </div>

        {/* Citizen Profile Card at Bottom */}
        <div className="p-3.5 m-3 rounded-2xl bg-slate-50 border border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-saathi-primary text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                {citizenUser.name ? citizenUser.name[0].toUpperCase() : 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-slate-800 truncate">{citizenUser.name}</p>
                <p className="text-[10px] text-slate-500 truncate font-mono">{citizenUser.contact}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title={t.logout}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ============================================================
          TOP NAVBAR: Visible on Small & Extra-Small Screens
          ============================================================ */}
      <header className="md:hidden bg-white border-b border-slate-200 p-3.5 sticky top-0 z-40 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-saathi-primary text-white flex items-center justify-center font-bold text-sm">
            ಅ
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 leading-tight">{t.appTitle}</h1>
            <p className="text-[10px] text-slate-500 font-medium">{t.appSubtitle}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveTab('settings')}
            className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg text-red-600 hover:bg-red-50"
            title={t.logout}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ============================================================
          MAIN CONTENT AREA
          ============================================================ */}
      <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-6xl mx-auto w-full pb-20 md:pb-8 overflow-y-auto">
        {activeTab === 'chat' && <ChatWindow />}
        {activeTab === 'eligibility' && <EligibilityWizard allSchemes={schemes} />}
        {activeTab === 'notice' && <NoticeScanner />}
        {activeTab === 'rights' && (
          <RightsDirectory onSelectQuestion={handleSelectRightsQuestion} />
        )}
        {activeTab === 'directory' && <SchemesDirectory schemes={schemes} />}
        {activeTab === 'settings' && (
          <SettingsView user={citizenUser} onLogout={handleLogout} />
        )}
      </main>

      {/* ============================================================
          MOBILE BOTTOM NAVBAR: Visible on Small Screens
          ============================================================ */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-50 flex justify-around py-1.5 shadow-lg">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center gap-0.5 py-1 px-2 text-[10px] font-bold transition-colors ${
                isActive ? 'text-saathi-primary' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label.split(' ')[0]}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default function App() {
  return (
    <LanguageProvider>
      <MainApp />
    </LanguageProvider>
  );
}

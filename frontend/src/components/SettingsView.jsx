import React, { useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { Globe, Lock, User, ShieldCheck, AlertCircle, LogOut } from 'lucide-react';

export const SettingsView = ({ user, onLogout }) => {
  const { language, setLanguage, t } = useLanguage();

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdMsg, setPwdMsg] = useState({ type: '', text: '' });

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwdMsg({ type: '', text: '' });

    if (!currentPassword || !newPassword) {
      setPwdMsg({ type: 'error', text: 'Please fill in both current and new password.' });
      return;
    }

    if (newPassword.length < 4) {
      setPwdMsg({ type: 'error', text: 'New password must be at least 4 characters.' });
      return;
    }

    setPwdLoading(true);
    try {
      const res = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact: user?.contact || '',
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setPwdMsg({ type: 'success', text: 'Password successfully updated!' });
        setCurrentPassword('');
        setNewPassword('');
      } else {
        setPwdMsg({ type: 'error', text: data.detail || 'Failed to update password.' });
      }
    } catch (err) {
      setPwdMsg({ type: 'error', text: 'Network error: ' + err.message });
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12">
      {/* Title */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h2 className="text-xl font-bold text-slate-800">{t.settingsTitle}</h2>
        <p className="text-xs text-slate-500 mt-1">
          Manage your portal language, account credentials, and citizen profile.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 1: Language Preference */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Globe className="w-5 h-5 text-saathi-primary" />
              <h3 className="text-base font-bold text-slate-800">{t.languagePreference}</h3>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Your chosen language will persist across page reloads and browser restarts.
            </p>

            <div className="space-y-2.5">
              {[
                { code: 'kn', label: 'ಕನ್ನಡ (Kannada)', desc: 'ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ಪ್ರಮುಖ ಭಾಷೆ' },
                { code: 'hi', label: 'हिंदी (Hindi)', desc: 'राष्ट्रीय कल्याणकारी योजनाएं' },
                { code: 'en', label: 'English', desc: 'Central & State Government Explanations' },
              ].map((item) => (
                <div
                  key={item.code}
                  onClick={() => setLanguage(item.code)}
                  className={`p-3.5 rounded-xl border-2 cursor-pointer transition-all flex items-center justify-between ${
                    language === item.code
                      ? 'border-saathi-primary bg-emerald-50/60 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div>
                    <div className="font-bold text-sm text-slate-800">{item.label}</div>
                    <div className="text-[11px] text-slate-500">{item.desc}</div>
                  </div>
                  {language === item.code && (
                    <div className="w-6 h-6 rounded-full bg-saathi-primary text-white flex items-center justify-center text-xs font-bold">
                      ✓
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Section 2: Citizen Profile Info */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-saathi-primary" />
            <h3 className="text-base font-bold text-slate-800">{t.profileInfoTitle}</h3>
          </div>

          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3 mb-4">
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                {t.fullName}
              </span>
              <span className="text-sm font-bold text-slate-800">{user?.name || 'Citizen'}</span>
            </div>
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                {t.contact}
              </span>
              <span className="text-sm font-mono text-slate-700">{user?.contact || '—'}</span>
            </div>
            {user?.dob && (
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  {t.dob}
                </span>
                <span className="text-sm text-slate-700">{user?.dob}</span>
              </div>
            )}
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Account Status
              </span>
              <span className="inline-block mt-0.5 px-2.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-xs rounded-full">
                Active Citizen Account
              </span>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="w-full py-2.5 px-4 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>{t.logout}</span>
          </button>
        </div>
      </div>

      {/* Section 3: Change Password */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <Lock className="w-5 h-5 text-saathi-primary" />
          <h3 className="text-base font-bold text-slate-800">{t.changePasswordTitle}</h3>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          Update your secure password stored in PBKDF2 HMAC SHA-256 salted hash form.
        </p>

        {pwdMsg.text && (
          <div
            className={`mb-4 p-3 rounded-xl flex items-center gap-2 text-xs font-semibold ${
              pwdMsg.type === 'success'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {pwdMsg.type === 'success' ? (
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            )}
            <span>{pwdMsg.text}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t.currentPassword}
            </label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              {t.newPassword}
            </label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="New password..."
              className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
            />
          </div>

          <div className="md:col-span-2 flex justify-end">
            <button
              type="submit"
              disabled={pwdLoading}
              className="px-6 py-2.5 bg-saathi-primary hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
            >
              {pwdLoading ? 'Updating...' : t.updatePasswordBtn}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { User, Phone, Calendar, Lock, ShieldCheck, AlertCircle, Sparkles, Globe, ArrowRight } from 'lucide-react';

export const AuthScreen = ({ onLoginSuccess }) => {
  const { language, setLanguage, t } = useLanguage();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form fields
  const [name, setName] = useState('');
  const [contact, setContact] = useState('');
  const [dob, setDob] = useState('');
  const [password, setPassword] = useState('');

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!name.trim() || !contact.trim() || !dob.trim() || !password) {
      setError('Please fill in all registration fields.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          contact: contact.trim(),
          dob: dob.trim(),
          password: password,
        }),
      });

      let data;
      try {
        const text = await res.text();
        data = text ? JSON.parse(text) : {};
      } catch (parseErr) {
        throw new Error('Could not connect to backend server. Please ensure FastAPI is running on port 8000.');
      }

      if (res.ok && data.status === 'success') {
        localStorage.setItem('adhikar_citizen_user', JSON.stringify(data.user));
        localStorage.setItem('adhikar_citizen_token', data.token);
        setSuccessMsg('Account registered successfully! Entering portal...');
        setTimeout(() => {
          onLoginSuccess(data.user);
        }, 500);
      } else {
        setError(data.detail || 'Registration failed. Please try again.');
      }
    } catch (err) {
      setError(err.message.includes('connect to backend') ? err.message : 'Connection error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!contact.trim() || !password) {
      setError('Please enter both contact and password.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact: contact.trim(),
          password: password,
        }),
      });

      let data;
      try {
        const text = await res.text();
        data = text ? JSON.parse(text) : {};
      } catch (parseErr) {
        throw new Error('Could not connect to backend server. Please ensure FastAPI is running on port 8000.');
      }

      if (res.ok && data.status === 'success') {
        localStorage.setItem('adhikar_citizen_user', JSON.stringify(data.user));
        localStorage.setItem('adhikar_citizen_token', data.token);
        setSuccessMsg('Login successful! Entering portal...');
        setTimeout(() => {
          onLoginSuccess(data.user);
        }, 400);
      } else {
        setError(data.detail || 'Invalid contact or password.');
      }
    } catch (err) {
      setError(err.message.includes('connect to backend') ? err.message : 'Connection error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 sm:p-6 lg:p-8 relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-saathi-primary/20 rounded-full blur-3xl pointer-events-none"></div>

      {/* Main Container */}
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200 grid grid-cols-1 lg:grid-cols-12 relative z-10">
        {/* Left Side: Brand & Feature Presentation */}
        <div className="lg:col-span-5 bg-gradient-to-br from-emerald-800 via-saathi-primary to-emerald-950 p-8 sm:p-10 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center font-bold text-2xl shadow-inner">
                ಅ
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">{t.appTitle}</h1>
                <span className="text-[11px] uppercase tracking-wider text-emerald-200 font-semibold">
                  Karnataka Citizen Portal
                </span>
              </div>
            </div>

            <p className="text-sm text-emerald-100 font-medium leading-relaxed mb-8">
              {t.appSubtitle}
            </p>

            {/* Feature Highlights */}
            <div className="space-y-4">
              <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm p-3.5 rounded-2xl border border-white/10">
                <Sparkles className="w-5 h-5 text-emerald-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-white">Multilingual Voice & Chat</h4>
                  <p className="text-[11px] text-emerald-100 mt-0.5">
                    Speak or chat naturally in Kannada, Hindi, or English.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm p-3.5 rounded-2xl border border-white/10">
                <ShieldCheck className="w-5 h-5 text-emerald-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-white">Deterministic Rules Engine</h4>
                  <p className="text-[11px] text-emerald-100 mt-0.5">
                    100% verified eligibility criteria without LLM guesswork.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm p-3.5 rounded-2xl border border-white/10">
                <Lock className="w-5 h-5 text-emerald-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-white">Salted Hash Security</h4>
                  <p className="text-[11px] text-emerald-100 mt-0.5">
                    Credentials are encrypted in PBKDF2 HMAC SHA-256 hash form.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Language Switcher on Login Page */}
          <div className="mt-8 pt-6 border-t border-white/15 relative z-10 flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-200 flex items-center gap-1.5">
              <Globe className="w-4 h-4" /> Language:
            </span>
            <div className="flex items-center gap-1 bg-white/10 p-1 rounded-xl">
              <button
                type="button"
                onClick={() => setLanguage('kn')}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  language === 'kn' ? 'bg-white text-emerald-900 shadow-sm' : 'text-white hover:bg-white/10'
                }`}
              >
                ಕನ್ನಡ
              </button>
              <button
                type="button"
                onClick={() => setLanguage('hi')}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  language === 'hi' ? 'bg-white text-emerald-900 shadow-sm' : 'text-white hover:bg-white/10'
                }`}
              >
                हिंदी
              </button>
              <button
                type="button"
                onClick={() => setLanguage('en')}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  language === 'en' ? 'bg-white text-emerald-900 shadow-sm' : 'text-white hover:bg-white/10'
                }`}
              >
                EN
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Sign In / Register Form */}
        <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-center bg-white">
          <div className="max-w-md w-full mx-auto">
            {/* Tabs */}
            <div className="flex bg-slate-100 p-1.5 rounded-2xl mb-8 border border-slate-200">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setError('');
                  setSuccessMsg('');
                }}
                className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all ${
                  mode === 'login'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {t.signIn}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register');
                  setError('');
                  setSuccessMsg('');
                }}
                className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all ${
                  mode === 'register'
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {t.register}
              </button>
            </div>

            {/* Error & Success Messages */}
            {error && (
              <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2.5 text-xs font-semibold text-red-700 animate-fade-in">
                <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="mb-5 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2.5 text-xs font-semibold text-emerald-800 animate-fade-in">
                <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Login Form */}
            {mode === 'login' ? (
              <form onSubmit={handleLoginSubmit} className="space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-1">{t.signIn}</h3>
                  <p className="text-xs text-slate-500 mb-4">
                    Enter your registered contact number/email and password.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    {t.contact}
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type="text"
                      required
                      value={contact}
                      onChange={(e) => setContact(e.target.value)}
                      placeholder="e.g. 9876543210 or email"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    {t.password}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-saathi-primary hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
                >
                  <span>{loading ? 'Entering...' : t.signIn}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <div className="text-center pt-3 text-xs text-slate-500">
                  {t.noAccount}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register');
                      setError('');
                    }}
                    className="font-bold text-saathi-primary hover:underline"
                  >
                    {t.register}
                  </button>
                </div>
              </form>
            ) : (
              /* Register Form */
              <form onSubmit={handleRegisterSubmit} className="space-y-3.5">
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-1">{t.register}</h3>
                  <p className="text-xs text-slate-500 mb-3">
                    Register once to access personalized scheme & rights guidance.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    {t.fullName}
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Ramesh Kumar / ರಮೇಶ್"
                      className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    {t.contact}
                  </label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={contact}
                      onChange={(e) => setContact(e.target.value)}
                      placeholder="Phone or Email"
                      className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Unique identifier. Duplicate accounts are blocked.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    {t.dob}
                  </label>
                  <div className="relative">
                    <Calendar className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="date"
                      required
                      value={dob}
                      onChange={(e) => setDob(e.target.value)}
                      className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    {t.password}
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create password..."
                      className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary"
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Hashed securely with PBKDF2 before storage.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-saathi-primary hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-1"
                >
                  <span>{loading ? 'Registering...' : t.register}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <div className="text-center pt-2 text-xs text-slate-500">
                  {t.alreadyAccount}{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('login');
                      setError('');
                    }}
                    className="font-bold text-saathi-primary hover:underline"
                  >
                    {t.signIn}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

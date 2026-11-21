import React, { useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { X, User, Phone, Calendar, Lock, ShieldCheck, AlertCircle } from 'lucide-react';

export const AuthModal = ({ isOpen, onClose, onLoginSuccess }) => {
  const { t } = useLanguage();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form fields
  const [name, setName] = useState('');
  const [contact, setContact] = useState('');
  const [dob, setDob] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

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
        setSuccessMsg('Account created successfully! Logging in...');
        setTimeout(() => {
          onLoginSuccess(data.user);
          onClose();
        }, 600);
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
      setError('Please provide both contact and password.');
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
        setSuccessMsg('Welcome back! Logging in...');
        setTimeout(() => {
          onLoginSuccess(data.user);
          onClose();
        }, 500);
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-700 to-saathi-primary text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center font-bold text-lg">
              ಅ
            </div>
            <div>
              <h2 className="text-lg font-bold leading-tight">
                {mode === 'login' ? t.signIn : t.register}
              </h2>
              <p className="text-xs text-emerald-100">{t.appTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-emerald-100 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Toggle */}
        <div className="flex border-b border-slate-200 bg-slate-50">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError('');
              setSuccessMsg('');
            }}
            className={`flex-1 py-3 text-sm font-bold text-center border-b-2 transition-all ${
              mode === 'login'
                ? 'border-saathi-primary text-saathi-primary bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
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
            className={`flex-1 py-3 text-sm font-bold text-center border-b-2 transition-all ${
              mode === 'register'
                ? 'border-saathi-primary text-saathi-primary bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.register}
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-xs font-semibold text-red-700">
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs font-semibold text-emerald-800">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {mode === 'login' ? (
            /* Login Form */
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t.contact}
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={contact}
                    onChange={(e) => setContact(e.target.value)}
                    placeholder="9876543210 / citizen@domain.com"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  {t.password}
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-saathi-primary hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {loading ? '...' : t.signIn}
              </button>

              <div className="text-center pt-2 text-xs text-slate-500">
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
                    placeholder="Ramesh Kumar / ರಮೇಶ್"
                    className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
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
                    placeholder="9876543210"
                    className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Unique identifier. Existing accounts cannot re-register.
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
                    className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
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
                    placeholder="Create a password..."
                    className="w-full pl-10 pr-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-saathi-primary focus:border-transparent transition-all"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Stored securely in PBKDF2 salted hash form.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-saathi-primary hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md transition-all disabled:opacity-50 mt-2"
              >
                {loading ? '...' : t.register}
              </button>

              <div className="text-center pt-1 text-xs text-slate-500">
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
  );
};

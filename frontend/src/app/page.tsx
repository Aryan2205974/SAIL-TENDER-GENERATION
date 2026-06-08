"use client";

import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { WorkflowStepper } from "@/components/layout/WorkflowStepper";

// View imports
import { DashboardView } from "@/components/dashboard/DashboardView";
import { RequirementsView } from "@/components/requirements/RequirementsView";
import { ReferencesView } from "@/components/references/ReferencesView";
import { DraftingView } from "@/components/drafting/DraftingView";
import { ReviewView } from "@/components/review/ReviewView";
import { WorkflowView } from "@/components/workflow/WorkflowView";
import { VendorsView } from "@/components/vendors/VendorsView";
import { EvaluationView } from "@/components/evaluation/EvaluationView";
import { ReportsView } from "@/components/reports/ReportsView";

import { Sparkles, ShieldCheck, Lock, UserCheck } from "lucide-react";

export default function Page() {
  const { 
    isAuthenticated, 
    login, 
    activeTab, 
    fetchCurrentUser,
    token 
  } = useStore();

  const [email, setEmail] = useState("admin@sail.in");
  const [password, setPassword] = useState("admin123");
  const [loginError, setLoginError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLoginError("");
    const success = await login(email, password);
    setLoading(false);
    if (!success) {
      setLoginError("Invalid email or password. Use demo details below.");
    }
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardView />;
      case "requirements":
        return <RequirementsView />;
      case "references":
        return <ReferencesView />;
      case "drafting":
        return <DraftingView />;
      case "review":
        return <ReviewView />;
      case "workflow":
        return <WorkflowView />;
      case "vendors":
        return <VendorsView />;
      case "evaluation":
        return <EvaluationView />;
      case "reports":
        return <ReportsView />;
      default:
        return <DashboardView />;
    }
  };

  // ── RENDER STUNNING LOGIN PAGE ─────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-950 relative overflow-hidden font-sans">
        {/* Glow ambient background assets */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px]" />

        <div className="w-full max-w-md p-8 relative z-10">
          <form 
            onSubmit={handleLoginSubmit}
            className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl shadow-indigo-950/20 space-y-6 animate-in zoom-in-95 duration-300"
          >
            {/* Header logo & title */}
            <div className="text-center space-y-2.5">
              <div className="mx-auto w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-white tracking-tight">SAIL Procurement AI</h1>
                <p className="text-xs text-slate-400">Enterprise AI Tender Drafting & Evaluation Platform</p>
              </div>
            </div>

            {loginError && (
              <div className="p-4 bg-rose-500/15 border border-rose-500/30 rounded-2xl text-xs font-semibold text-rose-300 flex items-center space-x-2">
                <Lock className="w-4 h-4" />
                <span>{loginError}</span>
              </div>
            )}

            <div className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Corporate Email</label>
                <input 
                  type="email" 
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                  placeholder="e.g. admin@sail.in"
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Password</label>
                <input 
                  type="password" 
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold py-3.5 rounded-xl cursor-pointer shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.01] active:scale-[0.99] text-sm flex items-center justify-center"
            >
              {loading ? "Authenticating..." : "Access Platform"}
            </button>

            {/* Quick credentials card */}
            <div className="border-t border-slate-800 pt-6 mt-4">
              <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-900/30 flex items-start space-x-3">
                <UserCheck className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
                <div className="space-y-1">
                  <p className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider">Demo Credentials</p>
                  <p className="text-xs text-slate-400">
                    Use <code className="text-slate-200 font-mono">admin@sail.in</code> / <code className="text-slate-200 font-mono">admin123</code> for full administrative access.
                  </p>
                </div>
              </div>
            </div>
          </form>
        </div>
      </main>
    );
  }

  // ── RENDER AUTHENTICATED PLATFORM LAYOUT ───────────────────────────────
  return (
    <div className="flex bg-slate-50 min-h-screen font-sans">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <Topbar />

        {/* Workflow Stepper */}
        <WorkflowStepper />

        {/* View Content Workspace */}
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
}

import React, { useEffect } from "react";
import { useStore } from "@/store/useStore";
import { 
  FileText, CheckSquare, Award, Clock, ArrowRight, 
  Sparkles, CheckCircle2, AlertCircle, RefreshCw 
} from "lucide-react";

export const DashboardView: React.FC = () => {
  const {
    requirements,
    tenders,
    fetchRequirements,
    fetchTenders,
    setActiveTab,
    notifications
  } = useStore();

  useEffect(() => {
    fetchRequirements();
    fetchTenders();
  }, []);

  const stats = [
    {
      label: "Active Requirements",
      value: requirements.length,
      icon: FileText,
      color: "bg-blue-500",
      textColor: "text-blue-600",
      borderColor: "border-blue-100",
    },
    {
      label: "Tenders in Review",
      value: tenders.filter(t => t.status === "in_review").length,
      icon: Clock,
      color: "bg-amber-500",
      textColor: "text-amber-600",
      borderColor: "border-amber-100",
    },
    {
      label: "Completed Checklist Checks",
      value: "86%",
      icon: CheckSquare,
      color: "bg-emerald-500",
      textColor: "text-emerald-600",
      borderColor: "border-emerald-100",
    },
    {
      label: "Active Bid Evaluations",
      value: "4 Vendors",
      icon: Award,
      color: "bg-indigo-500",
      textColor: "text-indigo-600",
      borderColor: "border-indigo-100",
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      {/* Banner / Welcome Header */}
      <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-8 relative overflow-hidden border border-indigo-950/60 shadow-xl">
        {/* Glow effect */}
        <div className="absolute right-0 top-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="absolute left-1/3 bottom-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl" />

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 bg-indigo-500/20 text-indigo-300 px-3.5 py-1.5 rounded-full text-xs font-bold border border-indigo-500/30 mb-6 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 mr-1" />
            GenAI Core Version 1.3 Active
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight mb-3">
            SAIL AI Procurement Intelligence
          </h1>
          <p className="text-slate-300 text-sm leading-relaxed mb-8">
            Create compliance-validated tender specifications, find similar tenders in the historical RAG library, and automatically score incoming vendor bids.
          </p>
          <div className="flex space-x-4">
            <button 
              onClick={() => setActiveTab("requirements")}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 shadow-lg shadow-indigo-600/30 flex items-center cursor-pointer"
            >
              Start New Procurement Intake
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
            <button 
              onClick={() => setActiveTab("references")}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center cursor-pointer"
            >
              Browse Tender Library
            </button>
          </div>
        </div>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div 
              key={idx} 
              className={`bg-white border ${stat.borderColor} rounded-2xl p-6 shadow-sm flex items-center justify-between hover:shadow-md transition-all duration-200`}
            >
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">{stat.label}</span>
                <span className="text-2xl font-extrabold text-slate-800">{stat.value}</span>
              </div>
              <div className={`w-12 h-12 rounded-xl ${stat.color}/10 flex items-center justify-center`}>
                <Icon className={`w-6 h-6 ${stat.textColor}`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Access & Recent Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Tenders list */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm lg:col-span-2 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <h3 className="font-bold text-slate-800 text-base">Active Tenders & AI drafting status</h3>
            <button 
              onClick={() => setActiveTab("drafting")}
              className="text-xs text-indigo-600 font-semibold hover:text-indigo-700"
            >
              View Workbench
            </button>
          </div>
          <div className="flex-1 space-y-4">
            {tenders.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-slate-400 text-xs">
                No active tenders. Initialize a requirement first.
              </div>
            ) : (
              tenders.slice(0, 3).map((tender) => (
                <div 
                  key={tender.id} 
                  className="p-4 rounded-xl border border-slate-100 hover:border-indigo-100 hover:bg-slate-50/50 transition-all duration-200 flex items-center justify-between"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] bg-slate-100 border border-slate-200 text-slate-500 font-bold px-2 py-0.5 rounded-full">
                        {tender.tender_id}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        tender.status === "in_review" 
                          ? "bg-amber-50 text-amber-600 border border-amber-200" 
                          : "bg-indigo-50 text-indigo-600 border border-indigo-200"
                      }`}>
                        {tender.status.replace("_", " ")}
                      </span>
                    </div>
                    <h4 className="font-bold text-slate-800 text-sm truncate">{tender.title}</h4>
                    <p className="text-xs text-slate-400">
                      Draft completeness: <span className="font-semibold text-slate-600">{tender.draft_completeness}%</span>
                    </p>
                  </div>

                  <button 
                    onClick={() => {
                      useStore.setState({ activeTender: tender });
                      if (tender.status === "in_review") {
                        setActiveTab("workflow");
                      } else {
                        setActiveTab("drafting");
                      }
                    }}
                    className="p-2 bg-slate-100 hover:bg-indigo-50 text-slate-500 hover:text-indigo-600 rounded-lg transition-colors cursor-pointer"
                  >
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Action Panel / Recent Notifications */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <h3 className="font-bold text-slate-800 text-base">System Events</h3>
            <button className="p-1 text-slate-400 hover:text-indigo-600 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 space-y-4">
            {notifications.slice(0, 4).map((n) => (
              <div key={n.id} className="flex space-x-3 text-xs leading-normal">
                <div className="mt-0.5">
                  {n.type === "warning" ? (
                    <AlertCircle className="w-4 h-4 text-amber-500" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  )}
                </div>
                <div className="space-y-0.5">
                  <p className="font-semibold text-slate-800">{n.title}</p>
                  <p className="text-slate-400">{n.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { BarChart3, TrendingUp, ShieldAlert, Cpu, CheckCircle2, History } from "lucide-react";
import { api } from "@/lib/api";

export const ReportsView: React.FC = () => {
  const { tenders } = useStore();
  const [governanceData, setGovernanceData] = useState<any>(null);

  useEffect(() => {
    const fetchGovernance = async () => {
      try {
        const res = await api.get("/api/reports/ai-governance");
        setGovernanceData(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchGovernance();
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Platform Analytics Dashboard (Left 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-lg font-bold text-slate-800">Reports & Analytics</h3>
          <p className="text-xs text-slate-400 mt-1">Platform-wide tender metadata distribution, system analytics, and speed KPI indicators</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-5 border border-slate-100 rounded-2xl space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Avg Drafting Time</span>
            <span className="text-2xl font-extrabold text-slate-800">45s / tender</span>
            <p className="text-[10px] text-slate-400 font-medium flex items-center">
              <TrendingUp className="w-3.5 h-3.5 mr-1 text-emerald-500" />
              98% faster than manual draft
            </p>
          </div>
          <div className="p-5 border border-slate-100 rounded-2xl space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Compliance rate</span>
            <span className="text-2xl font-extrabold text-emerald-600">100% Passed</span>
            <p className="text-[10px] text-slate-400 font-medium">All active templates verified</p>
          </div>
          <div className="p-5 border border-slate-100 rounded-2xl space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">AI-Human Touch Ratio</span>
            <span className="text-2xl font-extrabold text-indigo-600">86% / 14%</span>
            <p className="text-[10px] text-slate-400 font-medium">14% human modification weight</p>
          </div>
        </div>

        {/* System activity mock log */}
        <div className="space-y-3 pt-4 border-t border-slate-100">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <History className="w-4 h-4 mr-2 text-slate-500" />
            Historical Run Metrics
          </h4>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-slate-800">Tender Specifications generated</p>
                <p className="text-slate-400 text-[10px]">Tender Mode: OTE • Department: IT Services</p>
              </div>
              <span className="text-[10px] bg-indigo-50 border border-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
                1.3s generation
              </span>
            </div>
            <div className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 text-xs">
              <div className="space-y-0.5">
                <p className="font-bold text-slate-800">Historical RAG database indexed</p>
                <p className="text-slate-400 text-[10px]">Total records: 125 documents • Vector indexes: FAISS</p>
              </div>
              <span className="text-[10px] bg-emerald-50 border border-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">
                Healthy
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Governance Engine (Right 1 col) */}
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <Cpu className="w-4 h-4 mr-2 text-indigo-600 animate-pulse" />
            AI Governance Monitor
          </h4>
          <p className="text-xs text-slate-400 leading-normal">
            Track metrics and logs for auditing AI activity, token counts, model fine-tuning records, and prompt updates.
          </p>

          {governanceData ? (
            <div className="space-y-3 border-t border-slate-100 pt-5 text-xs animate-in fade-in duration-300">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Total tokens processed:</span>
                <span className="font-extrabold text-slate-800">{governanceData.total_tokens_processed.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Average LLM latency:</span>
                <span className="font-extrabold text-slate-800">{governanceData.average_latency_seconds}s</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Active Model:</span>
                <span className="font-extrabold text-indigo-600 bg-indigo-50 border border-indigo-100/50 px-2 py-0.5 rounded-md">
                  {governanceData.model_name.replace("meta-llama/", "")}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Safety checks:</span>
                <span className="font-extrabold text-emerald-600 flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> All clear
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 italic">Loading governance metrics...</div>
          )}
        </div>
      </div>

    </div>
  );
};

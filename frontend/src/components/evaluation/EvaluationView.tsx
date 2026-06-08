import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { Award, Upload, AlertCircle, FileText, CheckCircle2, ChevronRight, Sparkles, Building } from "lucide-react";
import { api } from "@/lib/api";

export const EvaluationView: React.FC = () => {
  const { tenders, vendors, fetchTenders, fetchVendors } = useStore();
  const [selectedTenderId, setSelectedTenderId] = useState<string>("");
  const [selectedVendorId, setSelectedVendorId] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  
  // Evaluation Output State
  const [evaluation, setEvaluation] = useState<any>(null);

  useEffect(() => {
    fetchTenders();
    fetchVendors();
  }, []);

  const handleBidUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !selectedTenderId || !selectedVendorId) return;
    setIsUploading(true);
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("tender_id", selectedTenderId);
    formData.append("vendor_id", selectedVendorId);

    try {
      const uploadRes = await api.post("/api/bids/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const bid = uploadRes.data;

      // Trigger Evaluation
      setIsEvaluating(true);
      const evalRes = await api.post("/api/bids/evaluate", { bid_id: bid.id });
      setEvaluation(evalRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
      setIsEvaluating(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Bid Upload & Config (Left Column) */}
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-lg font-bold text-slate-800">Submit Bid for Scoring</h3>
          <p className="text-xs text-slate-400 mt-1">Upload incoming vendor bids and run compliance score matching against tender rules</p>
        </div>

        <div className="space-y-4">
          {/* Target Tender */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Select Target Tender</label>
            <select
              value={selectedTenderId}
              onChange={e => setSelectedTenderId(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm bg-white"
            >
              <option value="">-- Choose Tender --</option>
              {tenders.map((t) => (
                <option key={t.id} value={t.id}>{t.tender_id} - {t.title}</option>
              ))}
            </select>
          </div>

          {/* Vendor */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Select Bidding Vendor</label>
            <select
              value={selectedVendorId}
              onChange={e => setSelectedVendorId(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm bg-white"
            >
              <option value="">-- Choose Vendor --</option>
              {vendors.map((v) => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </select>
          </div>

          {/* Dropzone */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Bid Document (PDF/Word)</label>
            <div className={`border-2 border-dashed rounded-2xl p-6 transition-colors flex flex-col items-center justify-center bg-slate-50/50 hover:bg-indigo-50/10 relative ${
              (!selectedTenderId || !selectedVendorId) ? "opacity-50 pointer-events-none" : "hover:border-indigo-400"
            }`}>
              <input 
                type="file" 
                id="bid-upload"
                onChange={handleBidUpload}
                className="absolute inset-0 opacity-0 cursor-pointer"
                disabled={isUploading || isEvaluating || !selectedTenderId || !selectedVendorId}
              />
              <div className="w-12 h-12 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center mb-3">
                <Upload className="w-5 h-5 text-indigo-600" />
              </div>
              <span className="text-xs font-semibold text-slate-800">
                {isUploading ? "Uploading Bid Spec..." : isEvaluating ? "AI Scoring Active..." : "Upload Vendor Bid"}
              </span>
              <span className="text-[10px] text-slate-400 mt-1">Select Tender & Vendor to enable</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Evaluation Report (Right 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm flex flex-col h-[calc(100vh-14rem)]">
        <div className="border-b border-slate-100 pb-4 mb-4">
          <h3 className="text-lg font-bold text-slate-800">AI Bid Evaluation Report</h3>
          <p className="text-xs text-slate-400 mt-1">AI-calculated compliance weights, technical completeness scoring, and final recommendations</p>
        </div>

        {evaluation ? (
          <div className="flex-1 overflow-y-auto space-y-6 pr-2 custom-scrollbar animate-in fade-in duration-300">
            {/* Score Ring Summary */}
            <div className="flex items-center space-x-6 bg-slate-50 border border-slate-100 p-5 rounded-2xl">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="#E2E8F0" strokeWidth="8" fill="transparent" />
                  <circle 
                    cx="48" cy="48" r="40" stroke="#4F46E5" strokeWidth="8" fill="transparent" 
                    strokeDasharray="251" strokeDashoffset={251 - (251 * evaluation.overall_score) / 100}
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute text-center">
                  <span className="text-xl font-extrabold text-slate-800">{evaluation.overall_score}%</span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="inline-flex items-center bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                  <Sparkles className="w-3 h-3 mr-1" /> AI Scoring Complete
                </div>
                <h4 className="font-extrabold text-slate-800 text-sm">Bid Compliance Score</h4>
                <p className="text-xs text-slate-400">
                  Calculated against {tenders.find(t => t.id.toString() === selectedTenderId)?.title || "the select tender specifications"}.
                </p>
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1.5" /> Strengths & Compliances
                </h5>
                <ul className="space-y-2">
                  {evaluation.strengths && evaluation.strengths.map((str: string, idx: number) => (
                    <li key={idx} className="p-3 bg-emerald-50/30 border border-emerald-100/50 text-xs text-emerald-800 rounded-xl leading-normal">
                      {str}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="space-y-2">
                <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center">
                  <AlertCircle className="w-4 h-4 text-rose-500 mr-1.5" /> Weaknesses & Gaps
                </h5>
                <ul className="space-y-2">
                  {evaluation.weaknesses && evaluation.weaknesses.map((wk: string, idx: number) => (
                    <li key={idx} className="p-3 bg-rose-50/30 border border-rose-100/50 text-xs text-rose-800 rounded-xl leading-normal">
                      {wk}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* AI Summary Text */}
            <div className="space-y-2">
              <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Evaluation Executive Summary</h5>
              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 border border-slate-100 p-4 rounded-xl font-mono">
                {evaluation.ai_summary}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 text-xs space-y-2">
            <Award className="w-12 h-12 text-slate-300" />
            <p className="font-semibold text-slate-500">No active bid evaluation results</p>
            <p className="max-w-[240px] text-center text-[10px] leading-normal text-slate-400">
              Select a tender and vendor, then upload their bid specifications to activate the evaluation engine.
            </p>
          </div>
        )}
      </div>

    </div>
  );
};

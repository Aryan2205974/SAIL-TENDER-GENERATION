import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { 
  Sparkles, CheckCircle2, AlertTriangle, AlertCircle, 
  Download, FileText, Send, ChevronRight, CheckSquare, MessageSquare
} from "lucide-react";
import { api, API_BASE_URL } from "@/lib/api";

export const ReviewView: React.FC = () => {
  const { 
    activeTender, 
    validationChecks, 
    comments, 
    fetchTenderDetails,
    setActiveTab 
  } = useStore();

  const [activeCheckId, setActiveCheckId] = useState<number | null>(null);
  const [commentText, setCommentText] = useState("");
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  useEffect(() => {
    if (activeTender) {
      fetchTenderDetails(activeTender.id);
    }
  }, [activeTender?.id]);

  useEffect(() => {
    if (validationChecks && validationChecks.length > 0 && activeCheckId === null) {
      setActiveCheckId(validationChecks[0].id);
    }
  }, [validationChecks]);

  const activeCheck = validationChecks.find(c => c.id === activeCheckId);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full flex items-center"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Verified</span>;
      case "warning":
        return <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full flex items-center"><AlertTriangle className="w-3.5 h-3.5 mr-1" /> Action Needed</span>;
      case "failed":
        return <span className="text-[10px] font-bold text-rose-600 bg-rose-50 border border-rose-100 px-2 py-0.5 rounded-full flex items-center"><AlertCircle className="w-3.5 h-3.5 mr-1" /> Failed</span>;
      default:
        return <span className="text-[10px] font-bold text-slate-400 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">Pending</span>;
    }
  };

  const handlePostComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTender || !commentText.trim()) return;
    setIsSubmittingComment(true);
    try {
      await api.post("/api/workflow/comment", {
        tender_id: activeTender.id,
        content: commentText
      });
      setCommentText("");
      await fetchTenderDetails(activeTender.id);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  const handleSubmitReview = async () => {
    if (!activeTender) return;
    setIsSubmittingReview(true);
    try {
      await api.post("/api/workflow/review", {
        tender_id: activeTender.id,
        assignee_id: 1, // first reviewer
        priority: "high",
        due_days: 3
      });
      setActiveTab("workflow");
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleExport = (type: string) => {
    if (!activeTender) return;
    // Direct link to the API download endpoint
    const url = `${API_BASE_URL}/api/export/${type}/${activeTender.id}`;
    window.open(url, "_blank");
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Validation Checklist (Left 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6 flex flex-col h-[calc(100vh-14rem)]">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-lg font-bold text-slate-800">Compliance & Validation Checklist</h3>
          <p className="text-xs text-slate-400 mt-1">AI-driven inspection engine checking guidelines, mandatory inputs, and terms validation</p>
        </div>

        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 min-h-0">
          {/* Checks list */}
          <div className="space-y-2 overflow-y-auto pr-2 custom-scrollbar">
            {validationChecks.map((check) => {
              const isActive = check.id === activeCheckId;
              return (
                <div
                  key={check.id}
                  onClick={() => setActiveCheckId(check.id)}
                  className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                    isActive 
                      ? "border-indigo-600 bg-indigo-50/10 shadow-sm"
                      : "border-slate-100 hover:border-slate-200 hover:bg-slate-50/40"
                  }`}
                >
                  <div className="space-y-1 min-w-0 mr-2">
                    <h4 className="font-bold text-slate-800 text-xs truncate">{check.check_area}</h4>
                    <p className="text-[10px] text-slate-400 truncate font-medium">Owner: {check.owner || "System"}</p>
                  </div>
                  {getStatusBadge(check.status)}
                </div>
              );
            })}
          </div>

          {/* Details column */}
          <div className="border border-slate-100 rounded-2xl p-5 bg-slate-50/50 flex flex-col justify-between overflow-y-auto custom-scrollbar">
            {activeCheck ? (
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <h4 className="font-bold text-slate-800 text-sm">{activeCheck.check_area}</h4>
                  {getStatusBadge(activeCheck.status)}
                </div>
                
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">AI Observation</span>
                  <p className="text-xs text-slate-600 leading-relaxed bg-white border border-slate-100 p-3 rounded-xl">
                    {activeCheck.ai_observation || "No observation logged."}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Human Action Required</span>
                  <p className="text-xs text-slate-600 leading-relaxed bg-white border border-slate-100 p-3 rounded-xl font-medium">
                    {activeCheck.human_action_required || "No manual action required."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
                Select validation check to view details.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Export & Comment Feed (Right 1 col) */}
      <div className="space-y-6 flex flex-col justify-between h-[calc(100vh-14rem)]">
        {/* Export options */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-4">
          <h4 className="font-bold text-slate-800 text-sm">Download Draft Spec</h4>
          <div className="grid grid-cols-3 gap-3">
            <button 
              onClick={() => handleExport("pdf")}
              className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/10 transition-all cursor-pointer font-semibold"
            >
              <Download className="w-5 h-5 text-indigo-600 mb-1" />
              <span className="text-[10px] text-slate-600">PDF</span>
            </button>
            <button 
              onClick={() => handleExport("docx")}
              className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/10 transition-all cursor-pointer font-semibold"
            >
              <Download className="w-5 h-5 text-indigo-600 mb-1" />
              <span className="text-[10px] text-slate-600">Word</span>
            </button>
            <button 
              onClick={() => handleExport("html")}
              className="flex flex-col items-center justify-center p-3 rounded-xl border border-slate-100 hover:border-indigo-200 hover:bg-indigo-50/10 transition-all cursor-pointer font-semibold"
            >
              <Download className="w-5 h-5 text-indigo-600 mb-1" />
              <span className="text-[10px] text-slate-600">HTML</span>
            </button>
          </div>
        </div>

        {/* Comments Feed */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex-1 flex flex-col space-y-4 min-h-0 overflow-hidden">
          <h4 className="font-bold text-slate-800 text-sm flex items-center">
            <MessageSquare className="w-4 h-4 mr-2 text-indigo-600" />
            Comments & Audit Logs
          </h4>
          
          {/* Feed */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {comments.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs italic">
                No comments posted yet.
              </div>
            ) : (
              comments.map((c) => (
                <div key={c.id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="font-bold text-slate-700">{c.author_name} ({c.author_role})</span>
                    <span className="text-slate-400">
                      {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-normal">{c.content}</p>
                </div>
              ))
            )}
          </div>

          {/* Input field */}
          <form onSubmit={handlePostComment} className="flex space-x-2">
            <input
              type="text"
              required
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              placeholder="Add review comment..."
            />
            <button
              type="submit"
              disabled={isSubmittingComment}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white p-2.5 rounded-xl cursor-pointer shadow-md"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* Submit to review button */}
        <button
          onClick={handleSubmitReview}
          disabled={isSubmittingReview}
          className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-3xl shadow-xl flex items-center justify-center cursor-pointer transition-all active:scale-[0.98]"
        >
          {isSubmittingReview ? "Submitting..." : "Submit for Approval"}
          <ChevronRight className="w-4 h-4 ml-1.5" />
        </button>
      </div>

    </div>
  );
};

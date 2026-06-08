import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { 
  CheckCircle2, Clock, Ban, User, AlertCircle, 
  ChevronRight, ArrowRight, ShieldCheck, ThumbsUp, ThumbsDown
} from "lucide-react";
import { api } from "@/lib/api";

export const WorkflowView: React.FC = () => {
  const { 
    activeTender, 
    approvals, 
    fetchTenderDetails,
    setActiveTab 
  } = useStore();

  const [actionLoading, setActionLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (activeTender) {
      fetchTenderDetails(activeTender.id);
    }
  }, [activeTender?.id]);

  const activeApproval = approvals.find(a => a.status === "in_progress");

  const handleAction = async (action: "approve" | "reject") => {
    if (!activeTender || !activeApproval) return;
    setActionLoading(true);
    try {
      const payload = action === "approve"
        ? {
            tender_id: activeTender.id,
            stage: activeApproval.stage,
            comment: `Action: approve performed by current reviewer.`
          }
        : {
            tender_id: activeTender.id,
            stage: activeApproval.stage,
            reason: `Action: reject performed by current reviewer.`
          };

      await api.post(`/api/workflow/${action}`, payload);
      setSuccessMsg(`Workflow Stage ${action === "approve" ? "Approved" : "Rejected"} successfully!`);
      setTimeout(() => setSuccessMsg(""), 4000);
      await fetchTenderDetails(activeTender.id);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!activeTender) return;
    setActionLoading(true);
    try {
      await api.put(`/api/tenders/${activeTender.id}`, {
        status: "published"
      });
      setSuccessMsg("Tender published successfully on e-portal!");
      setTimeout(() => setSuccessMsg(""), 4000);
      await fetchTenderDetails(activeTender.id);
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case "in_progress":
        return <Clock className="w-5 h-5 text-indigo-500 animate-pulse" />;
      case "rejected":
        return <Ban className="w-5 h-5 text-rose-500" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-slate-200 bg-white" />;
    }
  };

  const isWorkflowFullyCompleted = approvals.length > 0 && approvals.every(a => a.status === "completed");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Workflow Chain Timeline (Left 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-lg font-bold text-slate-800">Workflow Approval Chain</h3>
          <p className="text-xs text-slate-400 mt-1">Real-time status tracking for technical, financial, and committee approval milestones</p>
        </div>

        {/* Success message banner */}
        {successMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-2xl flex items-center space-x-2 text-xs font-semibold text-emerald-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Timeline list */}
        <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
          {approvals.map((ap) => {
            const isCompleted = ap.status === "completed";
            const isInProgress = ap.status === "in_progress";
            const isRejected = ap.status === "rejected";

            return (
              <div key={ap.id} className="relative flex items-start space-x-4">
                {/* Bullet */}
                <div className="absolute -left-[23px] top-0.5 z-10">
                  {getStatusIcon(ap.status)}
                </div>

                {/* Details */}
                <div className={`flex-1 border rounded-2xl p-4 transition-all ${
                  isInProgress 
                    ? "border-indigo-200 bg-indigo-50/10 shadow-sm" 
                    : isCompleted
                    ? "border-slate-100 bg-slate-50/20"
                    : "border-slate-50 bg-transparent text-slate-400"
                }`}>
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                    <div className="space-y-0.5">
                      <h4 className={`font-bold text-xs ${
                        isInProgress ? "text-indigo-900" : isCompleted ? "text-slate-700" : "text-slate-400"
                      }`}>
                        {ap.stage_label}
                      </h4>
                      {ap.assignee_name && (
                        <p className="text-[10px] font-medium flex items-center">
                          <User className="w-3.5 h-3.5 mr-1 text-slate-400" />
                          {ap.assignee_name} ({ap.assignee_role})
                        </p>
                      )}
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        isCompleted
                          ? "bg-emerald-50 text-emerald-600 border border-emerald-200"
                          : isInProgress
                          ? "bg-indigo-50 text-indigo-600 border border-indigo-200"
                          : isRejected
                          ? "bg-rose-50 text-rose-600 border border-rose-200"
                          : "bg-slate-100 text-slate-400 border border-slate-200"
                      }`}>
                        {ap.status}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Review Actions Panel (Right 1 col) */}
      <div className="space-y-6">
        
        {/* Actions Card */}
        {activeApproval ? (
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm space-y-6">
            <div>
              <h4 className="font-bold text-slate-800 text-sm flex items-center">
                <ShieldCheck className="w-4 h-4 mr-2 text-indigo-600" />
                Review Decision
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-normal">
                You are currently reviewing the <strong>{activeApproval.stage_label}</strong> step. Select a review action.
              </p>
            </div>

            <div className="space-y-3">
              <button
                onClick={() => handleAction("approve")}
                disabled={actionLoading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl cursor-pointer shadow-lg shadow-indigo-600/10 flex items-center justify-center transition-all active:scale-[0.98] text-sm"
              >
                <ThumbsUp className="w-4 h-4 mr-2" />
                Approve Stage
              </button>

              <button
                onClick={() => handleAction("reject")}
                disabled={actionLoading}
                className="w-full bg-white hover:bg-rose-50 text-rose-600 border border-rose-200 font-bold py-3.5 rounded-xl cursor-pointer flex items-center justify-center transition-colors text-sm"
              >
                <ThumbsDown className="w-4 h-4 mr-2" />
                Reject & Send Back
              </button>
            </div>
          </div>
        ) : isWorkflowFullyCompleted && activeTender?.status !== "published" ? (
          <div className="bg-gradient-to-br from-indigo-900 to-indigo-950 text-white border border-indigo-950 rounded-3xl p-6 shadow-xl space-y-4">
            <h4 className="font-bold text-white text-base">Ready for Publishing</h4>
            <p className="text-xs text-slate-300 leading-normal">
              The workflow approval chain has completed. The tender specifications can now be published directly onto the live public procurement portal.
            </p>
            <button
              onClick={handlePublish}
              disabled={actionLoading}
              className="w-full bg-white text-indigo-900 font-bold py-3.5 rounded-xl hover:bg-slate-100 transition-colors shadow-lg flex items-center justify-center cursor-pointer disabled:bg-slate-300 disabled:text-slate-500 active:scale-[0.98]"
            >
              Publish Tender Specifications
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm text-center py-12 text-slate-400 space-y-2">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
            <h4 className="font-bold text-slate-800 text-sm">Workflow Inactive</h4>
            <p className="text-xs max-w-[200px] mx-auto leading-normal">
              {activeTender?.status === "published" 
                ? "This tender has already been published to the e-portal." 
                : "A requirement must be submitted for review first."}
            </p>
          </div>
        )}

        {/* Dashboard shortcut */}
        <button
          onClick={() => setActiveTab("dashboard")}
          className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-3xl shadow-xl flex items-center justify-center cursor-pointer transition-all active:scale-[0.98]"
        >
          Return to Dashboard
          <ArrowRight className="w-4 h-4 ml-1.5" />
        </button>
      </div>

    </div>
  );
};

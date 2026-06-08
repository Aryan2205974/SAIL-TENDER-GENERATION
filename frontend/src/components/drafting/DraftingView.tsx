import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { 
  Sparkles, CheckCircle2, AlertTriangle, FileText, 
  HelpCircle, ChevronRight, RefreshCw, Send, Check, Undo
} from "lucide-react";
import { api } from "@/lib/api";

export const DraftingView: React.FC = () => {
  const { 
    activeTender, 
    tenderSections, 
    fetchTenders, 
    fetchTenderDetails,
    setActiveTab 
  } = useStore();

  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [refinementPrompt, setRefinementPrompt] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    // If no active tender, fetch and select the first one for the demo
    const loadData = async () => {
      await fetchTenders();
    };
    loadData();
  }, []);

  const storeActiveTender = useStore(state => state.activeTender);

  useEffect(() => {
    if (storeActiveTender) {
      setActiveSectionId(null);
      fetchTenderDetails(storeActiveTender.id);
    }
  }, [storeActiveTender?.id]);

  useEffect(() => {
    if (tenderSections && tenderSections.length > 0 && activeSectionId === null) {
      setActiveSectionId(tenderSections[0].id);
      setEditorContent(tenderSections[0].content || "");
    }
  }, [tenderSections, activeSectionId]);

  const activeSection = tenderSections.find(s => s.id === activeSectionId);

  // Sync editorContent state when selected section's content in store is populated or changed
  useEffect(() => {
    if (activeSection) {
      setEditorContent(activeSection.content || "");
    }
  }, [activeSectionId, activeSection?.content]);

  // Dynamic Polling: Fetch details every 5 seconds if the tender is currently generating
  useEffect(() => {
    if (!activeTender || activeTender.status !== "generating") return;

    const interval = setInterval(() => {
      fetchTenderDetails(activeTender.id);
    }, 5000);

    return () => clearInterval(interval);
  }, [activeTender?.id, activeTender?.status]);

  const handleSelectSection = (id: number) => {
    setActiveSectionId(id);
    const sec = tenderSections.find(s => s.id === id);
    setEditorContent(sec?.content || "");
  };

  const handleSaveContent = async () => {
    if (!activeTender || !activeSection) return;
    try {
      // Update section locally/remotely
      await api.put(`/api/tenders/${activeTender.id}`, {
        sections: [
          {
            id: activeSection.id,
            content: editorContent,
            status: "completed"
          }
        ]
      });
      setSuccessMsg("Changes saved successfully!");
      setTimeout(() => setSuccessMsg(""), 3000);
      await fetchTenderDetails(activeTender.id);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefineSection = async () => {
    if (!activeTender || !activeSection || !refinementPrompt.trim()) return;
    setIsRefining(true);
    try {
      const res = await api.post("/api/ai/section", {
        tender_id: activeTender.id,
        section_id: activeSection.id,
        prompt: refinementPrompt
      });
      setEditorContent(res.data.content);
      setRefinementPrompt("");
      setSuccessMsg("AI Section regenerated!");
      setTimeout(() => setSuccessMsg(""), 3000);
      await fetchTenderDetails(activeTender.id);
    } catch (err) {
      console.error(err);
    } finally {
      setIsRefining(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-slate-300" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Sections Sidebar (Left 1 col) */}
      <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm space-y-4 flex flex-col h-[calc(100vh-14rem)] overflow-y-auto custom-scrollbar">
        <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider px-2">Tender Sections</h4>
        <div className="space-y-1">
          {tenderSections.map((sec) => {
            const isActive = sec.id === activeSectionId;
            return (
              <button
                key={sec.id}
                onClick={() => handleSelectSection(sec.id)}
                className={`w-full flex items-center justify-between px-3 py-3 rounded-xl text-xs font-semibold transition-all text-left border ${
                  isActive
                    ? "bg-indigo-600/10 border-indigo-600 text-indigo-700"
                    : "border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <span className="truncate mr-2">{sec.section_name}</span>
                {getStatusIcon(sec.status)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Editor Workbench (Center 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm flex flex-col h-[calc(100vh-14rem)]">
        {activeSection ? (
          <div className="flex flex-col h-full space-y-4">
            {/* Header info */}
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
              <div>
                <h3 className="font-bold text-slate-800 text-base">{activeSection.section_name}</h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  AI confidence: <span className="font-semibold text-emerald-600">High</span> • Overrides count: {activeTender?.human_overrides_count || 0}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {successMsg && (
                  <span className="text-xs text-emerald-600 font-semibold bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-100 flex items-center">
                    <Check className="w-3.5 h-3.5 mr-1" />
                    {successMsg}
                  </span>
                )}
                <button
                  onClick={handleSaveContent}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl cursor-pointer shadow-md shadow-indigo-600/10 transition-colors"
                >
                  Save Section
                </button>
              </div>
            </div>

            {/* Editable Content */}
            <div className="flex-1 min-h-0">
              <textarea
                value={editorContent}
                onChange={(e) => setEditorContent(e.target.value)}
                className="w-full h-full border-none outline-none focus:ring-0 text-sm leading-relaxed text-slate-700 font-mono p-2 overflow-y-auto custom-scrollbar"
                placeholder="Section content markdown..."
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
            No sections available. Generating or loading draft...
          </div>
        )}
      </div>

      {/* AI Assistant Refinement Panel (Right 1 col) */}
      <div className="space-y-6 flex flex-col justify-between h-[calc(100vh-14rem)]">
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex-1 flex flex-col space-y-5 overflow-y-auto custom-scrollbar">
          <div>
            <h4 className="font-bold text-slate-800 text-sm mb-1 flex items-center">
              <Sparkles className="w-4 h-4 mr-2 text-indigo-600 animate-pulse" />
              AI Assistant Panel
            </h4>
            <p className="text-[11px] text-slate-400 leading-normal">
              Refine this section by submitting natural language instructions directly to the AI generator.
            </p>
          </div>

          {/* Chat/Refinement input box */}
          <div className="space-y-2">
            <textarea
              rows={3}
              value={refinementPrompt}
              onChange={(e) => setRefinementPrompt(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all leading-normal"
              placeholder="e.g. Add 10% advance payment terms or add details about vendor training..."
            />
            <button
              onClick={handleRefineSection}
              disabled={isRefining || !refinementPrompt.trim()}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold py-2.5 rounded-xl text-xs flex items-center justify-center cursor-pointer shadow-md"
            >
              {isRefining ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                  Generating Spec...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5 mr-1.5" />
                  Apply Refinements
                </>
              )}
            </button>
          </div>

          {/* References Source matches */}
          <div className="border-t border-slate-100 pt-4 space-y-3">
            <h5 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Source References Linked</h5>
            {activeSection?.source_ref ? (
              <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-start space-x-2 text-[11px] text-slate-600">
                <FileText className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
                <span>{activeSection.source_ref}</span>
              </div>
            ) : (
              <div className="text-[11px] text-slate-400 italic">No direct reference matches for this section.</div>
            )}
          </div>
        </div>

        {/* Proceed Button */}
        <button
          onClick={() => setActiveTab("review")}
          className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-4 rounded-3xl shadow-xl flex items-center justify-center cursor-pointer transition-all active:scale-[0.98]"
        >
          Checklist & Validation
          <ChevronRight className="w-4 h-4 ml-1.5" />
        </button>
      </div>

    </div>
  );
};

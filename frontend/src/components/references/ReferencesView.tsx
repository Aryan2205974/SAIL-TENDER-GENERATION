import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { 
  Library, Search, FileText, Upload, Check, 
  Sparkles, ShieldCheck, Trash2, ArrowRight, ChevronRight
} from "lucide-react";
import { api } from "@/lib/api";

export const ReferencesView: React.FC = () => {
  const { 
    references, 
    fetchReferences, 
    activeRequirement,
    generateTenderPlan,
    setActiveTab
  } = useStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]); 
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchReferences();
  }, []);

  const handleToggleDoc = (id: number) => {
    setSelectedDocs(prev => 
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploading(true);
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type", "Tender Document");
    formData.append("department", activeRequirement?.department || "Contracts & Procurement");
    formData.append("procurement_type", activeRequirement?.procurement_type || "Service Contracting");
    formData.append("year", new Date().getFullYear().toString());
    formData.append("category", activeRequirement?.category || "IT Services");

    try {
      // Upload
      const res = await api.post("/api/reference/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      const doc = res.data;
      
      // Instantly trigger chunking and embedding in the background for demo reactivity
      await api.post("/api/rag/chunk", { document_id: doc.id });
      await api.post("/api/rag/embed", { document_id: doc.id });
      
      // Preselect the new document
      setSelectedDocs(prev => [...prev, doc.id]);
      await fetchReferences();
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleGenerateDraft = async () => {
    setIsGenerating(true);
    try {
      // Find or use active requirement id
      const reqId = activeRequirement?.id || 1;
      await generateTenderPlan(reqId);
      setActiveTab("drafting");
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const filteredDocs = references.filter(doc => 
    doc.original_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (doc.tags && doc.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())))
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Document Library (Left 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Historical Reference Library</h3>
            <p className="text-xs text-slate-400 mt-1">Select previous tender templates and specifications to train the AI draft generator</p>
          </div>
          
          {/* Search bar */}
          <div className="relative max-w-xs w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="Search by tag, name..."
            />
          </div>
        </div>

        {/* Upload Zone */}
        <div className="border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-2xl p-6 transition-colors flex flex-col items-center justify-center bg-slate-50/50 hover:bg-indigo-50/10 relative">
          <input 
            type="file" 
            id="file-upload"
            onChange={handleFileUpload}
            className="absolute inset-0 opacity-0 cursor-pointer"
            disabled={isUploading}
          />
          <div className="w-12 h-12 rounded-xl bg-white border border-slate-100 shadow-sm flex items-center justify-center mb-3">
            <Upload className="w-5 h-5 text-indigo-600" />
          </div>
          <span className="text-sm font-semibold text-slate-800">
            {isUploading ? "Uploading & Vectorizing Document..." : "Upload Reference Document"}
          </span>
          <span className="text-xs text-slate-400 mt-1">PDF, DOCX formats supported. Auto-chunked & vectorized.</span>
        </div>

        {/* References Table/List */}
        <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
          {filteredDocs.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-slate-400 text-xs">
              No matching documents found in library.
            </div>
          ) : (
            filteredDocs.map((doc) => {
              const isSelected = selectedDocs.includes(doc.id);
              return (
                <div 
                  key={doc.id} 
                  onClick={() => handleToggleDoc(doc.id)}
                  className={`p-4 rounded-xl border transition-all duration-200 flex items-center justify-between cursor-pointer ${
                    isSelected 
                      ? "border-indigo-600 bg-indigo-50/10 shadow-sm shadow-indigo-600/5" 
                      : "border-slate-100 hover:border-slate-200 hover:bg-slate-50/40"
                  }`}
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    {/* Checkbox circle */}
                    <div className={`w-5 h-5 rounded-md flex items-center justify-center border transition-all ${
                      isSelected 
                        ? "bg-indigo-600 border-indigo-600 text-white" 
                        : "border-slate-300 bg-white"
                    }`}>
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3px]" />}
                    </div>

                    <div className="space-y-1.5 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] bg-slate-100 text-slate-500 font-bold px-2 py-0.5 rounded-full border border-slate-200">
                          {doc.doc_type}
                        </span>
                        <span className="text-[10px] text-slate-400">{doc.year} • {(doc.file_size / 1024).toFixed(0)} KB</span>
                      </div>
                      <h4 className="font-bold text-slate-800 text-sm truncate max-w-md">{doc.original_name}</h4>
                      {/* Tags */}
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {doc.tags.slice(0, 3).map((tag, idx) => (
                            <span key={idx} className="text-[9px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-md">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end space-y-1.5">
                    {doc.is_embedded && (
                      <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-md flex items-center">
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        Vectorized
                      </span>
                    )}
                    <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 border border-indigo-100/50 px-2.5 py-1 rounded-md">
                      92% Match
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* RAG Context Panel (Right 1 col) */}
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
          <h4 className="font-bold text-slate-800 text-sm mb-3">AI Context Configuration</h4>
          <p className="text-xs text-slate-400 leading-normal mb-6">
            The vector search algorithm (FAISS) matches semantic sections from selected documents to feed directly to the generator context window.
          </p>

          <div className="space-y-4 border-t border-slate-100 pt-5">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500 font-semibold">Selected Context Docs:</span>
              <span className="font-bold text-slate-800">{selectedDocs.length} Documents</span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500 font-semibold">Estimated Context Tokens:</span>
              <span className="font-bold text-emerald-600">~14,200 (Within limits)</span>
            </div>

            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-500 font-semibold">Similarity Threshold:</span>
              <span className="font-bold text-slate-800">&gt; 0.65 Cosine</span>
            </div>
          </div>
        </div>

        {/* Generate Button Container */}
        <div className="bg-gradient-to-br from-indigo-900 to-indigo-950 rounded-3xl p-6 shadow-xl border border-indigo-950 text-white space-y-4">
          <div className="inline-flex items-center space-x-2 bg-indigo-500/25 text-indigo-300 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider">
            <Sparkles className="w-3 h-3 mr-1.5 animate-spin" />
            RAG Pipeline Armed
          </div>
          <h4 className="font-bold text-white text-base">Generate Initial Draft</h4>
          <p className="text-xs text-slate-300 leading-normal">
            The AI engine will draft structured specifications, eligibility rules, commercial milestones, and validation checklist flags.
          </p>
          <button 
            onClick={handleGenerateDraft}
            disabled={isGenerating || selectedDocs.length === 0}
            className="w-full bg-white text-indigo-900 font-bold py-3.5 rounded-xl hover:bg-slate-100 transition-colors shadow-lg flex items-center justify-center cursor-pointer disabled:bg-slate-300 disabled:text-slate-500 active:scale-[0.98]"
          >
            {isGenerating ? "Synthesizing Tender..." : "Generate Draft Tender"}
            <ChevronRight className="w-4 h-4 ml-1.5" />
          </button>
        </div>
      </div>

    </div>
  );
};

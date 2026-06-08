import React, { useState } from "react";
import { useStore } from "@/store/useStore";
import { Sparkles, ArrowRight, ShieldAlert, CheckCircle2, ChevronRight, HelpCircle } from "lucide-react";

export const RequirementsView: React.FC = () => {
  const { createRequirement, setActiveTab } = useStore();
  const [loading, setLoading] = useState(false);

  // Form states
  const [title, setTitle] = useState("Supply, Installation and Commissioning of Enterprise Workflow Management System");
  const [department, setDepartment] = useState("Contracts & Procurement");
  const [procurementType, setProcurementType] = useState("Service Contracting");
  const [tenderMode, setTenderMode] = useState("Open Tender Enquiry");
  const [category, setCategory] = useState("IT Services");
  const [scope, setScope] = useState(
    "We require annual maintenance contract, implementation, and configurations support for the SAIL enterprise automation workspace. The vendor should provide SLA-backed software patch deployments, user training support, and API connection bridges."
  );
  const [estimatedValue, setEstimatedValue] = useState<number>(1250000);
  const [deliveryPeriod, setDeliveryPeriod] = useState("120 Days from PO");
  const [location, setLocation] = useState("Lumbini Data Center, Bhairahawa");
  const [priority, setPriority] = useState("high");
  const [instructions, setInstructions] = useState("Follow public procurement norms. Need high standard eligibility clauses.");

  // Calculate dynamic readiness score based on filled inputs
  const calculateReadiness = () => {
    let score = 0;
    const missing = [];

    if (title.trim().length > 10) score += 15;
    else missing.push("Title is too short");

    if (scope.trim().length > 100) score += 30;
    else if (scope.trim().length > 20) score += 15;
    else missing.push("Scope of work is too thin (need min 100 chars)");

    if (estimatedValue > 0) score += 15;
    else missing.push("Estimated value/budget missing");

    if (deliveryPeriod.trim().length > 0) score += 10;
    else missing.push("Delivery timeline unspecified");

    if (location.trim().length > 0) score += 10;
    else missing.push("Delivery location unspecified");

    if (category) score += 10;
    if (procurementType) score += 10;

    return { score, missing };
  };

  const { score: readinessScore, missing: missingList } = calculateReadiness();

  const getReadinessLevel = (s: number) => {
    if (s >= 80) return { label: "High AI Confidence", color: "text-emerald-500", bg: "bg-emerald-50", progress: "bg-emerald-500" };
    if (s >= 50) return { label: "Medium AI Readiness", color: "text-amber-500", bg: "bg-amber-50", progress: "bg-amber-500" };
    return { label: "Low AI Readiness", color: "text-rose-500", bg: "bg-rose-50", progress: "bg-rose-500" };
  };

  const readiness = getReadinessLevel(readinessScore);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await createRequirement({
        title,
        department,
        procurement_type: procurementType,
        tender_mode: tenderMode,
        category,
        scope,
        estimated_value: estimatedValue,
        delivery_period: deliveryPeriod,
        location,
        priority,
        additional_instructions: instructions,
        completeness_score: readinessScore,
        ai_confidence: readinessScore >= 75 ? "High" : readinessScore >= 50 ? "Medium" : "Low",
        missing_inputs: missingList,
        suggested_action: readinessScore < 75 
          ? "Add more scope details to increase context match probability."
          : "Ready to proceed. Select matching historical tenders in next step.",
      });

      // Switch to Reference Library tab
      setActiveTab("references");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Input Form Column (Left 2 cols) */}
      <form onSubmit={handleSubmit} className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-5">
          <h3 className="text-lg font-bold text-slate-800">Procurement Intake Form</h3>
          <p className="text-xs text-slate-400 mt-1">Capture basic project metadata to start generating structured tender specifications</p>
        </div>

        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Tender Title</label>
            <input 
              type="text" 
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="e.g. Annual Support for IT Automation Platform"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Department */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">User Department</label>
              <input 
                type="text" 
                required
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. IT Department"
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Category</label>
              <select 
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                <option value="IT Services">IT Services</option>
                <option value="Capital Procurement">Capital Procurement</option>
                <option value="Goods & Services">Goods & Services</option>
                <option value="Mechanical Equipment">Mechanical Equipment</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Procurement Type */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Procurement Type</label>
              <select 
                value={procurementType}
                onChange={(e) => setProcurementType(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                <option value="Service Contracting">Service Contracting</option>
                <option value="Capital Procurement">Capital Procurement</option>
                <option value="Goods & Services">Goods & Services</option>
              </select>
            </div>

            {/* Tender Mode */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Tender Mode</label>
              <input 
                type="text" 
                required
                value={tenderMode}
                onChange={(e) => setTenderMode(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. Open Tender Enquiry"
              />
            </div>
          </div>

          {/* Scope of Work */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Detailed Scope of Work</label>
            <textarea 
              rows={5}
              required
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-sans leading-relaxed"
              placeholder="Provide a comprehensive technical description of the required product, scope, delivery parameters and expectations..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Estimated Value */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Estimated Value (INR)</label>
              <input 
                type="number" 
                required
                value={estimatedValue}
                onChange={(e) => setEstimatedValue(Number(e.target.value))}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. 100000"
              />
            </div>

            {/* Delivery Period */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Delivery Period</label>
              <input 
                type="text" 
                required
                value={deliveryPeriod}
                onChange={(e) => setDeliveryPeriod(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. 90 Days from PO"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Location */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Delivery Location</label>
              <input 
                type="text" 
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. Bhairahawa site"
              />
            </div>

            {/* Priority */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Priority</label>
              <select 
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>
            </div>
          </div>

          {/* Special Instructions */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Special Instructions / Directives</label>
            <textarea 
              rows={2}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="e.g. Require safety standard JHA audits..."
            />
          </div>
        </div>

        <div className="flex justify-end pt-4">
          <button 
            type="submit" 
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-6 py-3.5 rounded-xl shadow-lg shadow-indigo-600/20 flex items-center cursor-pointer transition-all active:scale-[0.98]"
          >
            {loading ? "Saving..." : "Analyze & Continue"}
            <ArrowRight className="w-4 h-4 ml-2" />
          </button>
        </div>
      </form>

      {/* AI Readiness Sidebar (Right 1 col) */}
      <div className="space-y-6">
        {/* Score Panel */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm flex flex-col items-center text-center">
          <h4 className="font-bold text-slate-800 text-sm mb-4">AI Readiness score</h4>
          
          {/* Radial Ring mock */}
          <div className="relative w-36 h-36 flex items-center justify-center mb-4">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="72"
                cy="72"
                r="64"
                stroke="#F1F5F9"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                cx="72"
                cy="72"
                r="64"
                stroke="#4F46E5"
                strokeWidth="10"
                fill="transparent"
                strokeDasharray="402"
                strokeDashoffset={402 - (402 * readinessScore) / 100}
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-extrabold text-slate-800">{readinessScore}%</span>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Ready</span>
            </div>
          </div>

          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${readiness.bg} ${readiness.color} mb-4`}>
            <Sparkles className="w-3.5 h-3.5 mr-1.5 animate-pulse" />
            {readiness.label}
          </div>

          <p className="text-xs text-slate-400 leading-normal">
            Calculated by analyzing document completeness, scope vocabulary weight, and required financial constraints.
          </p>
        </div>

        {/* Action Panel Warnings */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm">
          <h4 className="font-bold text-slate-800 text-sm mb-4 flex items-center">
            <ShieldAlert className="w-4 h-4 mr-2 text-rose-500" />
            Missing Inputs Checklist
          </h4>
          
          <div className="space-y-3">
            {missingList.length === 0 ? (
              <div className="flex items-center space-x-2 text-xs text-emerald-600 bg-emerald-50 border border-emerald-100 p-3 rounded-xl font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>All parameters entered! The AI model has sufficient context.</span>
              </div>
            ) : (
              missingList.map((item, idx) => (
                <div key={idx} className="flex items-start space-x-2 text-xs text-slate-500 bg-slate-50 border border-slate-100 p-2.5 rounded-xl">
                  <div className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

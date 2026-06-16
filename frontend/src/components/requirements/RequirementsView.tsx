import React, { useState } from "react";
import { useStore } from "@/store/useStore";
import { ArrowRight } from "lucide-react";

const COMPANIES = [
  "SAIL",
  "NTPC",
  "ONGC",
  "IOCL",
  "NMDC",
  "BANK OF BARODA",
  "BoB",
  "Bihar Govt",
  "CG Govt",
  "ECIL",
  "Gujrat Govt",
  "INDIA POST",
  "Integral Coach Factory",
  "ITI Limited",
  "Karnataka Govt",
  "MH Govt",
  "MP Government",
  "OCAC",
  "Rajisthan Govt",
  "Sagarmala Finance Corporation Limited",
  "SPPU"
];

const PROCUREMENT_TYPES = [
  "Service Contracting",
  "Capital Procurement",
  "Goods & Services",
  "Service Procurement",
  "Solution Implementation",
  "All"
];

export const RequirementsView: React.FC = () => {
  const { createRequirement, setActiveTab } = useStore();
  const [loading, setLoading] = useState(false);

  // Form states
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("SAIL");
  const [procurementType, setProcurementType] = useState("Service Contracting");
  const [tenderMode, setTenderMode] = useState("Open Tender Enquiry");
  const [category, setCategory] = useState("");
  const [scope, setScope] = useState("");
  const [estimatedValue, setEstimatedValue] = useState<number | "">("");
  const [deliveryPeriod, setDeliveryPeriod] = useState("");
  const [location, setLocation] = useState("");
  const [priority, setPriority] = useState("medium");
  const [instructions, setInstructions] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await createRequirement({
        title,
        department,
        procurement_type: procurementType,
        tender_mode: tenderMode || "Open Tender Enquiry",
        category: category || "IT Services",
        scope: scope || title,
        estimated_value: estimatedValue === "" ? 0 : Number(estimatedValue),
        delivery_period: deliveryPeriod || "Not Specified",
        location: location || "Not Specified",
        priority,
        additional_instructions: instructions || "",
        completeness_score: 100,
        ai_confidence: "High",
        missing_inputs: [],
        suggested_action: "Ready to proceed. Select matching historical tenders in next step.",
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
    <div className="max-w-4xl mx-auto w-full animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Input Form Column */}
      <form onSubmit={handleSubmit} className="w-full bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="border-b border-slate-100 pb-5">
          <h3 className="text-lg font-bold text-slate-800">Procurement Intake Form</h3>
          <p className="text-xs text-slate-400 mt-1">Capture basic project metadata to start generating structured tender specifications</p>
        </div>

        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Tender Title <span className="text-rose-500">*</span>
            </label>
            <input 
              type="text" 
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              placeholder="e.g. Supply of Alumina Magnesia Spinel Bricks for SMS-II Ladle"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* User Department / Company */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">User Department / Company</label>
              <select 
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                {COMPANIES.map((company) => (
                  <option key={company} value={company}>
                    {company}
                  </option>
                ))}
              </select>
            </div>

            {/* Category */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Category</label>
              <select 
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                <option value="">None</option>
                <option value="IT Services">IT Services</option>
                <option value="Capital Procurement">Capital Procurement</option>
                <option value="Goods & Services">Goods & Services</option>
                <option value="Mechanical Equipment">Mechanical Equipment</option>
                <option value="Refractory">Refractory</option>
                <option value="Electrical">Electrical</option>
                <option value="Civil">Civil</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Procurement Type */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Procurement Type <span className="text-rose-500">*</span>
              </label>
              <select 
                required
                value={procurementType}
                onChange={(e) => setProcurementType(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                {PROCUREMENT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Tender Mode */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Tender Mode</label>
              <input 
                type="text" 
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
                value={estimatedValue}
                onChange={(e) => setEstimatedValue(e.target.value === "" ? "" : Number(e.target.value))}
                className="w-full px-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="e.g. 100000"
              />
            </div>

            {/* Delivery Period */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Delivery Period</label>
              <input 
                type="text" 
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

    </div>
  );
};

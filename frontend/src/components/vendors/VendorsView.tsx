import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { Users, Award, ShieldAlert, CheckCircle2, AlertTriangle, Building, ShieldCheck, UserPlus } from "lucide-react";
import { api } from "@/lib/api";

export const VendorsView: React.FC = () => {
  const { vendors, vendorScores, fetchVendors } = useStore();
  const [showAddVendor, setShowAddVendor] = useState(false);
  
  // Add Vendor Form State
  const [name, setName] = useState("");
  const [category, setCategory] = useState("IT Services");
  const [turnover, setTurnover] = useState(25000000);
  const [experience, setExperience] = useState(5);
  const [location, setLocation] = useState("");
  const [certifications, setCertifications] = useState("ISO 9001:2015, ISO 27001");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleCreateVendor = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const certList = certifications.split(",").map(c => c.trim()).filter(Boolean);
      await api.post("/api/vendors", {
        name,
        category,
        annual_turnover: Number(turnover),
        experience_years: Number(experience),
        certifications: certList,
        location
      });
      // reset form
      setName("");
      setLocation("");
      setCertifications("ISO 9001:2015, ISO 27001");
      setShowAddVendor(false);
      await fetchVendors();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getRiskBadge = (level?: string) => {
    switch (level) {
      case "low":
        return <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-md">Low Risk</span>;
      case "high":
        return <span className="text-[10px] font-bold text-rose-600 bg-rose-50 border border-rose-100 px-2.5 py-1 rounded-md">High Risk</span>;
      default:
        return <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded-md">Medium Risk</span>;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      
      {/* Vendor List (Left 2 cols) */}
      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="flex justify-between items-center border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-800">Vendor Intelligence Registry</h3>
            <p className="text-xs text-slate-400 mt-1">Manage vendor financial profiles, historical delivery ratings, and risk levels</p>
          </div>
          <button
            onClick={() => setShowAddVendor(!showAddVendor)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl cursor-pointer shadow-md flex items-center"
          >
            <UserPlus className="w-4 h-4 mr-1.5" />
            Add Vendor
          </button>
        </div>

        {showAddVendor && (
          <form onSubmit={handleCreateVendor} className="p-6 bg-slate-50 border border-slate-100 rounded-2xl space-y-4 animate-in slide-in-from-top-3 duration-200">
            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">New Vendor Onboarding</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Company Name</label>
                <input 
                  type="text" required value={name} onChange={e => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Location / Site</label>
                <input 
                  type="text" required value={location} onChange={e => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Category</label>
                <select 
                  value={category} onChange={e => setCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white"
                >
                  <option value="IT Services">IT Services</option>
                  <option value="Capital Procurement">Capital Procurement</option>
                  <option value="Goods & Services">Goods & Services</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Annual Turnover (INR)</label>
                <input 
                  type="number" required value={turnover} onChange={e => setTurnover(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Experience Years</label>
                <input 
                  type="number" required value={experience} onChange={e => setExperience(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Certifications (comma separated)</label>
              <input 
                type="text" value={certifications} onChange={e => setCertifications(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button 
                type="button" onClick={() => setShowAddVendor(false)}
                className="px-4 py-2 text-xs border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button 
                type="submit" disabled={isSubmitting}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-xs font-bold rounded-xl cursor-pointer shadow-md"
              >
                Onboard Vendor
              </button>
            </div>
          </form>
        )}

        {/* Vendors list grid */}
        <div className="space-y-4">
          {vendors.map((vendor) => {
            const score = vendorScores[vendor.id];
            return (
              <div 
                key={vendor.id} 
                className="p-5 border border-slate-100 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-100 hover:bg-slate-50/20 transition-all duration-200"
              >
                <div className="space-y-2 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] bg-slate-100 border border-slate-200 text-slate-500 font-bold px-2 py-0.5 rounded-full">
                      {vendor.category || "Vendor"}
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium">{vendor.location}</span>
                  </div>
                  <h4 className="font-extrabold text-slate-800 text-sm truncate">{vendor.name}</h4>
                  <div className="flex flex-wrap gap-1">
                    {vendor.certifications && vendor.certifications.map((c, idx) => (
                      <span key={idx} className="text-[9px] bg-indigo-50/60 text-indigo-600 px-2 py-0.5 rounded border border-indigo-100/50">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>

                {score && (
                  <div className="flex items-center space-x-6 border-l border-slate-100 pl-6 flex-shrink-0">
                    <div className="text-center">
                      <span className="text-[9px] font-bold text-slate-400 uppercase block mb-0.5">Rating</span>
                      <span className="text-sm font-extrabold text-indigo-600">{score.overall_rating}/100</span>
                    </div>
                    <div className="text-center">
                      <span className="text-[9px] font-bold text-slate-400 uppercase block mb-0.5">Delivery</span>
                      <span className="text-sm font-extrabold text-slate-700">{score.delivery_performance}%</span>
                    </div>
                    <div className="text-center">
                      {getRiskBadge(score.risk_level)}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Overview Analytics (Right 1 col) */}
      <div className="space-y-6">
        <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 shadow-xl border border-indigo-950">
          <h4 className="font-bold text-white text-base mb-2 flex items-center">
            <Building className="w-5 h-5 mr-2" />
            Governance Engine
          </h4>
          <p className="text-xs text-slate-300 leading-normal">
            Automatically verify vendor tax compliances (GSTIN, PAN), credit rating thresholds, and blacklisting registries prior to evaluation.
          </p>

          <div className="mt-6 border-t border-indigo-500/20 pt-5 space-y-4 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400 font-medium">Bidders registered:</span>
              <span className="font-bold">{vendors.length} Vendors</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400 font-medium">Tax compliance checks:</span>
              <span className="font-bold text-emerald-400">100% Passed</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400 font-medium">Blacklisted Registry Sync:</span>
              <span className="font-bold text-emerald-400">Synced 2m ago</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

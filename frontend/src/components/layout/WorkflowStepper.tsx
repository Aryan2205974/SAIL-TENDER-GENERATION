import React from "react";
import { useStore } from "@/store/useStore";
import { Check, ClipboardList, BookOpen, PenTool, ClipboardCheck, Send } from "lucide-react";

export const WorkflowStepper: React.FC = () => {
  const { activeTab, setActiveTab } = useStore();

  const steps = [
    { id: "requirements", label: "Requirement Intake", icon: ClipboardList, stepNumber: 1 },
    { id: "references", label: "Reference Library", icon: BookOpen, stepNumber: 2 },
    { id: "drafting", label: "AI Drafting Workbench", icon: PenTool, stepNumber: 3 },
    { id: "review", label: "Checklist & Export", icon: ClipboardCheck, stepNumber: 4 },
    { id: "workflow", label: "Review & Approvals", icon: Send, stepNumber: 5 },
  ];

  // Helper to determine step status index
  const getStepIndex = (tab: string) => {
    return steps.findIndex(s => s.id === tab);
  };

  const activeIndex = getStepIndex(activeTab);

  // If the active tab is not part of the 5-step workflow (e.g. dashboard, vendors, evaluations, reports)
  // we do not render the stepper.
  if (activeIndex === -1) {
    return null;
  }

  return (
    <div className="w-full bg-white border-b border-slate-200 py-5 px-8 shadow-sm">
      <div className="max-w-4xl mx-auto flex items-center justify-between relative">
        {/* Progress connecting line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-200 -translate-y-1/2 z-0" />
        
        {/* Colored progress line */}
        <div 
          className="absolute top-1/2 left-0 h-0.5 bg-indigo-600 -translate-y-1/2 z-0 transition-all duration-500" 
          style={{ width: `${(activeIndex / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((step, idx) => {
          const StepIcon = step.icon;
          const isCompleted = idx < activeIndex;
          const isActive = idx === activeIndex;
          const isPending = idx > activeIndex;

          return (
            <button
              key={step.id}
              onClick={() => setActiveTab(step.id)}
              className="flex flex-col items-center relative z-10 focus:outline-none cursor-pointer group"
            >
              {/* Step bubble */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 shadow-md ${
                  isCompleted
                    ? "bg-indigo-600 border-indigo-600 text-white hover:bg-indigo-700 hover:border-indigo-700"
                    : isActive
                    ? "bg-white border-indigo-600 text-indigo-600 ring-4 ring-indigo-100"
                    : "bg-white border-slate-300 text-slate-400 hover:border-slate-400"
                }`}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5 font-bold" />
                ) : (
                  <StepIcon className="w-4 h-4" />
                )}
              </div>

              {/* Step info labels */}
              <div className="absolute top-12 whitespace-nowrap flex flex-col items-center">
                <span 
                  className={`text-[10px] font-bold tracking-wider uppercase ${
                    isActive ? "text-indigo-600" : "text-slate-400"
                  }`}
                >
                  Step {step.stepNumber}
                </span>
                <span
                  className={`text-xs font-semibold mt-0.5 transition-colors duration-200 ${
                    isActive ? "text-slate-800 font-bold" : "text-slate-500 group-hover:text-slate-700"
                  }`}
                >
                  {step.label}
                </span>
              </div>
            </button>
          );
        })}
      </div>
      {/* Spacer to balance the absolute labels below */}
      <div className="h-8"></div>
    </div>
  );
};

import React from "react";
import { useStore } from "@/store/useStore";
import {
  LayoutDashboard,
  FileText,
  Library,
  PenTool,
  ClipboardCheck,
  GitMerge,
  Users,
  Award,
  BarChart3,
  LogOut,
  UserCheck
} from "lucide-react";

interface SidebarProps {
  onNavigate?: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNavigate }) => {
  const { activeTab, setActiveTab, user, logout } = useStore();

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "requirements", label: "Requirement Intake", icon: FileText },
    { id: "references", label: "Reference Library", icon: Library },
    { id: "drafting", label: "AI Drafting Workbench", icon: PenTool },
    { id: "review", label: "Review & Checklist", icon: ClipboardCheck },
    { id: "workflow", label: "Workflow & Approvals", icon: GitMerge },
    { id: "vendors", label: "Vendor Intelligence", icon: Users },
    { id: "evaluation", label: "Bid Evaluation", icon: Award },
    { id: "reports", label: "Reports & Analytics", icon: BarChart3 },
  ];

  const handleNav = (id: string) => {
    setActiveTab(id);
    if (onNavigate) onNavigate(id);
  };

  return (
    <div className="w-72 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3 bg-slate-950/40">
        <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30 ring-2 ring-indigo-400/20">
          <span className="font-extrabold text-white text-lg">S</span>
        </div>
        <div>
          <h1 className="font-bold text-white text-base leading-tight">SAIL Procurement</h1>
          <span className="text-xs text-indigo-400 font-semibold tracking-wider uppercase">AI Platform</span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto custom-scrollbar">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`w-full flex items-center px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 group relative ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-400 border-l-4 border-indigo-500 pl-3 bg-gradient-to-r from-indigo-900/10 to-transparent"
                  : "hover:bg-slate-800/60 hover:text-white"
              }`}
            >
              <Icon
                className={`w-5 h-5 mr-3 transition-transform duration-200 group-hover:scale-110 ${
                  isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-200"
                }`}
              />
              {item.label}
              
              {isActive && (
                <span className="absolute right-3 w-1.5 h-1.5 rounded-full bg-indigo-400 shadow-lg shadow-indigo-400/50"></span>
              )}
            </button>
          );
        })}
      </nav>

      {/* User Footer Profile */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/20">
        {user ? (
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/40 border border-slate-800/60">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-md">
                {user.avatar_initials || "AK"}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-white truncate max-w-[120px]">{user.name}</span>
                <span className="text-xs text-slate-400 truncate max-w-[120px] capitalize">{user.role.replace("_", " ")}</span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
              title="Logout"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-3 p-2 text-slate-400">
            <UserCheck className="w-5 h-5" />
            <span className="text-sm">Demo Mode Active</span>
          </div>
        )}
      </div>
    </div>
  );
};

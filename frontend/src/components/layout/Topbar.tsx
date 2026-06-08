import React, { useState, useEffect } from "react";
import { useStore } from "@/store/useStore";
import { Bell, RefreshCw, CheckCircle2, AlertTriangle, Info, ShieldAlert } from "lucide-react";

export const Topbar: React.FC = () => {
  const {
    activeTab,
    notifications,
    fetchNotifications,
    markNotificationRead,
    user
  } = useStore();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchNotifications();
    setIsRefreshing(false);
  };

  const unreadNotifications = notifications.filter(n => !n.is_read);

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case "error":
        return <ShieldAlert className="w-5 h-5 text-rose-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case "dashboard":
        return "Dashboard Overview";
      case "requirements":
        return "Step 1: Requirement Intake & AI Readiness";
      case "references":
        return "Step 2: Reference Library & Context Integration";
      case "drafting":
        return "Step 3: AI Drafting Workbench";
      case "review":
        return "Step 4: Checklist & Export Workbench";
      case "workflow":
        return "Step 5: Review Workflow & Approvals";
      case "vendors":
        return "Vendor Intelligence & Risk Analysis";
      case "evaluation":
        return "Technical & Commercial Bid Evaluation";
      case "reports":
        return "Reports & Governance Analytics";
      default:
        return "Procurement Platform";
    }
  };

  return (
    <header className="h-20 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-40 shadow-sm">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">{getPageTitle()}</h2>
        <p className="text-xs text-slate-400 mt-0.5">SAIL Procurement Intelligence Platform</p>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-6">
        {/* Refresh button */}
        <button
          onClick={handleRefresh}
          className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-xl transition-all duration-200"
          title="Refresh Data"
        >
          <RefreshCw className={`w-5 h-5 ${isRefreshing ? "animate-spin text-indigo-600" : ""}`} />
        </button>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded-xl transition-all duration-200 relative cursor-pointer"
          >
            <Bell className="w-5 h-5" />
            {unreadNotifications.length > 0 && (
              <span className="absolute top-1.5 right-1.5 w-5 h-5 bg-rose-500 text-white rounded-full flex items-center justify-center text-[10px] font-bold ring-2 ring-white animate-pulse">
                {unreadNotifications.length}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl z-50 overflow-hidden ring-1 ring-black/5 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
                <h4 className="font-semibold text-slate-800 text-sm">Notifications</h4>
                {unreadNotifications.length > 0 && (
                  <span className="text-[11px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full font-bold">
                    {unreadNotifications.length} New
                  </span>
                )}
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-50">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-slate-400 text-xs">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => markNotificationRead(notif.id)}
                      className={`p-4 hover:bg-slate-50 transition-colors cursor-pointer flex space-x-3 ${
                        !notif.is_read ? "bg-indigo-50/20" : ""
                      }`}
                    >
                      <div className="flex-shrink-0 mt-0.5">
                        {getNotificationIcon(notif.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-slate-800 truncate">{notif.title}</p>
                        <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{notif.message}</p>
                        <span className="text-[9px] text-slate-400 mt-1 block">
                          {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Department Badge */}
        {user && (
          <div className="flex items-center space-x-2 border-l border-slate-200 pl-6">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-100 px-2.5 py-1.5 rounded-lg border border-slate-200">
              {user.department || "Admin"}
            </span>
          </div>
        )}
      </div>
    </header>
  );
};

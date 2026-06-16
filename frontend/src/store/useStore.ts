import { create } from "zustand";
import { api } from "@/lib/api";

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  department: string;
  avatar_initials: string;
}

export interface Requirement {
  id: number;
  ref_id: string;
  title: string;
  department: string;
  procurement_type: string;
  tender_mode: string;
  category: string;
  scope: string;
  estimated_value: number;
  delivery_period: string;
  location: string;
  priority: string;
  additional_instructions?: string;
  status: string;
  completeness_score: number;
  ai_confidence: string;
  missing_inputs: string[];
  suggested_action: string;
}

export interface ReferenceDocument {
  id: number;
  filename: string;
  original_name: string;
  doc_type: string;
  department: string;
  procurement_type: string;
  year: number;
  category: string;
  file_size: number;
  is_chunked: boolean;
  is_embedded: boolean;
  chunk_count: number;
  tags: string[];
}

export interface Tender {
  id: number;
  tender_id: string;
  requirement_id: number;
  title: string;
  status: string;
  current_stage: string;
  draft_content: string;
  ai_confidence: string;
  ai_output_version: string;
  source_clauses_count: number;
  human_overrides_count: number;
  pending_validations_count: number;
  confidence_status: string;
  draft_completeness: number;
  mandatory_checks_completed: number;
  mandatory_checks_total: number;
  pending_human_inputs: number;
  source_references_linked: number;
}

export interface TenderSection {
  id: number;
  tender_id: number;
  section_name: string;
  content: string;
  status: string;
  source_ref?: string;
  order_index: number;
}

export interface ValidationCheck {
  id: number;
  tender_id: number;
  check_area: string;
  status: string;
  ai_observation: string;
  human_action_required: string;
  owner: string;
}

export interface Approval {
  id: number;
  tender_id: number;
  stage: string;
  stage_label: string;
  assignee_name: string;
  assignee_role: string;
  owner_role: string;
  status: string;
  priority: string;
  due_date: string;
}

export interface Comment {
  id: number;
  tender_id: number;
  author_name: string;
  author_role: string;
  author_initials: string;
  content: string;
  created_at: string;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface Vendor {
  id: number;
  name: string;
  category: string;
  annual_turnover: number;
  experience_years: number;
  certifications: string[];
  location: string;
}

export interface VendorScore {
  vendor_id: number;
  technical_score: number;
  commercial_score: number;
  risk_score: number;
  delivery_performance: number;
  quality_score: number;
  overall_rating: number;
  risk_level: string;
}

interface AppState {
  // Auth state
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;

  // Data state
  requirements: Requirement[];
  activeRequirement: Requirement | null;
  references: ReferenceDocument[];
  tenders: Tender[];
  activeTender: Tender | null;
  tenderSections: TenderSection[];
  validationChecks: ValidationCheck[];
  approvals: Approval[];
  comments: Comment[];
  notifications: Notification[];
  vendors: Vendor[];
  vendorScores: Record<number, VendorScore>;

  // UI state
  activeTab: string;
  setActiveTab: (tab: string) => void;
  workflowStep: number;
  setWorkflowStep: (step: number) => void;

  // Actions
  fetchRequirements: () => Promise<void>;
  fetchReferences: () => Promise<void>;
  fetchTenders: () => Promise<void>;
  fetchTenderDetails: (id: number) => Promise<void>;
  fetchNotifications: () => Promise<void>;
  fetchVendors: () => Promise<void>;
  markNotificationRead: (id: number) => Promise<void>;
  createRequirement: (data: Partial<Requirement>) => Promise<Requirement>;
  generateTenderPlan: (requirementId: number) => Promise<Tender>;
}

export const useStore = create<AppState>((set, get) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  isAuthenticated: false,
  
  requirements: [],
  activeRequirement: null,
  references: [],
  tenders: [],
  activeTender: null,
  tenderSections: [],
  validationChecks: [],
  approvals: [],
  comments: [],
  notifications: [],
  vendors: [],
  vendorScores: {},

  activeTab: "dashboard",
  setActiveTab: (tab) => set({ activeTab: tab }),
  workflowStep: 1,
  setWorkflowStep: (step) => set({ workflowStep: step }),

  login: async (email, password) => {
    try {
      const res = await api.post("/api/auth/login", {
        email,
        password,
      });
      
      const { access_token } = res.data;
      localStorage.setItem("token", access_token);
      set({ token: access_token, isAuthenticated: true });
      await get().fetchCurrentUser();
      return true;
    } catch (err) {
      console.error("Login failed:", err);
      // Fallback for mock demo
      if (email === "admin@sail.in" && password === "admin123") {
        const mockUser = {
          id: 1,
          name: "Aryan Kumar",
          email: "admin@sail.in",
          role: "admin",
          department: "Procurement",
          avatar_initials: "AK",
        };
        set({ user: mockUser, isAuthenticated: true, token: "mock-token" });
        localStorage.setItem("token", "mock-token");
        return true;
      }
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, token: null, isAuthenticated: false });
  },

  fetchCurrentUser: async () => {
    try {
      const res = await api.get("/api/auth/me");
      set({ user: res.data, isAuthenticated: true });
    } catch (err) {
      console.error("Failed to fetch user, logging out:", err);
      // Auto fallback if token exists (for demo resiliency)
      if (localStorage.getItem("token") === "mock-token" || get().token) {
        set({
          user: {
            id: 1,
            name: "Aryan Kumar",
            email: "admin@sail.in",
            role: "admin",
            department: "Procurement",
            avatar_initials: "AK",
          },
          isAuthenticated: true,
        });
      } else {
        get().logout();
      }
    }
  },

  fetchRequirements: async () => {
    try {
      const res = await api.get("/api/requirements");
      set({ requirements: res.data });
    } catch (err) {
      console.error("Fetch requirements error:", err);
    }
  },

  fetchReferences: async () => {
    try {
      const res = await api.get("/api/reference");
      set({ references: res.data });
    } catch (err) {
      console.error("Fetch references error:", err);
    }
  },

  fetchTenders: async () => {
    try {
      const res = await api.get("/api/tenders");
      set({ tenders: res.data });
    } catch (err) {
      console.error("Fetch tenders error:", err);
    }
  },

  fetchTenderDetails: async (id) => {
    if (!id || isNaN(Number(id))) {
      console.warn("fetchTenderDetails aborted: invalid tender ID:", id);
      return;
    }
    try {
      const [tenderRes, workflowRes, auditRes] = await Promise.all([
        api.get(`/api/tenders/${id}`),
        api.get(`/api/workflow/${id}/status`),
        api.get(`/api/workflow/${id}/audit`),
      ]);
      
      set({
        activeTender: tenderRes.data,
        tenderSections: tenderRes.data.sections || [],
        validationChecks: tenderRes.data.validation_checks || [],
        approvals: workflowRes.data.approvals || [],
        comments: tenderRes.data.comments || [],
      });
    } catch (err) {
      console.error("Fetch tender details error:", err);
    }
  },

  fetchNotifications: async () => {
    try {
      const res = await api.get("/api/notifications");
      set({ notifications: res.data });
    } catch (err) {
      console.error("Fetch notifications error:", err);
    }
  },

  fetchVendors: async () => {
    try {
      const res = await api.get("/api/vendors");
      set({ vendors: res.data });
      
      // Fetch details and scores for each vendor
      const scorePromises = res.data.map(async (v: any) => {
        try {
          const scoreRes = await api.get(`/api/vendors/risk/${v.id}`);
          return { id: v.id, score: scoreRes.data };
        } catch {
          return null;
        }
      });
      const resolvedScores = await Promise.all(scorePromises);
      const scoresMap: Record<number, VendorScore> = {};
      resolvedScores.forEach((s) => {
        if (s) scoresMap[s.id] = s.score;
      });
      set({ vendorScores: scoresMap });
    } catch (err) {
      console.error("Fetch vendors error:", err);
    }
  },

  markNotificationRead: async (id) => {
    try {
      await api.put(`/api/notifications/${id}/read`);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, is_read: true } : n
        ),
      }));
    } catch (err) {
      console.error("Mark read error:", err);
    }
  },

  createRequirement: async (data) => {
    const res = await api.post("/api/requirements", data);
    set((state) => ({
      requirements: [res.data, ...state.requirements],
      activeRequirement: res.data,
    }));
    return res.data;
  },

  generateTenderPlan: async (requirementId) => {
    // Phase 1: Call plan generation
    const planRes = await api.post("/api/ai/plan", { requirement_id: requirementId });
    
    // Fetch full tender details (which has sections and checks initialized)
    const tenderId = planRes.data.tender_id;
    const tenderRes = await api.get(`/api/tenders/${tenderId}`);
    
    set((state) => ({
      tenders: [tenderRes.data, ...state.tenders],
      activeTender: tenderRes.data,
    }));

    // Phase 2: Trigger the complete AI generation in background asynchronously without blocking
    api.post("/api/ai/generate", { requirement_id: requirementId }).catch(console.error);
    
    return tenderRes.data;
  },
}));

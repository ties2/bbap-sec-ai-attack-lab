import { useState, useEffect, useCallback } from "react";
import {
  Shield, ShieldCheck, ShieldAlert, Activity, Users, BookOpen, Bell, Settings,
  ChevronRight, Plus, Trash2, Edit3, Search, Filter, Check, X, AlertTriangle,
  Lock, Unlock, Eye, EyeOff, Database, Cpu, FileText, Layers, BarChart3,
  ArrowRight, Clock, Mail, UserPlus, Key, Globe, Server, Zap, TrendingUp,
  CheckCircle2, XCircle, AlertCircle, Info, ChevronDown, LayoutDashboard
} from "lucide-react";

// ── State Management ──
const useStore = () => {
  const [users, setUsers] = useState([
    { id: 1, name: "Admin User", email: "admin@bbap-sec.io", role: "admin", status: "active", lastLogin: "2026-05-05T10:30:00", mfa: true },
    { id: 2, name: "Sarah Chen", email: "s.chen@bbap-sec.io", role: "analyst", status: "active", lastLogin: "2026-05-05T09:15:00", mfa: true },
    { id: 3, name: "Marcus Rivera", email: "m.rivera@bbap-sec.io", role: "viewer", status: "active", lastLogin: "2026-05-04T14:20:00", mfa: false },
    { id: 4, name: "Aisha Patel", email: "a.patel@bbap-sec.io", role: "analyst", status: "suspended", lastLogin: "2026-04-28T08:00:00", mfa: true },
  ]);
  const [notes, setNotes] = useState([
    { id: 1, title: "OWASP LLM Top 10 — Key Takeaways", content: "LLM01 Prompt Injection remains the top risk. Our pipeline covers direct and indirect injection via the Simulate module. Need to add output validation for LLM02 (Sensitive Info Disclosure).", tags: ["owasp", "llm", "priority"], created: "2026-05-03", pinned: true },
    { id: 2, title: "Adversarial Training Results — MNIST", content: "FGSM at epsilon=0.03 drops accuracy from 98.5% to 42.1%. After adversarial training (mix_ratio=0.5), adversarial accuracy improved to 78.3% with only 2.1% clean accuracy loss. PGD-40 results pending.", tags: ["adversarial", "results"], created: "2026-05-04", pinned: false },
    { id: 3, title: "MITRE ATLAS Coverage Gap Analysis", content: "Current coverage: 8/16 tactics (50%). Missing: Reconnaissance, Initial Access, Impact, ML Supply Chain Compromise. Priority: add supply chain attack module for next sprint.", tags: ["atlas", "roadmap"], created: "2026-05-05", pinned: true },
  ]);
  const [alerts, setAlerts] = useState([
    { id: 1, severity: "critical", title: "Backdoor trigger detected in training batch", timestamp: "2026-05-05T11:02:00", source: "Data Ingestion", acknowledged: false },
    { id: 2, severity: "high", title: "API query rate exceeded threshold (1200/min)", timestamp: "2026-05-05T10:45:00", source: "API Security", acknowledged: false },
    { id: 3, severity: "medium", title: "Model drift detected: accuracy dropped 3.2%", timestamp: "2026-05-05T09:30:00", source: "Monitoring", acknowledged: true },
    { id: 4, severity: "low", title: "New user registration pending approval", timestamp: "2026-05-05T08:15:00", source: "User Management", acknowledged: true },
    { id: 5, severity: "high", title: "Prompt injection attempt blocked (indirect)", timestamp: "2026-05-05T07:50:00", source: "Prompt Filtering", acknowledged: true },
  ]);
  return { users, setUsers, notes, setNotes, alerts, setAlerts };
};

// ── Glassmorphism Styles ──
const glass = "bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]";
const glassHover = "hover:bg-white/[0.07] hover:border-white/[0.12] transition-all duration-200";
const glassStrong = "bg-white/[0.06] backdrop-blur-xl border border-white/[0.1]";

// ── Severity Styles ──
const sevStyles = {
  critical: { bg: "bg-red-500/10", border: "border-red-500/20", text: "text-red-400", dot: "bg-red-400" },
  high: { bg: "bg-orange-500/10", border: "border-orange-500/20", text: "text-orange-400", dot: "bg-orange-400" },
  medium: { bg: "bg-amber-500/10", border: "border-amber-500/20", text: "text-amber-400", dot: "bg-amber-400" },
  low: { bg: "bg-blue-500/10", border: "border-blue-500/20", text: "text-blue-400", dot: "bg-blue-400" },
};

// ── Pipeline Stage Data ──
const PIPELINE_STAGES = [
  { id: "ingest", label: "Data Ingestion", icon: Database, status: "secured", checks: 12, passed: 11, items: ["Schema validation", "Poison sample detection", "Source authentication", "Integrity hashing", "Outlier detection", "Format verification", "Volume anomaly check", "PII scanning", "Label consistency", "Duplicate detection", "Provenance tracking", "Encryption at rest"] },
  { id: "validate", label: "Model Validation", icon: Cpu, status: "warning", checks: 8, passed: 6, items: ["Architecture review", "Weight integrity check", "Adversarial robustness test", "Bias evaluation", "Performance benchmarking", "Backdoor scanning", "Supply chain audit", "Version control"] },
  { id: "prompt", label: "Prompt Filtering", icon: Filter, status: "secured", checks: 10, passed: 10, items: ["Input sanitization", "Injection pattern detection", "Encoding bypass prevention", "Delimiter enforcement", "Role boundary validation", "Context isolation", "Token limit enforcement", "Language detection", "Intent classification", "Output guardrails"] },
  { id: "api", label: "API Security", icon: Globe, status: "secured", checks: 9, passed: 9, items: ["Authentication (OAuth2/JWT)", "Rate limiting", "Query logging", "IP allowlisting", "Output truncation", "CORS policy", "TLS enforcement", "Input schema validation", "Response watermarking"] },
  { id: "monitor", label: "Monitoring & Logging", icon: Activity, status: "active", checks: 7, passed: 7, items: ["Query pattern analysis", "Output anomaly detection", "Model drift tracking", "Latency monitoring", "Error rate alerting", "Audit trail", "Real-time dashboarding"] },
];

const SECURITY_CONTROLS = [
  { category: "Input Security", items: ["Input Validation", "Prompt Filtering", "Sanitization", "Encoding Detection"], status: "active" },
  { category: "Output Security", items: ["Output Filtering", "Sensitive Data Detection", "Guardrails", "Response Truncation"], status: "active" },
  { category: "Model Security", items: ["Model Validation", "Adversarial Training", "Watermarking", "Access Control"], status: "partial" },
  { category: "Data & Infra", items: ["Encryption", "Access Control", "Data Masking", "Network Isolation"], status: "active" },
];

// ── Components ──

function Sidebar({ page, setPage, alertCount }) {
  const nav = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "pipeline", label: "Secure Pipeline", icon: Layers },
    { id: "controls", label: "Security Controls", icon: ShieldCheck },
    { id: "monitoring", label: "Monitoring", icon: Activity },
    { id: "users", label: "User Management", icon: Users },
    { id: "knowledge", label: "Knowledge Base", icon: BookOpen },
    { id: "alerts", label: "Alerts", icon: Bell, badge: alertCount },
    { id: "settings", label: "Settings", icon: Settings },
  ];
  return (
    <aside className="w-[220px] flex-shrink-0 h-screen flex flex-col border-r border-white/[0.06] bg-white/[0.02]">
      <div className="p-5 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-emerald-600 to-emerald-400 flex items-center justify-center font-mono text-xs font-bold text-white">B</div>
          <div>
            <div className="text-sm font-semibold text-white tracking-tight">BBAP-Sec</div>
            <div className="text-[9px] text-white/30 uppercase tracking-[0.2em]">AI Security</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        {nav.map(n => (
          <button key={n.id} onClick={() => setPage(n.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-[12px] font-medium transition-all duration-150 ${page === n.id ? "bg-emerald-500/12 text-emerald-400 border border-emerald-500/20" : "text-white/50 hover:text-white/80 hover:bg-white/[0.04] border border-transparent"}`}>
            <n.icon size={15} strokeWidth={1.8} />
            <span className="flex-1 text-left">{n.label}</span>
            {n.badge > 0 && <span className="text-[9px] font-mono bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{n.badge}</span>}
          </button>
        ))}
      </nav>
      <div className="p-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-white/[0.08] flex items-center justify-center text-[10px] font-medium text-white/60">A</div>
          <div className="flex-1 min-w-0">
            <div className="text-[11px] text-white/70 truncate">Admin User</div>
            <div className="text-[9px] text-white/30 font-mono">admin</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatCard({ label, value, sub, icon: Icon, color = "emerald" }) {
  const colors = { emerald: "text-emerald-400", amber: "text-amber-400", red: "text-red-400", blue: "text-blue-400", copper: "text-orange-300" };
  return (
    <div className={`${glass} rounded-lg p-4`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-8 h-8 rounded-md ${color === "red" ? "bg-red-500/10" : color === "amber" ? "bg-amber-500/10" : color === "blue" ? "bg-blue-500/10" : "bg-emerald-500/10"} flex items-center justify-center`}>
          <Icon size={15} className={colors[color]} strokeWidth={1.8} />
        </div>
      </div>
      <div className={`text-2xl font-semibold ${colors[color]} mb-0.5`}>{value}</div>
      <div className="text-[11px] text-white/40">{label}</div>
      {sub && <div className="text-[10px] text-white/25 mt-1 font-mono">{sub}</div>}
    </div>
  );
}

// ── Pages ──

function DashboardPage({ alerts }) {
  const unack = alerts.filter(a => !a.acknowledged).length;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Security Overview</h1>
        <p className="text-sm text-white/40">Real-time status of your AI security posture</p>
      </div>
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Pipeline Health" value="94%" sub="46/49 checks passed" icon={ShieldCheck} color="emerald" />
        <StatCard label="Active Alerts" value={unack} sub={`${alerts.length} total`} icon={AlertTriangle} color={unack > 0 ? "red" : "emerald"} />
        <StatCard label="ATLAS Coverage" value="50%" sub="8 of 16 tactics" icon={Shield} color="amber" />
        <StatCard label="Users Active" value="3" sub="4 total accounts" icon={Users} color="blue" />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className={`${glass} rounded-lg p-5 col-span-2`}>
          <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-4">Secure AI Pipeline Status</div>
          <div className="flex items-center gap-2">
            {PIPELINE_STAGES.map((s, i) => (
              <div key={s.id} className="flex items-center gap-2 flex-1">
                <div className={`flex-1 ${glassStrong} rounded-md p-3`}>
                  <div className="flex items-center gap-2 mb-2">
                    <s.icon size={13} className={s.status === "secured" ? "text-emerald-400" : s.status === "warning" ? "text-amber-400" : "text-blue-400"} strokeWidth={1.8} />
                    <span className="text-[10px] font-medium text-white/70">{s.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${s.status === "secured" ? "bg-emerald-500" : s.status === "warning" ? "bg-amber-500" : "bg-blue-500"}`} style={{ width: `${(s.passed / s.checks) * 100}%` }} />
                    </div>
                    <span className="text-[9px] font-mono text-white/40">{s.passed}/{s.checks}</span>
                  </div>
                </div>
                {i < PIPELINE_STAGES.length - 1 && <ChevronRight size={12} className="text-white/15 flex-shrink-0" />}
              </div>
            ))}
          </div>
        </div>

        <div className={`${glass} rounded-lg p-5`}>
          <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-3">Recent Alerts</div>
          <div className="space-y-2">
            {alerts.slice(0, 4).map(a => {
              const s = sevStyles[a.severity];
              return (
                <div key={a.id} className={`${s.bg} border ${s.border} rounded-md px-3 py-2`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                    <span className="text-[10px] text-white/70 flex-1 truncate">{a.title}</span>
                  </div>
                  <div className="text-[9px] text-white/30 font-mono mt-1">{a.source}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className={`${glass} rounded-lg p-5`}>
        <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-4">Security Controls Status</div>
        <div className="grid grid-cols-4 gap-3">
          {SECURITY_CONTROLS.map(c => (
            <div key={c.category} className={`${glassStrong} rounded-md p-4`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-semibold text-white/80">{c.category}</span>
                <span className={`text-[9px] font-mono px-2 py-0.5 rounded ${c.status === "active" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                  {c.status}
                </span>
              </div>
              <div className="space-y-1.5">
                {c.items.map(item => (
                  <div key={item} className="flex items-center gap-2 text-[10px] text-white/50">
                    <CheckCircle2 size={10} className="text-emerald-500/60" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PipelinePage() {
  const [expanded, setExpanded] = useState(null);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Secure AI Pipeline</h1>
        <p className="text-sm text-white/40">Five-stage architecture following AI security best practices</p>
      </div>
      <div className="flex items-center gap-3 mb-2">
        {PIPELINE_STAGES.map((s, i) => (
          <div key={s.id} className="flex items-center gap-3 flex-1">
            <div className={`flex-1 text-center py-2 px-3 rounded-md border cursor-default ${s.status === "secured" ? "bg-emerald-500/8 border-emerald-500/20" : s.status === "warning" ? "bg-amber-500/8 border-amber-500/20" : "bg-blue-500/8 border-blue-500/20"}`}>
              <div className="text-[10px] font-mono text-white/40 mb-0.5">Stage {i + 1}</div>
              <div className="text-[11px] font-medium text-white/80">{s.label}</div>
            </div>
            {i < PIPELINE_STAGES.length - 1 && <ArrowRight size={14} className="text-white/15 flex-shrink-0" />}
          </div>
        ))}
      </div>
      <div className="space-y-3">
        {PIPELINE_STAGES.map(stage => (
          <div key={stage.id} className={`${glass} rounded-lg overflow-hidden`}>
            <button onClick={() => setExpanded(expanded === stage.id ? null : stage.id)}
              className="w-full flex items-center gap-4 p-5 text-left hover:bg-white/[0.02] transition-colors">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${stage.status === "secured" ? "bg-emerald-500/10" : stage.status === "warning" ? "bg-amber-500/10" : "bg-blue-500/10"}`}>
                <stage.icon size={18} className={stage.status === "secured" ? "text-emerald-400" : stage.status === "warning" ? "text-amber-400" : "text-blue-400"} strokeWidth={1.5} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-white/90">{stage.label}</div>
                <div className="text-[11px] text-white/40">{stage.passed} of {stage.checks} checks passed</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-24 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${stage.status === "secured" ? "bg-emerald-500" : "bg-amber-500"}`} style={{ width: `${(stage.passed / stage.checks) * 100}%` }} />
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${stage.status === "secured" ? "bg-emerald-500/10 text-emerald-400" : stage.status === "warning" ? "bg-amber-500/10 text-amber-400" : "bg-blue-500/10 text-blue-400"}`}>
                  {stage.status}
                </span>
                <ChevronDown size={14} className={`text-white/30 transition-transform ${expanded === stage.id ? "rotate-180" : ""}`} />
              </div>
            </button>
            {expanded === stage.id && (
              <div className="px-5 pb-5 border-t border-white/[0.04]">
                <div className="grid grid-cols-3 gap-2 pt-4">
                  {stage.items.map((item, idx) => (
                    <div key={idx} className={`flex items-center gap-2 px-3 py-2 rounded-md ${idx < stage.passed ? "bg-emerald-500/[0.05]" : "bg-red-500/[0.05]"}`}>
                      {idx < stage.passed ? <CheckCircle2 size={12} className="text-emerald-500/70" /> : <XCircle size={12} className="text-red-400/70" />}
                      <span className="text-[11px] text-white/60">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ControlsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Security Controls</h1>
        <p className="text-sm text-white/40">Input, output, model, and infrastructure security layers</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {SECURITY_CONTROLS.map(ctrl => (
          <div key={ctrl.category} className={`${glass} rounded-lg p-5`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white/90">{ctrl.category}</h3>
              <span className={`text-[9px] font-mono uppercase tracking-wider px-2 py-1 rounded ${ctrl.status === "active" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>{ctrl.status}</span>
            </div>
            <div className="space-y-2">
              {ctrl.items.map(item => (
                <div key={item} className={`${glassStrong} rounded-md px-4 py-3 flex items-center justify-between`}>
                  <div className="flex items-center gap-3">
                    <CheckCircle2 size={13} className="text-emerald-500/60" />
                    <span className="text-[12px] text-white/70">{item}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono text-emerald-400/60 bg-emerald-500/8 px-2 py-0.5 rounded">enabled</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MonitoringPage() {
  const metrics = [
    { label: "Queries / min", value: "842", trend: "+12%", status: "normal" },
    { label: "Avg Latency", value: "45ms", trend: "-3ms", status: "normal" },
    { label: "Error Rate", value: "0.02%", trend: "stable", status: "normal" },
    { label: "Blocked Requests", value: "23", trend: "+5 today", status: "warning" },
    { label: "Model Accuracy", value: "97.8%", trend: "-0.3%", status: "normal" },
    { label: "Drift Score", value: "0.04", trend: "below threshold", status: "normal" },
  ];
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Monitoring & Logging</h1>
        <p className="text-sm text-white/40">Real-time system metrics, query patterns, and anomaly detection</p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {metrics.map(m => (
          <div key={m.label} className={`${glass} rounded-lg p-4`}>
            <div className="text-[10px] text-white/35 uppercase tracking-wider mb-2">{m.label}</div>
            <div className="text-xl font-semibold text-white/90 mb-1">{m.value}</div>
            <div className={`text-[10px] font-mono ${m.status === "warning" ? "text-amber-400" : "text-white/30"}`}>{m.trend}</div>
          </div>
        ))}
      </div>
      <div className={`${glass} rounded-lg p-5`}>
        <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-4">Activity Log</div>
        <div className="space-y-1.5">
          {[
            { time: "11:02:14", event: "Backdoor pattern detected in batch #4721", level: "error" },
            { time: "10:58:30", event: "Rate limit triggered for client 192.168.1.45", level: "warn" },
            { time: "10:45:22", event: "Model validation completed — 6/8 checks passed", level: "warn" },
            { time: "10:30:01", event: "Prompt injection attempt blocked (base64 encoding)", level: "info" },
            { time: "10:15:44", event: "Data ingestion pipeline completed — 12,000 samples validated", level: "info" },
            { time: "09:30:00", event: "Drift detection: accuracy delta -3.2% from baseline", level: "warn" },
            { time: "09:00:00", event: "Scheduled security scan completed — all clear", level: "info" },
          ].map((log, i) => (
            <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded-md ${log.level === "error" ? "bg-red-500/[0.04]" : log.level === "warn" ? "bg-amber-500/[0.04]" : "bg-white/[0.02]"}`}>
              <span className="text-[10px] font-mono text-white/25 w-14 flex-shrink-0">{log.time}</span>
              <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${log.level === "error" ? "bg-red-400" : log.level === "warn" ? "bg-amber-400" : "bg-white/20"}`} />
              <span className="text-[11px] text-white/60">{log.event}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function UsersPage({ users, setUsers }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", role: "viewer" });
  const [editId, setEditId] = useState(null);

  const roles = { admin: "bg-red-500/10 text-red-400 border-red-500/20", analyst: "bg-blue-500/10 text-blue-400 border-blue-500/20", viewer: "bg-white/[0.06] text-white/50 border-white/10" };

  const handleSave = () => {
    if (!form.name || !form.email) return;
    if (editId) {
      setUsers(users.map(u => u.id === editId ? { ...u, ...form } : u));
      setEditId(null);
    } else {
      setUsers([...users, { id: Date.now(), ...form, status: "active", lastLogin: new Date().toISOString(), mfa: false }]);
    }
    setForm({ name: "", email: "", role: "viewer" });
    setShowForm(false);
  };

  const startEdit = (u) => { setForm({ name: u.name, email: u.email, role: u.role }); setEditId(u.id); setShowForm(true); };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">User Management</h1>
          <p className="text-sm text-white/40">Manage access, roles, and authentication</p>
        </div>
        <button onClick={() => { setShowForm(!showForm); setEditId(null); setForm({ name: "", email: "", role: "viewer" }); }}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30 transition-colors">
          <UserPlus size={13} /> Add User
        </button>
      </div>
      {showForm && (
        <div className={`${glass} rounded-lg p-5`}>
          <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-4">{editId ? "Edit User" : "New User"}</div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-[10px] text-white/40 block mb-1">Full Name</label>
              <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] font-mono focus:outline-none focus:border-emerald-500/30" />
            </div>
            <div>
              <label className="text-[10px] text-white/40 block mb-1">Email</label>
              <input value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] font-mono focus:outline-none focus:border-emerald-500/30" />
            </div>
            <div>
              <label className="text-[10px] text-white/40 block mb-1">Role</label>
              <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] focus:outline-none focus:border-emerald-500/30">
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleSave} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 transition-colors">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px] hover:bg-white/[0.08] transition-colors">Cancel</button>
          </div>
        </div>
      )}
      <div className={`${glass} rounded-lg overflow-hidden`}>
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/[0.06]">
              {["User", "Email", "Role", "Status", "MFA", "Last Login", "Actions"].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[9px] font-semibold text-white/30 uppercase tracking-[0.15em]">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-white/[0.06] flex items-center justify-center text-[10px] font-medium text-white/50">{u.name.split(" ").map(n => n[0]).join("")}</div>
                    <span className="text-[12px] text-white/80">{u.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-[11px] text-white/50 font-mono">{u.email}</td>
                <td className="px-4 py-3"><span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${roles[u.role]}`}>{u.role}</span></td>
                <td className="px-4 py-3"><span className={`text-[9px] font-mono ${u.status === "active" ? "text-emerald-400" : "text-red-400"}`}>{u.status}</span></td>
                <td className="px-4 py-3">{u.mfa ? <Lock size={12} className="text-emerald-500/60" /> : <Unlock size={12} className="text-white/20" />}</td>
                <td className="px-4 py-3 text-[10px] text-white/30 font-mono">{new Date(u.lastLogin).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    <button onClick={() => startEdit(u)} className="p-1.5 rounded hover:bg-white/[0.06] text-white/30 hover:text-white/60 transition-colors"><Edit3 size={12} /></button>
                    <button onClick={() => setUsers(users.filter(x => x.id !== u.id))} className="p-1.5 rounded hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-colors"><Trash2 size={12} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KnowledgePage({ notes, setNotes }) {
  const [showEditor, setShowEditor] = useState(false);
  const [editNote, setEditNote] = useState({ title: "", content: "", tags: "" });
  const [editId, setEditId] = useState(null);
  const [search, setSearch] = useState("");

  const save = () => {
    if (!editNote.title) return;
    const tagArr = editNote.tags.split(",").map(t => t.trim()).filter(Boolean);
    if (editId) {
      setNotes(notes.map(n => n.id === editId ? { ...n, title: editNote.title, content: editNote.content, tags: tagArr } : n));
    } else {
      setNotes([{ id: Date.now(), title: editNote.title, content: editNote.content, tags: tagArr, created: new Date().toISOString().split("T")[0], pinned: false }, ...notes]);
    }
    setShowEditor(false); setEditNote({ title: "", content: "", tags: "" }); setEditId(null);
  };

  const startEdit = (n) => { setEditNote({ title: n.title, content: n.content, tags: n.tags.join(", ") }); setEditId(n.id); setShowEditor(true); };
  const togglePin = (id) => setNotes(notes.map(n => n.id === id ? { ...n, pinned: !n.pinned } : n));

  const filtered = notes.filter(n => !search || n.title.toLowerCase().includes(search.toLowerCase()) || n.content.toLowerCase().includes(search.toLowerCase()) || n.tags.some(t => t.toLowerCase().includes(search.toLowerCase())));
  const sorted = [...filtered].sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">Knowledge Base</h1>
          <p className="text-sm text-white/40">Notes, findings, and research documentation</p>
        </div>
        <button onClick={() => { setShowEditor(true); setEditId(null); setEditNote({ title: "", content: "", tags: "" }); }}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30 transition-colors">
          <Plus size={13} /> New Note
        </button>
      </div>
      <div className="flex gap-3">
        <div className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-md ${glass}`}>
          <Search size={13} className="text-white/25" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search notes, tags..." className="flex-1 bg-transparent text-[12px] text-white/70 focus:outline-none placeholder:text-white/20" />
        </div>
      </div>
      {showEditor && (
        <div className={`${glass} rounded-lg p-5`}>
          <input value={editNote.title} onChange={e => setEditNote({ ...editNote, title: e.target.value })} placeholder="Note title..." className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-sm font-medium mb-3 focus:outline-none focus:border-emerald-500/30" />
          <textarea value={editNote.content} onChange={e => setEditNote({ ...editNote, content: e.target.value })} placeholder="Write your note... (supports plain text)" rows={6} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[12px] leading-relaxed mb-3 focus:outline-none focus:border-emerald-500/30 resize-none font-mono" />
          <input value={editNote.tags} onChange={e => setEditNote({ ...editNote, tags: e.target.value })} placeholder="Tags (comma-separated): owasp, adversarial, roadmap" className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono mb-3 focus:outline-none focus:border-emerald-500/30" />
          <div className="flex gap-2">
            <button onClick={save} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500">Save</button>
            <button onClick={() => setShowEditor(false)} className="px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px] hover:bg-white/[0.08]">Cancel</button>
          </div>
        </div>
      )}
      <div className="space-y-3">
        {sorted.map(n => (
          <div key={n.id} className={`${glass} rounded-lg p-5 ${n.pinned ? "border-l-2 border-l-emerald-500/40" : ""}`}>
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {n.pinned && <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                <h3 className="text-sm font-medium text-white/90">{n.title}</h3>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => togglePin(n.id)} className={`p-1.5 rounded hover:bg-white/[0.06] transition-colors ${n.pinned ? "text-emerald-400" : "text-white/20"}`}>
                  <BookOpen size={11} />
                </button>
                <button onClick={() => startEdit(n)} className="p-1.5 rounded hover:bg-white/[0.06] text-white/25 hover:text-white/60"><Edit3 size={11} /></button>
                <button onClick={() => setNotes(notes.filter(x => x.id !== n.id))} className="p-1.5 rounded hover:bg-red-500/10 text-white/15 hover:text-red-400"><Trash2 size={11} /></button>
              </div>
            </div>
            <p className="text-[12px] text-white/50 leading-relaxed mb-3 whitespace-pre-wrap">{n.content}</p>
            <div className="flex items-center justify-between">
              <div className="flex gap-1.5">
                {n.tags.map(t => (
                  <span key={t} className="text-[9px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-white/35 border border-white/[0.06]">{t}</span>
                ))}
              </div>
              <span className="text-[9px] font-mono text-white/20">{n.created}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AlertsPage({ alerts, setAlerts }) {
  const ack = (id) => setAlerts(alerts.map(a => a.id === id ? { ...a, acknowledged: true } : a));
  const ackAll = () => setAlerts(alerts.map(a => ({ ...a, acknowledged: true })));
  const unack = alerts.filter(a => !a.acknowledged).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">Alerts & Notifications</h1>
          <p className="text-sm text-white/40">{unack} unacknowledged alert{unack !== 1 ? "s" : ""}</p>
        </div>
        {unack > 0 && (
          <button onClick={ackAll} className="flex items-center gap-2 px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px] hover:bg-white/[0.08] transition-colors">
            <Check size={13} /> Acknowledge All
          </button>
        )}
      </div>
      <div className={`${glass} rounded-lg p-5`}>
        <div className="text-[10px] font-semibold text-white/30 uppercase tracking-[0.15em] mb-3">Email Notification Settings</div>
        <div className="grid grid-cols-2 gap-3">
          {["Critical alerts", "High severity alerts", "Daily digest", "Weekly summary"].map((label, i) => (
            <div key={label} className={`${glassStrong} rounded-md px-4 py-3 flex items-center justify-between`}>
              <div className="flex items-center gap-3">
                <Mail size={13} className="text-white/30" />
                <span className="text-[11px] text-white/60">{label}</span>
              </div>
              <div className={`w-8 h-4 rounded-full relative cursor-pointer transition-colors ${i < 2 ? "bg-emerald-500/30" : "bg-white/[0.08]"}`}>
                <div className={`w-3 h-3 rounded-full absolute top-0.5 transition-all ${i < 2 ? "right-0.5 bg-emerald-400" : "left-0.5 bg-white/30"}`} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        {alerts.map(a => {
          const s = sevStyles[a.severity];
          return (
            <div key={a.id} className={`${glass} rounded-lg px-5 py-4 flex items-center gap-4 ${a.acknowledged ? "opacity-50" : ""}`}>
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
              <div className="flex-1 min-w-0">
                <div className="text-[12px] text-white/80 mb-0.5">{a.title}</div>
                <div className="flex items-center gap-3 text-[9px] font-mono text-white/30">
                  <span>{a.source}</span>
                  <span>{new Date(a.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
              <span className={`text-[9px] font-mono px-2 py-0.5 rounded ${s.bg} ${s.text} border ${s.border}`}>{a.severity}</span>
              {!a.acknowledged && (
                <button onClick={() => ack(a.id)} className="px-3 py-1.5 rounded-md bg-white/[0.04] text-white/40 text-[10px] hover:bg-white/[0.08] hover:text-white/60 transition-colors">Acknowledge</button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white mb-1">Settings</h1>
        <p className="text-sm text-white/40">System configuration and administration</p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {[
          { title: "API Configuration", desc: "Manage API keys, rate limits, and access tokens", icon: Key },
          { title: "Email / SMTP", desc: "Configure email notifications and alert delivery", icon: Mail },
          { title: "Authentication", desc: "SSO, OAuth, MFA policies and session management", icon: Lock },
          { title: "Integrations", desc: "Connect to SIEM, ticketing, and monitoring tools", icon: Zap },
          { title: "Backup & Recovery", desc: "Database backups, export settings, disaster recovery", icon: Database },
          { title: "Audit Log", desc: "System-wide audit trail and access history", icon: FileText },
        ].map(s => (
          <div key={s.title} className={`${glass} rounded-lg p-5 ${glassHover} cursor-pointer`}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-lg bg-white/[0.04] flex items-center justify-center">
                <s.icon size={16} className="text-white/40" strokeWidth={1.5} />
              </div>
              <div>
                <div className="text-[13px] font-medium text-white/80">{s.title}</div>
                <div className="text-[10px] text-white/35">{s.desc}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main App ──

export default function App() {
  const [page, setPage] = useState("dashboard");
  const store = useStore();
  const unackAlerts = store.alerts.filter(a => !a.acknowledged).length;

  const pages = {
    dashboard: <DashboardPage alerts={store.alerts} />,
    pipeline: <PipelinePage />,
    controls: <ControlsPage />,
    monitoring: <MonitoringPage />,
    users: <UsersPage users={store.users} setUsers={store.setUsers} />,
    knowledge: <KnowledgePage notes={store.notes} setNotes={store.setNotes} />,
    alerts: <AlertsPage alerts={store.alerts} setAlerts={store.setAlerts} />,
    settings: <SettingsPage />,
  };

  return (
    <div className="flex h-screen bg-[#080b12] text-white overflow-hidden" style={{ fontFamily: "'DM Sans', system-ui, sans-serif" }}>
      <div className="fixed inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 60% 40% at 20% 10%, rgba(46,204,113,0.03), transparent), radial-gradient(ellipse 50% 50% at 80% 80%, rgba(184,115,51,0.02), transparent)" }} />
      <Sidebar page={page} setPage={setPage} alertCount={unackAlerts} />
      <main className="flex-1 overflow-y-auto relative z-10 p-6 pb-20">
        {pages[page]}
      </main>
    </div>
  );
}

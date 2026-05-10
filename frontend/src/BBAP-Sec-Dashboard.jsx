import { useState, useEffect } from "react";
import {
  Shield, ShieldCheck, ShieldAlert, ChevronRight, Plus, Search,
  Check, AlertTriangle, Lock, Database, Cpu, FileText, Layers, Filter,
  Globe, Zap, Download, ExternalLink, CheckCircle2, XCircle,
  ChevronDown, Play, Loader2, Target, Upload, Server, Terminal,
  MessageSquare, Eye, Bug, Box, Network, Radio, BarChart3,
  FileWarning, Unplug, Fingerprint, Brain, Workflow, ArrowRight,
  Settings, Users, BookOpen, Bell, Activity, Gauge,
  TrendingUp, TrendingDown, Minus
} from "lucide-react";

const G = "bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]";
const GS = "bg-white/[0.06] backdrop-blur-xl border border-white/[0.1]";

/* ── API helpers ── */
const API2 = "/api/v2";
const api = {
  get: u => fetch(API2+u).then(r=>r.json()),
  post: (u,b) => fetch(API2+u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>r.json()),
};
const atlas = { get: u => fetch("/api/atlas"+u).then(r=>r.json()) };

/* Module labels for ATLAS mapping (maps backend module keys → display names) */
const MOD_LABELS = {
  adversarial:"Adversarial", data_poisoning:"Data Poisoning", evasion:"Evasion",
  model_extraction:"Model Extraction", prompt_injection:"Prompt Injection"
};

/* ── COLOR SYSTEM ── */
const LAYER_META = {
  training:     { label: "Training Phase",    color: "#60a5fa", bg: "bg-blue-500/10",    bd: "border-blue-500/20",    tx: "text-blue-400",    icon: Brain,        tag: "TRN" },
  inference:    { label: "Inference Phase",   color: "#34d399", bg: "bg-emerald-500/10",  bd: "border-emerald-500/20",  tx: "text-emerald-400", icon: Zap,          tag: "INF" },
  artifacts:    { label: "Model Artifacts",   color: "#fb923c", bg: "bg-orange-500/10",   bd: "border-orange-500/20",   tx: "text-orange-400",  icon: Box,          tag: "ART" },
  pipeline:     { label: "Data Pipeline",     color: "#f87171", bg: "bg-red-500/10",      bd: "border-red-500/20",      tx: "text-red-400",     icon: Workflow,     tag: "DPL" },
  infra:        { label: "Infrastructure",    color: "#a78bfa", bg: "bg-violet-500/10",   bd: "border-violet-500/20",   tx: "text-violet-400",  icon: Server,       tag: "INF" },
  output:       { label: "Output Layer",      color: "#fbbf24", bg: "bg-amber-500/10",    bd: "border-amber-500/20",    tx: "text-amber-400",   icon: MessageSquare,tag: "OUT" },
};

const SEV = {
  critical: { bg: "bg-red-500/10",    bd: "border-red-500/20",    tx: "text-red-400",    dot: "bg-red-400"    },
  high:     { bg: "bg-orange-500/10",  bd: "border-orange-500/20",  tx: "text-orange-400",  dot: "bg-orange-400"  },
  medium:   { bg: "bg-amber-500/10",   bd: "border-amber-500/20",   tx: "text-amber-400",   dot: "bg-amber-400"   },
  low:      { bg: "bg-blue-500/10",    bd: "border-blue-500/20",    tx: "text-blue-400",    dot: "bg-blue-400"    },
  info:     { bg: "bg-white/[0.04]",   bd: "border-white/[0.08]",   tx: "text-white/40",    dot: "bg-white/20"    },
};

/* ── LAYER ATTACK DEFINITIONS ── */
const LAYER_ATTACKS = {
  training: [
    { id: "poison_label",   name: "Label-flip poisoning",     difficulty: "Intermediate", atlas: "AML.T0020.000", access: ["upload","registry"] },
    { id: "poison_backdoor", name: "Backdoor implant",        difficulty: "Advanced",     atlas: "AML.T0020.001", access: ["upload","registry"] },
    { id: "supply_chain",   name: "Supply chain compromise",  difficulty: "Advanced",     atlas: "AML.T0010",     access: ["registry"] },
    { id: "clean_label",    name: "Clean-label poisoning",    difficulty: "Expert",       atlas: "AML.T0020",     access: ["upload"] },
  ],
  inference: [
    { id: "fgsm",           name: "FGSM",                    difficulty: "Beginner",     atlas: "AML.T0043.001", access: ["upload"] },
    { id: "pgd",            name: "PGD",                     difficulty: "Intermediate", atlas: "AML.T0043.001", access: ["upload"] },
    { id: "evasion_pixel",  name: "Pixel perturbation",      difficulty: "Beginner",     atlas: "AML.T0047",     access: ["upload","api"] },
    { id: "evasion_noise",  name: "Gaussian noise",          difficulty: "Beginner",     atlas: "AML.T0047",     access: ["upload","api"] },
    { id: "evasion_spatial", name: "Spatial transform",      difficulty: "Intermediate", atlas: "AML.T0047.003", access: ["upload","api"] },
    { id: "model_inversion", name: "Model inversion",        difficulty: "Expert",       atlas: "AML.T0024",     access: ["api"] },
  ],
  artifacts: [
    { id: "extract_random", name: "Model extraction (random)",  difficulty: "Intermediate", atlas: "AML.T0044", access: ["api"] },
    { id: "extract_active", name: "Model extraction (active)",  difficulty: "Advanced",     atlas: "AML.T0044", access: ["api"] },
    { id: "weight_exfil",   name: "Weight exfiltration",        difficulty: "Advanced",     atlas: "AML.T0024", access: ["upload","registry"] },
    { id: "arch_reverse",   name: "Architecture reverse eng.",   difficulty: "Expert",       atlas: "AML.T0005", access: ["api"] },
  ],
  pipeline: [
    { id: "tainted_data",   name: "Tainted dataset injection",  difficulty: "Intermediate", atlas: "AML.T0020", access: ["upload","registry"] },
    { id: "label_corrupt",  name: "Label corruption",           difficulty: "Beginner",     atlas: "AML.T0020.000", access: ["upload","registry"] },
    { id: "scraping_abuse", name: "Scraping / API abuse",       difficulty: "Beginner",     atlas: null,             access: ["api"] },
    { id: "provenance_spoof", name: "Provenance spoofing",     difficulty: "Advanced",     atlas: "AML.T0010",     access: ["registry"] },
  ],
  infra: [
    { id: "rate_limit",     name: "Rate limit bypass",          difficulty: "Beginner",     atlas: "AML.T0005",     access: ["api"] },
    { id: "auth_bypass",    name: "Authentication bypass",      difficulty: "Intermediate", atlas: null,             access: ["api"] },
    { id: "registry_audit", name: "Registry access audit",      difficulty: "Intermediate", atlas: "AML.T0010",     access: ["registry"] },
    { id: "misconfig",      name: "Serving misconfiguration",   difficulty: "Intermediate", atlas: null,             access: ["api"] },
  ],
  output: [
    { id: "inject_direct",  name: "Direct prompt injection",    difficulty: "Beginner",     atlas: "AML.T0051.000", access: ["llm"] },
    { id: "inject_indirect", name: "Indirect injection",        difficulty: "Advanced",     atlas: "AML.T0051.001", access: ["llm"] },
    { id: "prompt_leak",    name: "System prompt leakage",      difficulty: "Intermediate", atlas: "AML.T0053",     access: ["llm"] },
    { id: "jailbreak",      name: "LLM jailbreak",              difficulty: "Intermediate", atlas: "AML.T0054",     access: ["llm"] },
    { id: "guardrail_bypass", name: "Output guardrail bypass",  difficulty: "Advanced",     atlas: null,             access: ["llm","api"] },
    { id: "hallucination",  name: "Hallucination probing",      difficulty: "Beginner",     atlas: null,             access: ["llm"] },
  ],
};

/* ── MOCK DATA ── */
const MOCK_ENGAGEMENTS = [
  { id: 1, name: "FinCorp Fraud Model", target_type: "api_endpoint",
    target_config: { url: "https://api.fincorp.internal/v2/fraud/predict", auth: "Bearer ••••••" },
    scope: ["training","inference","artifacts","infra","output"],
    status: "active", risk_score: 38 },
  { id: 2, name: "MedScan ResNet50", target_type: "model_upload",
    target_config: { framework: "pytorch", filename: "resnet50_medical.pt" },
    scope: ["training","inference","artifacts","pipeline"],
    status: "active", risk_score: 52 },
  { id: 3, name: "ChatBot v2 (GPT-4o)", target_type: "llm_endpoint",
    target_config: { provider: "OpenAI", model: "gpt-4o" },
    scope: ["output","infra"],
    status: "active", risk_score: 15 },
  { id: 4, name: "Credit Scoring XGB", target_type: "model_upload",
    target_config: { framework: "sklearn", filename: "credit_xgb.pkl" },
    scope: ["training","inference","pipeline"],
    status: "completed", risk_score: 8 },
];
const MOCK_SANDBOX = {
  id: 1, engagement_id: 2, status: "running", framework: "pytorch",
  filename: "resnet50_medical.pt", port: 5001, gpu: true, uptime: "2h 14m",
};
const MOCK_FINDINGS = [
  { id: "F-001", layer: "inference", attack: "fgsm", severity: "high", title: "FGSM drops accuracy 56% at ε=0.03", metrics: { accuracy_drop: 56.4, asr: 57.9 }, atlas: "AML.T0043.001", related: ["F-003"], status: "open" },
  { id: "F-002", layer: "output", attack: "inject_direct", severity: "critical", title: "Direct injection bypasses system prompt", metrics: { asr: 40, defended: 6, injected: 4 }, atlas: "AML.T0051.000", related: ["F-004"], status: "open" },
  { id: "F-003", layer: "infra", attack: "rate_limit", severity: "medium", title: "No rate limiting on /predict endpoint", metrics: { queries_before_block: "unlimited" }, atlas: "AML.T0005", related: ["F-001"], status: "in_progress" },
  { id: "F-004", layer: "output", attack: "prompt_leak", severity: "high", title: "System prompt leaked via fictional framing", metrics: { leaked_secrets: 2 }, atlas: "AML.T0053", related: ["F-002"], status: "open" },
  { id: "F-005", layer: "artifacts", attack: "extract_random", severity: "high", title: "Model cloned with 91% fidelity in 1000 queries", metrics: { fidelity: 91.4, queries: 1000 }, atlas: "AML.T0044", related: ["F-003"], status: "open" },
  { id: "F-006", layer: "training", attack: "poison_backdoor", severity: "critical", title: "Backdoor trigger achieves 94% ASR", metrics: { backdoor_asr: 94.2, poison_rate: 0.1 }, atlas: "AML.T0020.001", related: [], status: "open" },
];

/* ═══════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════ */
function Sidebar({ page, setPage, engagement, engagements, onSelectEngagement, onNewEngagement }) {
  const layers = Object.entries(LAYER_META);
  const findingsCount = MOCK_FINDINGS.filter(f => f.status === "open").length;
  const [engOpen, setEngOpen] = useState(false);

  const Section = ({ label, children }) => (
    <div className="mb-1">
      <div className="px-4 pt-3 pb-1 text-[8px] font-semibold tracking-[0.2em] uppercase text-white/15">{label}</div>
      {children}
    </div>
  );

  const NavBtn = ({ id, icon: Icon, label, badge, color }) => (
    <button onClick={() => setPage(id)} className={`w-full flex items-center gap-2.5 px-3 py-[7px] rounded-md text-[11px] font-medium transition-all ${page === id ? "bg-emerald-500/12 text-emerald-400 border border-emerald-500/20" : "text-white/45 hover:text-white/75 hover:bg-white/[0.03] border border-transparent"}`}>
      <Icon size={14} strokeWidth={1.8} style={color ? { color } : undefined} />
      <span className="flex-1 text-left">{label}</span>
      {badge > 0 && <span className="text-[8px] font-mono bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{badge}</span>}
    </button>
  );

  return (
    <aside className="w-[210px] shrink-0 h-screen flex flex-col border-r border-white/[0.06] bg-white/[0.015]">
      {/* Brand */}
      <div className="p-3.5 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-8 h-8 rounded-md bg-gradient-to-br from-emerald-600 to-emerald-400 flex items-center justify-center font-mono text-[10px] font-bold text-white">B</div>
          <div><div className="text-[12px] font-semibold text-white">BBAP-Sec</div><div className="text-[8px] text-white/25 uppercase tracking-[0.2em]">AI Pentest Platform</div></div>
        </div>

        {/* Engagement selector */}
        <div className="text-[8px] text-white/20 uppercase tracking-widest mb-1">Engagement</div>
        <div className="relative">
          <button onClick={() => setEngOpen(!engOpen)} className={`w-full px-2.5 py-1.5 rounded-md ${G} text-left flex items-center justify-between hover:border-white/[0.15] transition-colors`}>
            <span className="text-[10px] font-mono text-emerald-400/80 truncate">{engagement.name}</span>
            <ChevronDown size={11} className={`text-white/20 transition-transform ${engOpen ? "rotate-180" : ""}`} />
          </button>

          {engOpen && (
            <div className={`absolute left-0 right-0 top-full mt-1 rounded-md ${GS} shadow-xl z-50 overflow-hidden`}>
              {engagements.map(e => (
                <button key={e.id} onClick={() => { onSelectEngagement(e.id); setEngOpen(false); }}
                  className={`w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-white/[0.04] transition-colors ${e.id === engagement.id ? "bg-emerald-500/[0.06]" : ""}`}>
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${e.status === "active" ? "bg-emerald-400" : "bg-white/20"}`} />
                  <div className="flex-1 min-w-0">
                    <div className={`text-[10px] truncate ${e.id === engagement.id ? "text-emerald-400" : "text-white/60"}`}>{e.name}</div>
                    <div className="text-[8px] text-white/20">{e.target_type.replace("_"," ")}</div>
                  </div>
                </button>
              ))}
              <button onClick={() => { onNewEngagement(); setEngOpen(false); }}
                className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-white/[0.04] border-t border-white/[0.06]">
                <Plus size={11} className="text-emerald-400/60" />
                <span className="text-[10px] text-emerald-400/60">New Engagement</span>
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 mt-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${engagement.status === "active" ? "bg-emerald-400" : "bg-white/20"}`} />
          <span className="text-[9px] text-white/25">{engagement.target_type.replace("_"," ")}</span>
        </div>
      </div>

      <nav className="flex-1 py-1.5 px-2 overflow-y-auto">
        <NavBtn id="overview" icon={Activity} label="Overview" />
        <NavBtn id="target" icon={Unplug} label="Target Setup" />

        <Section label="Attack surfaces">
          {layers.map(([key, m]) => {
            const Icon = m.icon;
            return <NavBtn key={key} id={`layer_${key}`} icon={Icon} label={m.label} color={m.color} />;
          })}
        </Section>

        <Section label="Assessment">
          <NavBtn id="findings" icon={Bug} label="Findings" badge={findingsCount} />
          <NavBtn id="pipeline_checks" icon={Layers} label="Pipeline" />
          <NavBtn id="atlas" icon={Target} label="ATLAS Intel" />
          <NavBtn id="report" icon={BarChart3} label="Report Generator" />
        </Section>

        <Section label="AI risk management">
          <NavBtn id="governance" icon={ShieldCheck} label="Governance" />
          <NavBtn id="monitoring" icon={Gauge} label="Monitoring" />
        </Section>

        <Section label="Management">
          <NavBtn id="team" icon={Users} label="Team" />
          <NavBtn id="knowledge" icon={BookOpen} label="Knowledge Base" />
          <NavBtn id="alerts" icon={Bell} label="Alerts" />
          <NavBtn id="settings" icon={Settings} label="Settings" />
        </Section>
      </nav>
    </aside>
  );
}

/* ═══════════════════════════════════
   OVERVIEW PAGE
   ═══════════════════════════════════ */
function OverviewPage({ engagement }) {
  const layers = Object.entries(LAYER_META);
  const findingsByLayer = {};
  MOCK_FINDINGS.forEach(f => {
    findingsByLayer[f.layer] = (findingsByLayer[f.layer] || 0) + 1;
  });
  const critCount = MOCK_FINDINGS.filter(f => f.severity === "critical").length;
  const highCount = MOCK_FINDINGS.filter(f => f.severity === "high").length;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white mb-0.5">Engagement Overview</h1>
        <p className="text-sm text-white/35">{engagement.name} — {engagement.target_type.replace("_"," ")}</p>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { l: "Risk Score", v: engagement.risk_score + "/100", c: "text-amber-400", bg: "bg-amber-500/10", I: ShieldAlert },
          { l: "Findings", v: MOCK_FINDINGS.length, c: "text-orange-400", bg: "bg-orange-500/10", I: Bug },
          { l: "Critical", v: critCount, c: critCount > 0 ? "text-red-400" : "text-emerald-400", bg: critCount > 0 ? "bg-red-500/10" : "bg-emerald-500/10", I: AlertTriangle },
          { l: "High", v: highCount, c: "text-orange-300", bg: "bg-orange-500/10", I: FileWarning },
          { l: "Layers Tested", v: `${new Set(MOCK_FINDINGS.map(f=>f.layer)).size}/6`, c: "text-blue-400", bg: "bg-blue-500/10", I: Layers },
        ].map(x => (
          <div key={x.l} className={`${G} rounded-lg p-3.5`}>
            <div className={`w-7 h-7 rounded-md ${x.bg} flex items-center justify-center mb-2`}><x.I size={14} className={x.c} /></div>
            <div className={`text-xl font-semibold font-mono ${x.c}`}>{x.v}</div>
            <div className="text-[10px] text-white/35 mt-0.5">{x.l}</div>
          </div>
        ))}
      </div>

      {/* Attack Surface Health */}
      <div>
        <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Attack surface health</div>
        <div className="grid grid-cols-3 gap-3">
          {layers.map(([key, m]) => {
            const Icon = m.icon;
            const count = findingsByLayer[key] || 0;
            const inScope = engagement.scope?.includes(key);
            return (
              <div key={key} className={`${G} rounded-lg p-4 ${!inScope ? "opacity-30" : ""}`}>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-8 h-8 rounded-lg ${m.bg} border ${m.bd} flex items-center justify-center`}>
                    <Icon size={15} style={{ color: m.color }} />
                  </div>
                  <div className="flex-1">
                    <div className={`text-[12px] font-medium`} style={{ color: m.color }}>{m.label}</div>
                    <div className="text-[10px] text-white/30">{inScope ? `${count} findings` : "Out of scope"}</div>
                  </div>
                  {count > 0 && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${count > 2 ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>
                      {count}
                    </span>
                  )}
                </div>
                <div className="flex gap-1 flex-wrap">
                  {LAYER_ATTACKS[key]?.slice(0, 3).map(a => (
                    <span key={a.id} className="text-[8px] font-mono text-white/20 bg-white/[0.03] px-1.5 py-0.5 rounded">{a.name}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent critical findings */}
      <div>
        <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Critical & high findings</div>
        <div className="space-y-2">
          {MOCK_FINDINGS.filter(f => f.severity === "critical" || f.severity === "high").map(f => {
            const lm = LAYER_META[f.layer];
            const sv = SEV[f.severity];
            return (
              <div key={f.id} className={`${G} rounded-lg px-4 py-3 flex items-center gap-3`}>
                <div className={`w-2 h-2 rounded-full ${sv.dot}`} />
                <span className="text-[9px] font-mono text-white/25 w-12">{f.id}</span>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${lm.bg} border ${lm.bd}`} style={{ color: lm.color }}>{lm.label}</span>
                <span className="text-[11px] text-white/65 flex-1">{f.title}</span>
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${sv.bg} ${sv.tx} border ${sv.bd}`}>{f.severity}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   TARGET SETUP PAGE
   ═══════════════════════════════════ */
function TargetPage({ engagement }) {
  const [method, setMethod] = useState(engagement.target_type || "api_endpoint");
  const [file, setFile] = useState(null);
  const [framework, setFramework] = useState("pytorch");
  const [url, setUrl] = useState(engagement.target_config?.url || "");
  const [authHeaders, setAuthHeaders] = useState(engagement.target_config?.auth || "");
  const [inputShape, setInputShape] = useState("");
  const [provider, setProvider] = useState("Anthropic (Claude)");
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("");
  const [registryUrl, setRegistryUrl] = useState("");
  const [registryModelId, setRegistryModelId] = useState("");
  const [registryCreds, setRegistryCreds] = useState("");
  const [sandbox, setSandbox] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const fileInputRef = useState(null);

  const methods = [
    { id: "api_endpoint", label: "API Endpoint", icon: Globe, desc: "Test a deployed model via its REST API", sandbox: false },
    { id: "model_upload", label: "Model Upload", icon: Upload, desc: "Upload .pt/.onnx/.h5 into isolated sandbox", sandbox: true },
    { id: "registry",     label: "Registry",     icon: Database, desc: "Pull from MLflow, HuggingFace, S3", sandbox: true },
    { id: "llm_endpoint", label: "LLM Endpoint", icon: MessageSquare, desc: "Test LLM apps via API (OpenAI, Anthropic)", sandbox: false },
  ];
  const sel = methods.find(m => m.id === method);

  const handleFileSelect = (e) => {
    const f = e.target.files?.[0];
    if (f) { setFile(f); setError(null); }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) { setFile(f); setError(null); }
  };

  const handleCreateSandbox = async () => {
    if (!file) { setError("Select a model file first"); return; }
    setLoading(true); setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("engagement_id", engagement.id);
      formData.append("framework", framework);
      formData.append("gpu", "false");
      const resp = await fetch("/api/v2/sandbox/create", { method: "POST", body: formData });
      const data = await resp.json();
      if (resp.ok) { setSandbox(data); } else { setError(data.error || "Sandbox creation failed"); }
    } catch (e) { setError(`Connection failed: ${e.message}`); }
    setLoading(false);
  };

  const handleDestroySandbox = async () => {
    if (!sandbox) return;
    try {
      await fetch(`/api/v2/sandbox/${sandbox.id}`, { method: "DELETE" });
      setSandbox(null); setFile(null);
    } catch (e) { setError(`Destroy failed: ${e.message}`); }
  };

  const handleTestConnection = async () => {
    setLoading(true); setError(null); setTestResult(null);
    try {
      const resp = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", ...(authHeaders ? { Authorization: authHeaders } : {}) }, body: JSON.stringify({ input: [[0]] }) });
      setTestResult({ ok: resp.ok, status: resp.status, time: "—" });
    } catch (e) { setTestResult({ ok: false, status: 0, error: e.message }); }
    setLoading(false);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white mb-0.5">Target Setup</h1>
        <p className="text-sm text-white/35">Configure how to reach the AI system under test</p>
      </div>

      {/* Method selector */}
      <div className="grid grid-cols-4 gap-3">
        {methods.map(m => (
          <button key={m.id} onClick={() => { setMethod(m.id); setError(null); setTestResult(null); }} className={`${G} rounded-lg p-4 text-left transition-all ${method === m.id ? "border-emerald-500/30 bg-emerald-500/[0.04]" : "hover:border-white/[0.12]"}`}>
            <m.icon size={18} className={method === m.id ? "text-emerald-400" : "text-white/30"} />
            <div className={`text-[12px] font-medium mt-2 ${method === m.id ? "text-emerald-400" : "text-white/70"}`}>{m.label}</div>
            <div className="text-[10px] text-white/30 mt-1">{m.desc}</div>
            {m.sandbox && <span className="inline-block mt-2 text-[8px] font-mono text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded border border-violet-500/20">Sandbox</span>}
          </button>
        ))}
      </div>

      {/* ── API Endpoint config ── */}
      {method === "api_endpoint" && (
        <div className={`${G} rounded-lg p-5`}>
          <h3 className="text-sm font-medium text-emerald-400 mb-4">API Endpoint — Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-[10px] text-white/35 block mb-1">URL</label>
              <input value={url} onChange={e => setUrl(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="https://api.target.com/v2/predict" /></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Authorization header</label>
              <input value={authHeaders} onChange={e => setAuthHeaders(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="Bearer sk-..." /></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Response format</label>
              <input className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="JSON (auto-detect)" /></div>
          </div>
          <div className="flex items-center gap-3 mt-5">
            <button onClick={handleTestConnection} disabled={!url || loading} className="px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2">
              {loading ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}Test Connection
            </button>
            {testResult && (
              <span className={`text-[10px] font-mono px-2 py-1 rounded ${testResult.ok ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                {testResult.ok ? `✓ Connected (${testResult.status})` : `✗ Failed: ${testResult.error || testResult.status}`}
              </span>
            )}
          </div>
        </div>
      )}

      {/* ── Model Upload config ── */}
      {method === "model_upload" && (
        <div className={`${G} rounded-lg p-5`}>
          <h3 className="text-sm font-medium text-emerald-400 mb-4">Model Upload — Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] text-white/35 block mb-1">Model file</label>
              <input type="file" accept=".pt,.pth,.onnx,.h5,.keras,.pb,.pkl,.joblib,.safetensors" onChange={handleFileSelect} className="hidden" id="model-file-input" />
              <label htmlFor="model-file-input"
                onDrop={handleDrop} onDragOver={e => e.preventDefault()}
                className={`flex items-center gap-3 px-3 py-3 rounded-md border border-dashed cursor-pointer transition-colors ${file ? "bg-emerald-500/[0.04] border-emerald-500/30" : "bg-black/30 border-white/[0.1] hover:border-emerald-500/30"}`}>
                {file ? (
                  <>
                    <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] text-emerald-400 truncate">{file.name}</div>
                      <div className="text-[9px] text-white/25">{formatSize(file.size)}</div>
                    </div>
                    <button onClick={(e) => { e.preventDefault(); setFile(null); }} className="text-white/20 hover:text-white/50"><XCircle size={14} /></button>
                  </>
                ) : (
                  <>
                    <Upload size={14} className="text-white/25" />
                    <span className="text-[11px] text-white/30">Drop file or click to browse</span>
                  </>
                )}
              </label>
            </div>
            <div><label className="text-[10px] text-white/35 block mb-1">Framework</label>
              <select value={framework} onChange={e => setFramework(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] focus:outline-none focus:border-emerald-500/30">
                <option value="pytorch">PyTorch (.pt, .pth)</option><option value="onnx">ONNX (.onnx)</option><option value="tensorflow">TensorFlow (.h5, .pb)</option><option value="sklearn">scikit-learn (.pkl)</option><option value="safetensors">SafeTensors (.safetensors)</option>
              </select></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Input shape (optional)</label>
              <input value={inputShape} onChange={e => setInputShape(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="e.g. 1,28,28 or 3,224,224" /></div>
          </div>
          <div className="flex items-center gap-3 mt-5">
            <button onClick={handleCreateSandbox} disabled={!file || loading} className="px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2">
              {loading ? <Loader2 size={13} className="animate-spin" /> : <Box size={13} />}
              {loading ? "Creating sandbox..." : "Create Sandbox & Connect"}
            </button>
            <span className="text-[10px] text-white/20">Uploads model into isolated Docker container</span>
          </div>
        </div>
      )}

      {/* ── Registry config ── */}
      {method === "registry" && (
        <div className={`${G} rounded-lg p-5`}>
          <h3 className="text-sm font-medium text-emerald-400 mb-4">Registry — Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-[10px] text-white/35 block mb-1">Registry URL</label>
              <input value={registryUrl} onChange={e => setRegistryUrl(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="https://mlflow.internal:5000 or huggingface.co" /></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Model ID</label>
              <input value={registryModelId} onChange={e => setRegistryModelId(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="models:/fraud-detector/production" /></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Credentials</label>
              <input type="password" value={registryCreds} onChange={e => setRegistryCreds(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="Token or API key" /></div>
          </div>
          <div className="flex items-center gap-3 mt-5">
            <button disabled={!registryUrl || !registryModelId} className="px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"><Box size={13} />Pull & Create Sandbox</button>
          </div>
        </div>
      )}

      {/* ── LLM Endpoint config ── */}
      {method === "llm_endpoint" && (
        <div className={`${G} rounded-lg p-5`}>
          <h3 className="text-sm font-medium text-emerald-400 mb-4">LLM Endpoint — Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="text-[10px] text-white/35 block mb-1">Provider</label>
              <select value={provider} onChange={e => setProvider(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] focus:outline-none focus:border-emerald-500/30">
                <option>Anthropic (Claude)</option><option>OpenAI (GPT)</option><option>Azure OpenAI</option><option>Self-hosted (Ollama, vLLM)</option><option>Custom endpoint</option>
              </select></div>
            <div><label className="text-[10px] text-white/35 block mb-1">API key</label>
              <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="sk-..." /></div>
            <div><label className="text-[10px] text-white/35 block mb-1">Model name</label>
              <input value={modelName} onChange={e => setModelName(e.target.value)} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="claude-sonnet-4-20250514 or gpt-4o" /></div>
          </div>
          <div className="flex items-center gap-3 mt-5">
            <button disabled={!apiKey} className="px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"><Zap size={13} />Test Connection</button>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-md bg-red-500/10 border border-red-500/20">
          <AlertTriangle size={14} className="text-red-400 shrink-0" />
          <span className="text-[11px] text-red-400">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400/50 hover:text-red-400"><XCircle size={14} /></button>
        </div>
      )}

      {/* Active sandbox status */}
      {sandbox && sandbox.status === "running" && (
        <div className={`${G} rounded-lg p-5`}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-violet-400 flex items-center gap-2"><Server size={14} />Active Sandbox</h3>
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{sandbox.status}</span>
              <button onClick={handleDestroySandbox} className="text-[9px] text-red-400/50 hover:text-red-400 px-2 py-0.5 rounded hover:bg-red-500/10">Destroy</button>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            {[
              { l: "Container", v: sandbox.container_id || `bbap-sbx-${String(sandbox.id).padStart(3,"0")}` },
              { l: "Framework", v: sandbox.framework },
              { l: "Port", v: `:${sandbox.port}` },
              { l: "Mode", v: sandbox.mode || "docker" },
            ].map(x => (
              <div key={x.l}>
                <div className="text-[9px] text-white/25 uppercase tracking-wider">{x.l}</div>
                <div className="text-[11px] font-mono text-white/60 mt-0.5">{x.v}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2 text-[10px] text-white/20">
            <Radio size={10} className="text-emerald-400 animate-pulse" />
            <span>Network isolated — {sandbox.model_filename} ({formatSize(sandbox.model_size_bytes)})</span>
          </div>
          {sandbox.api_url && (
            <div className="mt-2 text-[10px] font-mono text-emerald-400/40">API: {sandbox.api_url}</div>
          )}
        </div>
      )}

      {/* Sandbox creation in progress */}
      {sandbox && sandbox.status === "starting" && (
        <div className={`${G} rounded-lg p-5 text-center`}>
          <Loader2 size={20} className="text-emerald-400 animate-spin mx-auto mb-2" />
          <div className="text-[11px] text-white/40">Creating sandbox container...</div>
        </div>
      )}

      {/* Sandbox failed */}
      {sandbox && sandbox.status === "failed" && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-md bg-red-500/10 border border-red-500/20">
          <XCircle size={14} className="text-red-400 shrink-0" />
          <div className="flex-1">
            <div className="text-[11px] text-red-400">Sandbox creation failed</div>
            {sandbox.error && <div className="text-[10px] text-red-400/50 mt-0.5 font-mono">{sandbox.error}</div>}
          </div>
          <button onClick={() => setSandbox(null)} className="text-[10px] text-white/30 hover:text-white/50">Dismiss</button>
        </div>
      )}

      {/* Scope selection */}
      <div className={`${G} rounded-lg p-5`}>
        <h3 className="text-sm font-medium text-white/70 mb-3">Attack Surface Scope</h3>
        <p className="text-[10px] text-white/25 mb-3">Select which layers to include in this engagement. Grayed-out attacks require a different access method.</p>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(LAYER_META).map(([key, m]) => {
            const Icon = m.icon;
            const attacks = LAYER_ATTACKS[key];
            const available = attacks.filter(a => a.access.includes(method === "api_endpoint" ? "api" : method === "model_upload" ? "upload" : method === "registry" ? "registry" : "llm"));
            return (
              <label key={key} className={`flex items-center gap-3 px-3 py-2.5 rounded-md bg-white/[0.02] hover:bg-white/[0.04] cursor-pointer transition-colors ${available.length === 0 ? "opacity-25 pointer-events-none" : ""}`}>
                <input type="checkbox" defaultChecked={available.length > 0} className="rounded border-white/20 bg-black/30" />
                <Icon size={14} style={{ color: m.color }} />
                <div className="flex-1">
                  <span className="text-[11px] text-white/65">{m.label}</span>
                  <span className="text-[9px] text-white/25 ml-2">{available.length}/{attacks.length} attacks</span>
                </div>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   ATTACK LAYER PAGE (reusable)
   ═══════════════════════════════════ */
function LayerPage({ layerKey, engagement }) {
  const meta = LAYER_META[layerKey];
  const attacks = LAYER_ATTACKS[layerKey] || [];
  const findings = MOCK_FINDINGS.filter(f => f.layer === layerKey);
  const [sel, setSel] = useState(null);
  const Icon = meta.icon;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${meta.bg} border ${meta.bd} flex items-center justify-center`}>
          <Icon size={20} style={{ color: meta.color }} />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-white">{meta.label}</h1>
          <p className="text-sm text-white/35">{attacks.length} attacks available — {findings.length} findings</p>
        </div>
      </div>

      {/* Attack catalog */}
      <div>
        <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Available attacks</div>
        <div className="grid grid-cols-2 gap-2">
          {attacks.map(a => (
            <button key={a.id} onClick={() => setSel(a)} className={`${G} rounded-lg p-4 text-left transition-all hover:border-white/[0.12] ${sel?.id === a.id ? "border-emerald-500/30 bg-emerald-500/[0.03]" : ""}`}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[12px] font-medium text-white/80">{a.name}</span>
                <span className={`text-[8px] font-mono px-1.5 py-0.5 rounded ${a.difficulty === "Beginner" ? "bg-emerald-500/10 text-emerald-400" : a.difficulty === "Intermediate" ? "bg-amber-500/10 text-amber-400" : a.difficulty === "Advanced" ? "bg-orange-500/10 text-orange-400" : "bg-red-500/10 text-red-400"}`}>{a.difficulty}</span>
              </div>
              <div className="flex items-center gap-2">
                {a.atlas && <span className="text-[9px] font-mono text-orange-300/60">{a.atlas}</span>}
                <div className="flex gap-1">
                  {a.access.map(ac => (
                    <span key={ac} className="text-[8px] font-mono text-white/20 bg-white/[0.03] px-1 py-0.5 rounded">{ac}</span>
                  ))}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Run panel */}
      {sel && (
        <div className={`${G} rounded-lg p-5`}>
          <h3 className="text-sm font-medium mb-3" style={{ color: meta.color }}>Run: {sel.name}</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div><label className="text-[10px] text-white/35 block mb-1">Target</label><div className="px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-[11px] text-white/40 font-mono">{engagement.name}</div></div>
            {layerKey === "inference" && sel.id.startsWith("fgsm") && (
              <div><label className="text-[10px] text-white/35 block mb-1">Epsilon (ε)</label><input type="number" defaultValue={0.03} step={0.01} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" /></div>
            )}
            {layerKey === "training" && (
              <div><label className="text-[10px] text-white/35 block mb-1">Poison rate</label><input type="number" defaultValue={0.1} step={0.05} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" /></div>
            )}
            {layerKey === "artifacts" && (
              <div><label className="text-[10px] text-white/35 block mb-1">Max queries</label><input type="number" defaultValue={1000} step={100} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30" /></div>
            )}
          </div>
          <button className="px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 flex items-center gap-2"><Play size={13} />Execute Attack</button>
        </div>
      )}

      {/* Layer findings */}
      {findings.length > 0 && (
        <div>
          <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Findings in this layer</div>
          <div className="space-y-2">
            {findings.map(f => {
              const sv = SEV[f.severity];
              return (
                <div key={f.id} className={`${G} rounded-lg px-4 py-3`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${sv.dot}`} />
                    <span className="text-[9px] font-mono text-white/25 w-10">{f.id}</span>
                    <span className="text-[11px] text-white/70 flex-1">{f.title}</span>
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${sv.bg} ${sv.tx} border ${sv.bd}`}>{f.severity}</span>
                    {f.related.length > 0 && (
                      <span className="text-[8px] font-mono text-white/20 flex items-center gap-1"><Network size={10} />{f.related.length} linked</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════
   FINDINGS PAGE
   ═══════════════════════════════════ */
function FindingsPage() {
  const [filter, setFilter] = useState("all");
  const filtered = filter === "all" ? MOCK_FINDINGS : MOCK_FINDINGS.filter(f => f.layer === filter);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-0.5">Findings</h1>
          <p className="text-sm text-white/35">{MOCK_FINDINGS.length} findings across {new Set(MOCK_FINDINGS.map(f=>f.layer)).size} layers</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30"><Download size={13} />Export Findings</button>
      </div>

      {/* Layer filter */}
      <div className="flex gap-1.5 flex-wrap">
        <button onClick={() => setFilter("all")} className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition-all ${filter === "all" ? "bg-emerald-500/12 text-emerald-400 border border-emerald-500/20" : `${G} text-white/40 hover:text-white/60`}`}>All ({MOCK_FINDINGS.length})</button>
        {Object.entries(LAYER_META).map(([key, m]) => {
          const count = MOCK_FINDINGS.filter(f => f.layer === key).length;
          if (count === 0) return null;
          return (
            <button key={key} onClick={() => setFilter(key)} className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition-all ${filter === key ? `${m.bg} border ${m.bd}` : `${G} text-white/40 hover:text-white/60`}`} style={filter === key ? { color: m.color } : undefined}>
              {m.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Findings list with connections */}
      <div className="space-y-2">
        {filtered.map(f => {
          const lm = LAYER_META[f.layer];
          const sv = SEV[f.severity];
          const relatedFindings = MOCK_FINDINGS.filter(r => f.related.includes(r.id));
          return (
            <div key={f.id} className={`${G} rounded-lg`}>
              <div className="px-5 py-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-2 h-2 rounded-full ${sv.dot}`} />
                  <span className="text-[9px] font-mono text-white/25">{f.id}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${lm.bg} border ${lm.bd}`} style={{ color: lm.color }}>{lm.label}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${sv.bg} ${sv.tx} border ${sv.bd}`}>{f.severity}</span>
                  {f.atlas && <span className="text-[9px] font-mono text-orange-300/50">{f.atlas}</span>}
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ml-auto ${f.status === "open" ? "bg-red-500/10 text-red-400" : f.status === "in_progress" ? "bg-amber-500/10 text-amber-400" : "bg-emerald-500/10 text-emerald-400"}`}>{f.status}</span>
                </div>
                <div className="text-[12px] text-white/75 mb-2">{f.title}</div>
                <div className="flex gap-3 flex-wrap">
                  {Object.entries(f.metrics).map(([k, v]) => (
                    <span key={k} className="text-[9px] font-mono bg-white/[0.03] text-white/35 px-2 py-0.5 rounded">{k}: {typeof v === 'number' ? (v % 1 === 0 ? v : v.toFixed(1)) : v}</span>
                  ))}
                </div>
              </div>

              {/* Related findings */}
              {relatedFindings.length > 0 && (
                <div className="px-5 py-2.5 border-t border-white/[0.04] bg-white/[0.01]">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Network size={10} className="text-white/20" />
                    <span className="text-[9px] text-white/20 uppercase tracking-wider">Connected findings</span>
                  </div>
                  {relatedFindings.map(r => {
                    const rlm = LAYER_META[r.layer];
                    return (
                      <div key={r.id} className="flex items-center gap-2 ml-3 py-1">
                        <ArrowRight size={10} className="text-white/10" />
                        <span className="text-[9px] font-mono text-white/25">{r.id}</span>
                        <span className="text-[9px]" style={{ color: rlm.color }}>{rlm.label}</span>
                        <span className="text-[10px] text-white/40">{r.title}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   REPORT GENERATOR PAGE
   ═══════════════════════════════════ */
function ReportPage({ engagement }) {
  const sections = [
    { name: "Executive Summary", desc: "Risk score, key findings, target overview", auto: true },
    { name: "Training Phase", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="training").length} findings`, auto: true },
    { name: "Inference Phase", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="inference").length} findings`, auto: true },
    { name: "Model Artifacts", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="artifacts").length} findings`, auto: true },
    { name: "Data Pipeline", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="pipeline").length} findings`, auto: true },
    { name: "Infrastructure", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="infra").length} findings`, auto: true },
    { name: "Output Layer", desc: `${MOCK_FINDINGS.filter(f=>f.layer==="output").length} findings`, auto: true },
    { name: "Cross-Layer Analysis", desc: "Attack chains and finding relationships", auto: true },
    { name: "Pipeline Health", desc: "46 controls status", auto: true },
    { name: "Compliance Mapping", desc: "NIST, ATLAS, OWASP, EU AI Act", auto: true },
    { name: "Remediation Roadmap", desc: "Prioritized action plan", auto: true },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-0.5">Report Generator</h1>
          <p className="text-sm text-white/35">Pulls findings from all 6 layers into a comprehensive report</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-white/[0.04] text-white/50 text-[11px] hover:bg-white/[0.08] border border-white/[0.06]"><FileText size={13} />Export PDF</button>
          <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500"><Download size={13} />Export JSON</button>
        </div>
      </div>

      <div className="space-y-2">
        {sections.map((s, i) => (
          <div key={i} className={`${G} rounded-lg px-5 py-3.5 flex items-center gap-4`}>
            <div className="w-6 h-6 rounded-md bg-emerald-500/10 flex items-center justify-center text-[10px] font-bold text-emerald-400 font-mono">{i + 1}</div>
            <div className="flex-1">
              <div className="text-[12px] font-medium text-white/80">{s.name}</div>
              <div className="text-[10px] text-white/30">{s.desc}</div>
            </div>
            {s.auto && <CheckCircle2 size={14} className="text-emerald-500/50" />}
            <span className="text-[9px] font-mono text-emerald-400/40">auto-populated</span>
          </div>
        ))}
      </div>

      <div className={`${G} rounded-lg p-5`}>
        <div className="text-[10px] text-white/25 uppercase tracking-widest mb-3">Report preview</div>
        <div className="font-mono text-[11px] text-white/40 space-y-1">
          <div>Engagement: <span className="text-emerald-400">{engagement.name}</span></div>
          <div>Target: <span className="text-white/60">{engagement.target_type.replace("_"," ")}</span></div>
          <div>Findings: <span className="text-orange-400">{MOCK_FINDINGS.length}</span> ({MOCK_FINDINGS.filter(f=>f.severity==="critical").length} critical, {MOCK_FINDINGS.filter(f=>f.severity==="high").length} high)</div>
          <div>Layers tested: <span className="text-white/60">{new Set(MOCK_FINDINGS.map(f=>f.layer)).size}/6</span></div>
          <div>Risk score: <span className="text-amber-400">{engagement.risk_score}/100 (medium)</span></div>
          <div>Cross-layer connections: <span className="text-violet-400">{MOCK_FINDINGS.reduce((s,f) => s + f.related.length, 0)}</span></div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   OVERLAY (shared modal)
   ═══════════════════════════════════ */
function Overlay({children,onClose}){
  return(
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
      <div className={`${GS} rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto`}>{children}</div>
    </div>
  );
}

/* ═══════════════════════════════════
   ATLAS INTEL PAGE
   ═══════════════════════════════════ */
function AtlasPage(){
  const[stats,sStats]=useState(null);
  const[q,sQ]=useState("");const[sr,sSr]=useState(null);
  const[modTab,sModTab]=useState(null);const[mapping,sMapping]=useState(null);
  const[coverage,sCov]=useState(null);const[tactics,sTactics]=useState([]);
  const[detail,sDetail]=useState(null);

  useEffect(()=>{
    atlas.get("/stats").then(sStats).catch(()=>{});
    atlas.get("/coverage").then(sCov).catch(()=>{});
    atlas.get("/tactics").then(sTactics).catch(()=>{});
  },[]);

  const doSearch=async()=>{if(!q.trim())return;const d=await atlas.get(`/search?q=${encodeURIComponent(q)}`);sSr(d);};
  const showMod=async m=>{sModTab(m);const d=await atlas.get(`/mapping/${m}`);sMapping(d);};
  const showTech=async id=>{const d=await atlas.get(`/technique/${id}`);sDetail({type:"tech",...d});};
  const showCase=async id=>{const d=await atlas.get(`/case-study/${id}`);sDetail({type:"case",...d});};

  return(<div className="space-y-5">
    <div><h1 className="text-xl font-semibold text-white mb-0.5">MITRE ATLAS Intelligence</h1>
    <p className="text-sm text-white/35">AI/ML threat framework — techniques, mitigations, case studies</p></div>

    {/* Stats */}
    {stats&&<div className="grid grid-cols-5 gap-3">{[
      {l:"Version",v:`v${stats.version}`,c:"text-emerald-400"},
      {l:"Tactics",v:stats.tactics,c:"text-amber-400"},
      {l:"Techniques",v:stats.techniques_total,c:"text-orange-300"},
      {l:"Mitigations",v:stats.mitigations,c:"text-blue-400"},
      {l:"Case Studies",v:stats.case_studies,c:"text-white/70"},
    ].map(x=><div key={x.l} className={`${G} rounded-lg p-4`}><div className="text-[10px] text-white/25 uppercase tracking-widest">{x.l}</div><div className={`text-xl font-semibold mt-1 ${x.c}`}>{x.v}</div></div>)}</div>}

    {/* Search */}
    <div className="flex gap-2">
      <div className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-md ${G}`}>
        <Search size={14} className="text-white/25"/>
        <input value={q} onChange={e=>sQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&doSearch()} placeholder="Search techniques, mitigations, case studies..." className="flex-1 bg-transparent text-[12px] text-white/70 focus:outline-none placeholder:text-white/20"/>
      </div>
      <button onClick={doSearch} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500">Search</button>
    </div>

    {sr&&<div className={`${G} rounded-lg p-4 space-y-3`}>
      {sr.techniques?.length>0&&<div>
        <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Techniques ({sr.techniques.length})</div>
        {sr.techniques.slice(0,8).map(t=><div key={t.id} onClick={()=>showTech(t.id)} className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[90px]">{t.id}</span><span className="text-[11px] text-white/70">{t.name}</span></div>)}
      </div>}
      {sr.case_studies?.length>0&&<div>
        <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Case Studies ({sr.case_studies.length})</div>
        {sr.case_studies.slice(0,5).map(c=><div key={c.id} onClick={()=>showCase(c.id)} className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[90px]">{c.id}</span><span className="text-[11px] text-white/70">{c.name}</span></div>)}
      </div>}
      {sr.mitigations?.length>0&&<div>
        <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Mitigations ({sr.mitigations.length})</div>
        {sr.mitigations.slice(0,5).map(m=><div key={m.id} className="flex items-center gap-3 px-3 py-2"><span className="text-[10px] font-mono text-blue-400 min-w-[90px]">{m.id}</span><span className="text-[11px] text-white/70">{m.name}</span></div>)}
      </div>}
      {!sr.techniques?.length&&!sr.case_studies?.length&&!sr.mitigations?.length&&<p className="text-[11px] text-white/25">No results found.</p>}
    </div>}

    {/* Module Mappings */}
    <div>
      <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Attack module → ATLAS mapping</div>
      <div className="flex gap-2 flex-wrap mb-3">
        {Object.entries(MOD_LABELS).map(([k,v])=><button key={k} onClick={()=>showMod(k)} className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${modTab===k?"bg-emerald-500/12 text-emerald-400 border border-emerald-500/20":`${G} text-white/45 hover:text-white/70`}`}>{v}</button>)}
      </div>

      {mapping&&<div className={`${G} rounded-lg p-5`}>
        <h3 className="text-sm font-medium text-emerald-400 mb-1">{mapping.name}</h3>
        <p className="text-[11px] text-white/35 mb-4">{mapping.description}</p>
        <div className="space-y-4">
          <div>
            <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Techniques ({mapping.techniques?.length||0})</div>
            {mapping.techniques?.map(t=><div key={t.id} onClick={()=>showTech(t.id)} className="flex gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer mb-1">
              <span className="text-[10px] font-mono text-orange-300 min-w-[100px] shrink-0">{t.id}</span>
              <div className="flex-1">
                <div className="text-[11px] text-white/70 font-medium">{t.name}</div>
                <div className="text-[10px] text-white/30 mt-0.5">{t.relevance}</div>
                {t.bbap_functions?.length>0&&<div className="text-[10px] text-emerald-400/50 font-mono mt-0.5">{t.bbap_functions.join(", ")}</div>}
              </div>
            </div>)}
          </div>
          <div>
            <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Mitigations ({mapping.mitigations?.length||0})</div>
            {mapping.mitigations?.map(m=><div key={m.id} className="flex gap-3 px-3 py-1.5"><span className="text-[10px] font-mono text-blue-400 min-w-[100px]">{m.id}</span><span className="text-[11px] text-white/55">{m.name}</span></div>)}
          </div>
          <div>
            <div className="text-[10px] text-white/25 uppercase tracking-widest mb-2">Case Studies ({mapping.case_studies?.length||0})</div>
            {mapping.case_studies?.map(c=><div key={c.id} onClick={()=>showCase(c.id)} className="flex gap-3 px-3 py-1.5 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[100px]">{c.id}</span><span className="text-[11px] text-white/55">{c.name}</span></div>)}
          </div>
        </div>
      </div>}
    </div>

    {/* Tactic Coverage Matrix */}
    {coverage&&tactics.length>0&&<div>
      <div className="text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-3">Tactic coverage</div>
      <div className={`${G} rounded-lg overflow-hidden`}>
        {tactics.map(t=>{const mods=coverage[t.name]||[];const has=mods.length>0;return(
          <div key={t.id} className={`flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.04] last:border-b-0 ${has?"bg-emerald-500/[0.02]":""}`}>
            <span className="text-[10px] font-mono text-orange-300/60 min-w-[90px]">{t.id}</span>
            <span className="text-[11px] text-white/65 flex-1">{t.name}</span>
            <div className="flex gap-1.5">{has?mods.map(m=><span key={m} className="text-[8px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{MOD_LABELS[m]||m}</span>):<span className="text-[9px] text-white/15">not covered</span>}</div>
          </div>
        );})}
      </div>
    </div>}

    {/* Detail Overlay */}
    {detail&&<Overlay onClose={()=>sDetail(null)}>
      <div className="p-5">
        {detail.type==="tech"&&detail.technique&&<>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[10px] font-mono text-orange-300 bg-orange-500/10 px-2 py-1 rounded">{detail.technique.id}</span>
            <h3 className="text-sm font-semibold text-white">{detail.technique.name}</h3>
          </div>
          <p className="text-[12px] text-white/50 leading-relaxed mb-4">{detail.technique.description?.slice(0,500)}{detail.technique.description?.length>500?"...":""}</p>
          {detail.technique.tactics&&<div className="mb-3"><span className="text-[10px] text-white/25">Tactics: </span><span className="text-[10px] text-white/45">{detail.technique.tactics.join(", ")}</span></div>}
          {detail.subtechniques?.length>0&&<div className="mb-3">
            <div className="text-[10px] text-white/25 mb-1">Sub-techniques ({detail.subtechniques.length})</div>
            {detail.subtechniques.map(s=><div key={s.id} className="text-[10px] text-white/45 ml-2 mb-0.5"><span className="text-orange-300/50 font-mono">{s.id}</span> {s.name}</div>)}
          </div>}
          {detail.mitigations?.length>0&&<div className="mb-3">
            <div className="text-[10px] text-white/25 mb-1">Mitigations ({detail.mitigations.length})</div>
            {detail.mitigations.map(m=><div key={m.id} className="text-[10px] text-white/45 ml-2 mb-0.5"><span className="text-blue-400/50 font-mono">{m.id}</span> {m.name}</div>)}
          </div>}
          <a href={`https://atlas.mitre.org/techniques/${detail.technique.id}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 mt-2 text-[11px] text-emerald-400 hover:underline"><ExternalLink size={11}/>View on atlas.mitre.org</a>
        </>}
        {detail.type==="case"&&detail.case_study&&<>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[10px] font-mono text-orange-300 bg-orange-500/10 px-2 py-1 rounded">{detail.case_study.id}</span>
            <h3 className="text-sm font-semibold text-white">{detail.case_study.name}</h3>
          </div>
          <p className="text-[12px] text-white/50 leading-relaxed mb-4">{detail.case_study.summary}</p>
          {detail.case_study["incident-date"]&&<div className="text-[10px] text-white/25 mb-3">Date: {detail.case_study["incident-date"]}</div>}
          {detail.attack_chain?.length>0&&<div>
            <div className="text-[10px] text-white/25 mb-2">Attack chain ({detail.attack_chain.length} steps)</div>
            {detail.attack_chain.map((s,i)=><div key={i} className="flex gap-3 mb-3">
              <div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">{i+1}</div>
              <div>
                <div className="text-[9px] text-amber-400 uppercase tracking-wider">{s.tactic_name}</div>
                <div onClick={()=>showTech(s.technique_id)} className="text-[11px] text-emerald-400 cursor-pointer hover:underline">{s.technique_id}: {s.technique_name}</div>
                <div className="text-[10px] text-white/30 mt-0.5">{s.description?.slice(0,150)}</div>
              </div>
            </div>)}
          </div>}
          <a href={`https://atlas.mitre.org/studies/${detail.case_study.id}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 mt-2 text-[11px] text-emerald-400 hover:underline"><ExternalLink size={11}/>View on atlas.mitre.org</a>
        </>}
      </div>
    </Overlay>}
  </div>);
}

/* ═══════════════════════════════════
   GOVERNANCE / AI RISK MANAGEMENT
   ═══════════════════════════════════ */
function GovernancePage({ engagement }) {
  const [activeTab, setActiveTab] = useState("rmf");
  const [expandedRmf, setExpandedRmf] = useState(null);

  const RMF = [
    { id:"govern", name:"GOVERN", color:"text-violet-400", bg:"bg-violet-500/10", bd:"border-violet-500/20", icon:Users, desc:"Policies, processes, and accountability",
      subs:[{id:"GOVERN 1.1",n:"Legal/regulatory requirements documented",s:"partial"},{id:"GOVERN 1.2",n:"Trustworthy AI in policies",s:"met"},{id:"GOVERN 1.3",n:"Risk tolerance defined",s:"met"},{id:"GOVERN 1.6",n:"Policies transparent and documented",s:"partial"},{id:"GOVERN 1.7",n:"Supply chain risks managed",s:"met"},{id:"GOVERN 2.1",n:"Roles and responsibilities defined",s:"met"},{id:"GOVERN 2.2",n:"Personnel trained",s:"partial"}],
      features:["User Management — Admin/analyst/viewer roles","Knowledge Base — Policy documentation","Audit Trail — Activity logging","Pipeline: Authentication — OAuth2/JWT","Pipeline: Supply Chain Audit"]},
    { id:"map", name:"MAP", color:"text-cyan-400", bg:"bg-cyan-500/10", bd:"border-cyan-500/20", icon:Target, desc:"Identifying and contextualizing AI risks",
      subs:[{id:"MAP 1.1",n:"Intended purposes documented",s:"met"},{id:"MAP 1.2",n:"Data sources documented",s:"met"},{id:"MAP 1.5",n:"Input data quality assessed",s:"met"},{id:"MAP 1.6",n:"Privacy risks identified",s:"met"},{id:"MAP 2.1",n:"AI risks categorized",s:"met"},{id:"MAP 3.1",n:"Benefits and costs assessed",s:"partial"},{id:"MAP 3.4",n:"Supply chain risks mapped",s:"met"}],
      features:["Secure Pipeline — 46 controls across 5 stages","ATLAS Intel — 170 techniques, 16 tactics","Project Management — Per-project risk scoping","Pipeline: PII Scan","Pipeline: Source Auth & Provenance"]},
    { id:"measure", name:"MEASURE", color:"text-emerald-400", bg:"bg-emerald-500/10", bd:"border-emerald-500/20", icon:BarChart3, desc:"Quantifying and benchmarking AI risks",
      subs:[{id:"MEASURE 1.1",n:"Measurement approaches established",s:"met"},{id:"MEASURE 2.5",n:"Adversarial robustness tested",s:"met"},{id:"MEASURE 2.6",n:"Bias and fairness tested",s:"partial"},{id:"MEASURE 2.7",n:"Safety and security tested",s:"met"}],
      features:["Adversarial — FGSM/PGD at configurable epsilon","Data Poisoning — Label-flip and backdoor","Evasion — Pixel, noise, spatial","Model Extraction — Random and active learning","Prompt Injection — 10-attack catalog","Results & Reports — Quantified metrics"]},
    { id:"manage", name:"MANAGE", color:"text-rose-400", bg:"bg-rose-500/10", bd:"border-rose-500/20", icon:Shield, desc:"Responding and communicating about AI risks",
      subs:[{id:"MANAGE 1.1",n:"Risk treatment plans defined",s:"met"},{id:"MANAGE 2.1",n:"AI system monitored",s:"met"},{id:"MANAGE 4.1",n:"Results communicated",s:"met"}],
      features:["Alerts — Severity-based incident tracking","Pipeline Remediation — Control status tracking","Knowledge Base — Lessons learned","Export Reports — Stakeholder-ready JSON","Monitoring — Query rates, latency, drift"]},
  ];

  const totalSubs = RMF.reduce((s,f)=>s+f.subs.length,0);
  const metSubs = RMF.reduce((s,f)=>s+f.subs.filter(sc=>sc.s==="met").length,0);
  const partialSubs = RMF.reduce((s,f)=>s+f.subs.filter(sc=>sc.s==="partial").length,0);
  const overallPct = Math.round(metSubs/totalSubs*100);

  const COMPLIANCE = [
    {name:"NIST AI RMF",ver:"1.0 (2023)",cov:85,detail:"4 functions, 13+ sub-categories"},
    {name:"MITRE ATLAS",ver:"5.6.0 (2025)",cov:50,detail:"8/16 tactics covered by attack modules"},
    {name:"OWASP LLM Top 10",ver:"2025",cov:60,detail:"LLM01, LLM02, LLM07 directly covered"},
    {name:"EU AI Act",ver:"2024",cov:45,detail:"Risk classification, documentation, robustness"},
    {name:"ISO/IEC 42001",ver:"2023",cov:55,detail:"Pipeline controls, roles, audit trails"},
  ];

  const CONTROLS = [
    {name:"Input Controls",icon:Database,items:["Data validation","Poison detection","PII scanning","Source authentication","Prompt filtering","Injection detection","Encoding bypass prevention"]},
    {name:"Model Controls",icon:Cpu,items:["Adversarial robustness","Backdoor detection","Architecture review","Weight integrity","Version control","Supply chain audit"]},
    {name:"Output Controls",icon:Filter,items:["Output guardrails","Response watermarking","Output truncation","Context isolation"]},
    {name:"Infrastructure Controls",icon:Globe,items:["Authentication (OAuth2/JWT)","Rate limiting","Encryption at rest","Query logging","TLS enforcement","Audit trail"]},
  ];

  const riskScores = {adversarial:33,poisoning:22,evasion:15,extraction:28,injection:45};
  const composite = 30;
  const ratingOf = s => s<=15?"low":s<=40?"medium":s<=70?"high":"critical";

  const tabs = [{id:"rmf",l:"NIST AI RMF"},{id:"controls",l:"Controls"},{id:"risk",l:"Risk Scores"},{id:"compliance",l:"Compliance"}];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div><h1 className="text-xl font-semibold text-white mb-0.5">AI Risk Management & Governance</h1>
        <p className="text-sm text-white/35">NIST AI RMF alignment, controls framework, and compliance tracking</p></div>
        <button className="flex items-center gap-2 px-4 py-2 rounded-md bg-white/[0.04] text-white/50 text-[11px] hover:bg-white/[0.08] border border-white/[0.06]"><Download size={13}/>Export Report</button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-3">
        {[{l:"RMF Coverage",v:`${overallPct}%`,s:`${metSubs}/${totalSubs} sub-categories met`,c:"text-emerald-400",bg:"bg-emerald-500/10",I:ShieldCheck},
          {l:"Pipeline Health",v:"76%",s:"35/46 controls passing",c:"text-cyan-400",bg:"bg-cyan-500/10",I:Layers},
          {l:"Partial",v:partialSubs,s:"sub-categories need attention",c:"text-amber-400",bg:"bg-amber-500/10",I:AlertTriangle},
          {l:"Frameworks",v:COMPLIANCE.length,s:"compliance mappings tracked",c:"text-rose-400",bg:"bg-rose-500/10",I:Globe},
        ].map(x=><div key={x.l} className={`${G} rounded-lg p-3.5`}><div className={`w-7 h-7 rounded-md ${x.bg} flex items-center justify-center mb-2`}><x.I size={14} className={x.c}/></div><div className={`text-xl font-semibold font-mono ${x.c}`}>{x.v}</div><div className="text-[10px] text-white/35">{x.l}</div><div className="text-[9px] text-white/20 mt-0.5">{x.s}</div></div>)}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/[0.06]">
        {tabs.map(t=><button key={t.id} onClick={()=>setActiveTab(t.id)} className={`px-4 py-2.5 text-[11px] font-medium border-b-2 transition-all ${activeTab===t.id?"text-emerald-400 border-emerald-500/50":"text-white/40 border-transparent hover:text-white/60"}`}>{t.l}</button>)}
      </div>

      {/* RMF Tab */}
      {activeTab==="rmf"&&<div className="space-y-3">
        <div className="text-[9px] text-white/20 uppercase tracking-widest">NIST AI Risk Management Framework — 4 core functions</div>
        {RMF.map(fn=>{const Icon=fn.icon;const met=fn.subs.filter(s=>s.s==="met").length;const total=fn.subs.length;const pct=Math.round(met/total*100);const open=expandedRmf===fn.id;
        return(<div key={fn.id} className={`${G} rounded-lg overflow-hidden`}>
          <button onClick={()=>setExpandedRmf(open?null:fn.id)} className="w-full px-5 py-4 flex items-center gap-4 hover:bg-white/[0.02] transition-colors">
            <div className={`w-9 h-9 rounded-lg ${fn.bg} border ${fn.bd} flex items-center justify-center`}><Icon size={16} className={fn.color}/></div>
            <div className="flex-1 text-left"><div className={`text-[12px] font-semibold ${fn.color}`}>{fn.name}</div><div className="text-[10px] text-white/35">{fn.desc}</div></div>
            <span className="text-[9px] font-mono text-white/25">{met}/{total}</span>
            <div className="w-14 h-1.5 rounded-full bg-white/[0.06] overflow-hidden"><div className={`h-full rounded-full ${pct>=80?"bg-emerald-500":pct>=50?"bg-amber-500":"bg-red-500"}`} style={{width:`${pct}%`}}/></div>
            {open?<ChevronDown size={14} className="text-white/25"/>:<ChevronRight size={14} className="text-white/25"/>}
          </button>
          {open&&<div className="px-5 pb-5 space-y-3">
            <div><div className="text-[8px] uppercase tracking-widest text-white/20 mb-2">BBAP-Sec Features</div>
              {fn.features.map((f,i)=><div key={i} className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/[0.02] mb-1"><CheckCircle2 size={11} className="text-emerald-500/50 shrink-0"/><span className="text-[10px] text-white/55">{f}</span></div>)}</div>
            <div><div className="text-[8px] uppercase tracking-widest text-white/20 mb-2">Sub-category compliance</div>
              {fn.subs.map((sc,i)=><div key={i} className="flex items-center gap-3 px-3 py-1.5 rounded-md bg-white/[0.02] mb-1">
                {sc.s==="met"?<CheckCircle2 size={11} className="text-emerald-400 shrink-0"/>:<AlertTriangle size={11} className="text-amber-400 shrink-0"/>}
                <span className="text-[10px] font-mono text-white/40 w-20 shrink-0">{sc.id}</span>
                <span className="text-[10px] text-white/50 flex-1">{sc.n}</span>
                <span className={`text-[8px] font-mono px-1.5 py-0.5 rounded ${sc.s==="met"?"bg-emerald-500/10 text-emerald-400 border border-emerald-500/20":"bg-amber-500/10 text-amber-400 border border-amber-500/20"}`}>{sc.s}</span>
              </div>)}</div>
          </div>}
        </div>);})}
      </div>}

      {/* Controls Tab */}
      {activeTab==="controls"&&<div className="space-y-3">
        <div className="text-[9px] text-white/20 uppercase tracking-widest">Layered control framework — 4 domains</div>
        {CONTROLS.map((d,i)=>{const Icon=d.icon;return(
          <div key={i} className={`${G} rounded-lg p-5`}>
            <div className="flex items-center gap-3 mb-3"><div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center"><Icon size={15} className="text-white/40"/></div><span className="text-[12px] font-medium text-white/70">{d.name}</span><span className="text-[9px] text-white/20">{d.items.length} controls</span></div>
            <div className="grid grid-cols-3 gap-1.5">{d.items.map((c,j)=><div key={j} className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/[0.02]"><CheckCircle2 size={10} className="text-emerald-500/40 shrink-0"/><span className="text-[10px] text-white/50">{c}</span></div>)}</div>
          </div>
        );})}
      </div>}

      {/* Risk Scores Tab */}
      {activeTab==="risk"&&<div className="space-y-5">
        <div className="text-[9px] text-white/20 uppercase tracking-widest">Risk assessment — quantified scores from attack modules</div>
        <div className={`${G} rounded-lg p-6 text-center`}>
          <div className={`text-3xl font-bold font-mono ${SEV[ratingOf(composite)].tx}`}>{composite}</div>
          <div className="text-[10px] text-white/30 mt-1">Composite risk score (0–100)</div>
          <span className={`inline-block mt-2 text-[9px] font-mono px-2 py-0.5 rounded ${SEV[ratingOf(composite)].bg} ${SEV[ratingOf(composite)].tx} border ${SEV[ratingOf(composite)].bd}`}>{ratingOf(composite)}</span>
        </div>
        <div className="grid grid-cols-5 gap-3">
          {[{k:"adversarial",l:"Adversarial",w:1.0},{k:"poisoning",l:"Poisoning",w:1.2},{k:"evasion",l:"Evasion",w:0.8},{k:"extraction",l:"Extraction",w:1.0},{k:"injection",l:"Injection",w:1.5}].map(a=>{
            const sc=riskScores[a.k];const r=ratingOf(sc);const sv=SEV[r];
            return(<div key={a.k} className={`${G} rounded-lg p-4 text-center`}><div className={`text-xl font-bold font-mono ${sv.tx}`}>{sc}</div><div className="text-[10px] text-white/45 mt-1">{a.l}</div><div className="text-[8px] text-white/20 font-mono">weight: {a.w}</div><span className={`inline-block mt-2 text-[8px] font-mono px-1.5 py-0.5 rounded ${sv.bg} ${sv.tx} border ${sv.bd}`}>{r}</span></div>);
          })}
        </div>
        <div className={`${G} rounded-lg p-4`}>
          <div className="text-[9px] text-white/20 uppercase tracking-widest mb-2">Risk scoring formula</div>
          <div className="font-mono text-[10px] text-white/40 space-y-1">
            <div><span className="text-emerald-400">project_risk</span> = Σ(weight × risk_score) / Σ(weight)</div>
            <div><span className="text-emerald-400">adjusted_risk</span> = project_risk × (1 - pipeline_health / 200)</div>
          </div>
        </div>
      </div>}

      {/* Compliance Tab */}
      {activeTab==="compliance"&&<div className="space-y-3">
        <div className="text-[9px] text-white/20 uppercase tracking-widest">Multi-framework compliance mapping</div>
        {COMPLIANCE.map((fw,i)=>{const col=fw.cov>=80?"bg-emerald-500":fw.cov>=50?"bg-amber-500":"bg-red-500";const tc=fw.cov>=80?"text-emerald-400":fw.cov>=50?"text-amber-400":"text-red-400";
        return(<div key={i} className={`${G} rounded-lg px-5 py-4`}>
          <div className="flex items-center justify-between mb-2"><div><div className="text-[12px] font-medium text-white/80">{fw.name}</div><div className="text-[9px] font-mono text-white/20">{fw.ver}</div></div><span className={`text-[10px] font-mono px-2 py-0.5 rounded ${tc}`}>{fw.cov}%</span></div>
          <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden mb-1.5"><div className={`h-full rounded-full ${col}`} style={{width:`${fw.cov}%`}}/></div>
          <div className="text-[10px] text-white/25">{fw.detail}</div>
        </div>);})}

        <div className={`${G} rounded-lg p-5 mt-2`}>
          <div className="flex items-center gap-2 mb-3"><FileText size={14} className="text-white/40"/><span className="text-[12px] font-medium text-white/70">Assessment templates</span></div>
          {["AI Threat Model Template — threat-model-template.md","AI Risk Assessment Template — risk-assessment-template.md","AI Security Test Report — ai-security-test-report-template.md","Incident Response Playbook — incident-response-playbook-template.md"].map((t,i)=>
            <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-md bg-white/[0.02] hover:bg-white/[0.04] cursor-pointer transition-colors mb-1"><BookOpen size={11} className="text-emerald-500/40 shrink-0"/><span className="text-[10px] text-white/50 flex-1">{t}</span><ExternalLink size={10} className="text-white/15"/></div>
          )}
          <div className="text-[9px] text-white/20 mt-2">Templates are in <span className="font-mono">doc/templates/</span></div>
        </div>
      </div>}
    </div>
  );
}

/* ═══════════════════════════════════
   MONITORING PAGE
   ═══════════════════════════════════ */
function MonitoringPage() {
  const metrics = [
    {l:"Queries / min",v:"842",trend:"+12%",dir:"up",status:"normal"},
    {l:"Avg Latency",v:"45ms",trend:"-3ms",dir:"down",status:"normal"},
    {l:"Error Rate",v:"0.02%",trend:"stable",dir:"flat",status:"normal"},
    {l:"Blocked Requests",v:"23",trend:"+5 today",dir:"up",status:"warning"},
    {l:"Model Accuracy",v:"97.8%",trend:"-0.3%",dir:"down",status:"normal"},
    {l:"Drift Score",v:"0.04",trend:"below threshold",dir:"flat",status:"normal"},
  ];

  const recentEvents = [
    {time:"2 min ago", event:"Rate limit triggered — 5 requests blocked from 192.168.1.42", sev:"warning"},
    {time:"14 min ago", event:"Model accuracy check passed — 97.8% on validation set", sev:"ok"},
    {time:"1 hr ago", event:"Drift score computed — 0.04 (threshold: 0.1)", sev:"ok"},
    {time:"3 hr ago", event:"Sandbox bbap-sbx-001 health check passed", sev:"ok"},
    {time:"5 hr ago", event:"Unusual query pattern detected — 340 sequential requests", sev:"warning"},
  ];

  return (
    <div className="space-y-5">
      <div><h1 className="text-xl font-semibold text-white mb-0.5">Monitoring</h1><p className="text-sm text-white/35">Real-time system metrics and activity tracking</p></div>

      <div className="grid grid-cols-3 gap-3">
        {metrics.map(m=>{
          const DirIcon = m.dir==="up"?TrendingUp:m.dir==="down"?TrendingDown:Minus;
          return(<div key={m.l} className={`${G} rounded-lg p-4`}>
            <div className="text-[9px] text-white/25 uppercase tracking-wider mb-2">{m.l}</div>
            <div className="text-xl font-semibold text-white/90 mb-1">{m.v}</div>
            <div className={`flex items-center gap-1.5 text-[10px] font-mono ${m.status==="warning"?"text-amber-400":"text-white/30"}`}>
              <DirIcon size={11}/>{m.trend}
            </div>
          </div>);
        })}
      </div>

      <div className={`${G} rounded-lg p-5`}>
        <div className="text-[9px] font-semibold text-white/25 uppercase tracking-widest mb-3">Recent events</div>
        <div className="space-y-2">
          {recentEvents.map((e,i)=>(
            <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-md bg-white/[0.02]">
              <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${e.sev==="warning"?"bg-amber-400":"bg-emerald-400"}`}/>
              <span className="text-[10px] font-mono text-white/20 w-20 shrink-0">{e.time}</span>
              <span className="text-[10px] text-white/55 flex-1">{e.event}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={`${G} rounded-lg p-5`}>
        <div className="text-[9px] font-semibold text-white/25 uppercase tracking-widest mb-3">Active sandbox resources</div>
        <div className="grid grid-cols-4 gap-4">
          {[{l:"CPU",v:"24%",c:"text-emerald-400"},{l:"Memory",v:"1.2 GB",c:"text-blue-400"},{l:"GPU",v:"38%",c:"text-violet-400"},{l:"Disk",v:"840 MB",c:"text-amber-400"}].map(r=>
            <div key={r.l}><div className="text-[9px] text-white/20 uppercase tracking-wider">{r.l}</div><div className={`text-lg font-semibold font-mono ${r.c} mt-1`}>{r.v}</div></div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   PLACEHOLDER PAGES
   ═══════════════════════════════════ */
function PlaceholderPage({ title, desc }) {
  return (
    <div className="space-y-5">
      <div><h1 className="text-xl font-semibold text-white mb-0.5">{title}</h1><p className="text-sm text-white/35">{desc}</p></div>
      <div className={`${G} rounded-lg p-10 text-center`}><Shield size={32} className="text-white/10 mx-auto mb-3" /><p className="text-sm text-white/25">Section ready for implementation</p></div>
    </div>
  );
}

/* ═══════════════════════════════════
   MAIN APP
   ═══════════════════════════════════ */
export default function App() {
  const [page, setPage] = useState("overview");
  const [engagements, setEngagements] = useState(MOCK_ENGAGEMENTS);
  const [engagementId, setEngagementId] = useState(MOCK_ENGAGEMENTS[0].id);
  const engagement = engagements.find(e => e.id === engagementId) || engagements[0];

  const handleNewEngagement = () => {
    const name = prompt("Engagement name:");
    if (!name) return;
    const newEng = {
      id: Math.max(...engagements.map(e => e.id)) + 1,
      name,
      target_type: "api_endpoint",
      target_config: {},
      scope: [],
      status: "active",
      risk_score: 0,
    };
    setEngagements([...engagements, newEng]);
    setEngagementId(newEng.id);
    setPage("target");
  };

  const getContent = () => {
    if (page === "overview") return <OverviewPage engagement={engagement} />;
    if (page === "target") return <TargetPage engagement={engagement} />;
    if (page.startsWith("layer_")) return <LayerPage layerKey={page.replace("layer_", "")} engagement={engagement} />;
    if (page === "findings") return <FindingsPage />;
    if (page === "report") return <ReportPage engagement={engagement} />;
    if (page === "governance") return <GovernancePage engagement={engagement} />;
    if (page === "monitoring") return <MonitoringPage />;
    if (page === "pipeline_checks") return <PlaceholderPage title="Secure Pipeline" desc="46 security controls across 5 stages" />;
    if (page === "atlas") return <AtlasPage />;
    if (page === "team") return <PlaceholderPage title="Team" desc="User management and engagement assignments" />;
    if (page === "knowledge") return <PlaceholderPage title="Knowledge Base" desc="Notes, policies, and templates" />;
    if (page === "alerts") return <PlaceholderPage title="Alerts" desc="Severity-based notifications" />;
    if (page === "settings") return <PlaceholderPage title="Settings" desc="API keys, sandbox config, audit log" />;
    return <OverviewPage engagement={engagement} />;
  };

  return (
    <div className="flex h-screen bg-[#080b12] text-white overflow-hidden" style={{ fontFamily: "'DM Sans',system-ui,sans-serif" }}>
      <div className="fixed inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 60% 40% at 20% 10%,rgba(46,204,113,0.03),transparent),radial-gradient(ellipse 50% 50% at 80% 80%,rgba(184,115,51,0.02),transparent)" }} />
      <Sidebar page={page} setPage={setPage} engagement={engagement}
        engagements={engagements} onSelectEngagement={setEngagementId} onNewEngagement={handleNewEngagement} />
      <main className="flex-1 overflow-y-auto relative z-10 p-6 pb-20">{getContent()}</main>
    </div>
  );
}

/**
 * BBAP-Sec AI Attack Lab — Governance Page Component
 * ===================================================
 * AI Risk Management & Governance dashboard page.
 * Implements NIST AI RMF alignment, governance controls,
 * risk scoring, and compliance tracking.
 *
 * Add to the sidebar navigation in BBAP-Sec-Dashboard_v1.jsx:
 *   {id:"governance",l:"Governance",I:ShieldCheck}
 *
 * Add to the page map in App():
 *   governance:<GovernancePage pid={project?.id} stats={stats} pipeline={pipeline}/>,
 */

import { useState, useEffect, useMemo } from "react";
import {
  Shield, ShieldCheck, ShieldAlert, CheckCircle2, XCircle, AlertTriangle,
  FileText, ChevronDown, ChevronRight, ExternalLink, Download,
  Layers, Target, Activity, Globe, Lock, Database, Cpu, Filter,
  BookOpen, Users, Bell, Settings, Zap, BarChart3
} from "lucide-react";

/* ── Design tokens (matching BBAP-Sec-Dashboard_v1.jsx) ── */
const G  = "bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]";
const GS = "bg-white/[0.06] backdrop-blur-xl border border-white/[0.1]";

const RATING_COLORS = {
  low:      { bg: "bg-emerald-500/10", bd: "border-emerald-500/20", tx: "text-emerald-400", dot: "bg-emerald-400" },
  medium:   { bg: "bg-amber-500/10",   bd: "border-amber-500/20",   tx: "text-amber-400",   dot: "bg-amber-400"   },
  high:     { bg: "bg-orange-500/10",  bd: "border-orange-500/20",  tx: "text-orange-400",  dot: "bg-orange-400"  },
  critical: { bg: "bg-red-500/10",     bd: "border-red-500/20",     tx: "text-red-400",     dot: "bg-red-400"     },
};

/* ── NIST AI RMF Data ── */
const RMF_FUNCTIONS = [
  {
    id: "govern",
    name: "GOVERN",
    icon: Users,
    color: "text-violet-400",
    colorBg: "bg-violet-500/10",
    colorBd: "border-violet-500/20",
    description: "Policies, processes, and accountability structures",
    features: [
      { name: "User Management", detail: "Admin/analyst/viewer roles with MFA", sub: "GOVERN 2.1" },
      { name: "Knowledge Base", detail: "Policy documentation with tagging", sub: "GOVERN 1.1" },
      { name: "Audit Trail", detail: "Activity logging in Settings", sub: "GOVERN 1.6" },
      { name: "Pipeline: Authentication", detail: "OAuth2/JWT enforcement", sub: "GOVERN 2.1" },
      { name: "Pipeline: Supply Chain Audit", detail: "Dependency verification", sub: "GOVERN 1.7" },
    ],
    subCategories: [
      { id: "GOVERN 1.1", name: "Legal/regulatory requirements documented", status: "partial" },
      { id: "GOVERN 1.2", name: "Trustworthy AI in policies", status: "met" },
      { id: "GOVERN 1.3", name: "Risk tolerance defined", status: "met" },
      { id: "GOVERN 1.6", name: "Policies transparent and documented", status: "partial" },
      { id: "GOVERN 1.7", name: "Supply chain risks managed", status: "met" },
      { id: "GOVERN 2.1", name: "Roles and responsibilities defined", status: "met" },
      { id: "GOVERN 2.2", name: "Personnel trained", status: "partial" },
    ],
  },
  {
    id: "map",
    name: "MAP",
    icon: Target,
    color: "text-cyan-400",
    colorBg: "bg-cyan-500/10",
    colorBd: "border-cyan-500/20",
    description: "Identifying and contextualizing AI risks",
    features: [
      { name: "Secure Pipeline", detail: "5-stage architecture checks (46 controls)", sub: "MAP 1.1" },
      { name: "ATLAS Intel", detail: "170 techniques, 16 tactics indexed", sub: "MAP 2.1" },
      { name: "Project Management", detail: "Per-project risk scoping", sub: "MAP 1.1" },
      { name: "Pipeline: PII Scan", detail: "Personal data identification", sub: "MAP 1.6" },
      { name: "Pipeline: Source Auth", detail: "Data provenance tracking", sub: "MAP 1.2" },
    ],
    subCategories: [
      { id: "MAP 1.1", name: "Intended purposes documented", status: "met" },
      { id: "MAP 1.2", name: "Data sources documented", status: "met" },
      { id: "MAP 1.5", name: "Input data quality assessed", status: "met" },
      { id: "MAP 1.6", name: "Privacy risks identified", status: "met" },
      { id: "MAP 2.1", name: "AI risks identified and categorized", status: "met" },
      { id: "MAP 3.1", name: "Benefits and costs assessed", status: "partial" },
      { id: "MAP 3.4", name: "Supply chain risks mapped", status: "met" },
    ],
  },
  {
    id: "measure",
    name: "MEASURE",
    icon: BarChart3,
    color: "text-emerald-400",
    colorBg: "bg-emerald-500/10",
    colorBd: "border-emerald-500/20",
    description: "Quantifying and benchmarking AI risks",
    features: [
      { name: "Adversarial Attacks", detail: "FGSM/PGD at configurable epsilon", sub: "MEASURE 2.5" },
      { name: "Data Poisoning", detail: "Label-flip and backdoor testing", sub: "MEASURE 2.6" },
      { name: "Evasion Attacks", detail: "Pixel, noise, spatial methods", sub: "MEASURE 2.5" },
      { name: "Model Extraction", detail: "Random and active learning", sub: "MEASURE 2.5" },
      { name: "Prompt Injection", detail: "10-attack catalog across 5 categories", sub: "MEASURE 2.5" },
      { name: "Results & Reports", detail: "Quantified metric collection", sub: "MEASURE 1.1" },
    ],
    subCategories: [
      { id: "MEASURE 1.1", name: "Measurement approaches established", status: "met" },
      { id: "MEASURE 2.5", name: "Adversarial robustness tested", status: "met" },
      { id: "MEASURE 2.6", name: "Bias and fairness tested", status: "partial" },
      { id: "MEASURE 2.7", name: "Safety and security tested", status: "met" },
    ],
  },
  {
    id: "manage",
    name: "MANAGE",
    icon: Shield,
    color: "text-rose-400",
    colorBg: "bg-rose-500/10",
    colorBd: "border-rose-500/20",
    description: "Responding to, recovering from, and communicating about AI risks",
    features: [
      { name: "Alerts", detail: "Severity-based incident tracking", sub: "MANAGE 1.1" },
      { name: "Pipeline Remediation", detail: "Control status tracking", sub: "MANAGE 1.1" },
      { name: "Knowledge Base", detail: "Lessons learned documentation", sub: "MANAGE 1.1" },
      { name: "Export Reports", detail: "Stakeholder-ready JSON reports", sub: "MANAGE 4.1" },
      { name: "Monitoring", detail: "Query rates, latency, drift", sub: "MANAGE 2.1" },
    ],
    subCategories: [
      { id: "MANAGE 1.1", name: "Risk treatment plans defined", status: "met" },
      { id: "MANAGE 2.1", name: "AI system monitored", status: "met" },
      { id: "MANAGE 4.1", name: "Results communicated", status: "met" },
    ],
  },
];

const CONTROL_DOMAINS = [
  {
    name: "Input Controls",
    icon: Database,
    controls: [
      { name: "Data validation", stage: "Data Ingestion", rmf: "MAP 1.5" },
      { name: "Poison detection", stage: "Data Ingestion", rmf: "MAP 2.1" },
      { name: "PII scanning", stage: "Data Ingestion", rmf: "GOVERN 1.1" },
      { name: "Source authentication", stage: "Data Ingestion", rmf: "GOVERN 1.4" },
      { name: "Prompt filtering", stage: "Prompt Filtering", rmf: "MEASURE 2.5" },
      { name: "Injection detection", stage: "Prompt Filtering", rmf: "MEASURE 2.5" },
      { name: "Encoding bypass prevention", stage: "Prompt Filtering", rmf: "MEASURE 2.5" },
    ],
  },
  {
    name: "Model Controls",
    icon: Cpu,
    controls: [
      { name: "Adversarial robustness", stage: "Model Validation", rmf: "MEASURE 2.5" },
      { name: "Backdoor detection", stage: "Model Validation", rmf: "MEASURE 2.5" },
      { name: "Architecture review", stage: "Model Validation", rmf: "MAP 1.1" },
      { name: "Weight integrity", stage: "Model Validation", rmf: "MEASURE 2.5" },
      { name: "Version control", stage: "Model Validation", rmf: "GOVERN 1.2" },
      { name: "Supply chain audit", stage: "Model Validation", rmf: "MAP 3.4" },
    ],
  },
  {
    name: "Output Controls",
    icon: Filter,
    controls: [
      { name: "Output guardrails", stage: "Monitoring", rmf: "MEASURE 2.5" },
      { name: "Response watermarking", stage: "Monitoring", rmf: "GOVERN 1.2" },
      { name: "Output truncation", stage: "Monitoring", rmf: "MANAGE 2.1" },
      { name: "Context isolation", stage: "Monitoring", rmf: "MEASURE 2.5" },
    ],
  },
  {
    name: "Infrastructure Controls",
    icon: Globe,
    controls: [
      { name: "Authentication (OAuth2/JWT)", stage: "API Security", rmf: "GOVERN 2.1" },
      { name: "Rate limiting", stage: "API Security", rmf: "MANAGE 2.1" },
      { name: "Encryption at rest", stage: "API Security", rmf: "GOVERN 1.1" },
      { name: "Query logging", stage: "Monitoring", rmf: "MANAGE 2.1" },
      { name: "TLS enforcement", stage: "API Security", rmf: "GOVERN 1.1" },
      { name: "Audit trail", stage: "Monitoring", rmf: "GOVERN 1.6" },
    ],
  },
];

const COMPLIANCE_FRAMEWORKS = [
  { name: "NIST AI RMF", version: "1.0 (2023)", coverage: 85, details: "4 functions, 13+ sub-categories" },
  { name: "MITRE ATLAS", version: "5.6.0 (2025)", coverage: 50, details: "8/16 tactics covered" },
  { name: "OWASP LLM Top 10", version: "2025", coverage: 60, details: "LLM01, LLM02, LLM07 covered" },
  { name: "EU AI Act", version: "2024", coverage: 45, details: "Risk classification, documentation, robustness" },
  { name: "ISO/IEC 42001", version: "2023", coverage: 55, details: "Pipeline controls, roles, audit" },
];


/* ── Helper: risk rating from score ── */
function riskRating(score) {
  if (score <= 15) return "low";
  if (score <= 40) return "medium";
  if (score <= 70) return "high";
  return "critical";
}

/* ── Sub-components ── */

function RMFCard({ fn, expanded, onToggle }) {
  const Icon = fn.icon;
  const metCount = fn.subCategories.filter(s => s.status === "met").length;
  const total = fn.subCategories.length;
  const pct = Math.round((metCount / total) * 100);

  return (
    <div className={`${G} rounded-lg overflow-hidden`}>
      <button
        onClick={onToggle}
        className="w-full px-5 py-4 flex items-center gap-4 hover:bg-white/[0.02] transition-colors"
      >
        <div className={`w-10 h-10 rounded-lg ${fn.colorBg} border ${fn.colorBd} flex items-center justify-center`}>
          <Icon size={18} className={fn.color} />
        </div>
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-semibold ${fn.color}`}>{fn.name}</span>
            <span className="text-[10px] text-white/30 font-mono">{metCount}/{total} sub-categories</span>
          </div>
          <div className="text-[11px] text-white/40">{fn.description}</div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-16 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className={`h-full rounded-full ${pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500"}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-[11px] font-mono text-white/40 w-8 text-right">{pct}%</span>
          {expanded ? <ChevronDown size={14} className="text-white/25" /> : <ChevronRight size={14} className="text-white/25" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4">
          {/* Features */}
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 mb-2">BBAP-Sec Features</div>
            <div className="space-y-1.5">
              {fn.features.map((f, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-md bg-white/[0.02]">
                  <CheckCircle2 size={12} className="text-emerald-500/60 shrink-0" />
                  <span className="text-[11px] text-white/70 flex-1">{f.name}</span>
                  <span className="text-[10px] text-white/30 font-mono">{f.detail}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${fn.colorBg} ${fn.color} border ${fn.colorBd}`}>
                    {f.sub}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Sub-categories */}
          <div>
            <div className="text-[9px] uppercase tracking-widest text-white/25 mb-2">Sub-Category Compliance</div>
            <div className="space-y-1">
              {fn.subCategories.map((sc, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-1.5 rounded-md bg-white/[0.02]">
                  {sc.status === "met" ? (
                    <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                  ) : sc.status === "partial" ? (
                    <AlertTriangle size={12} className="text-amber-400 shrink-0" />
                  ) : (
                    <XCircle size={12} className="text-red-400 shrink-0" />
                  )}
                  <span className="text-[11px] font-mono text-white/50 w-24 shrink-0">{sc.id}</span>
                  <span className="text-[11px] text-white/60 flex-1">{sc.name}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    sc.status === "met"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : sc.status === "partial"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                  }`}>
                    {sc.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ControlDomainCard({ domain, pipeline }) {
  const [open, setOpen] = useState(false);
  const Icon = domain.icon;

  /* Match controls to pipeline check status if available */
  const getStatus = (controlName) => {
    if (!pipeline || pipeline.length === 0) return null;
    for (const stage of pipeline) {
      const check = (stage.checks || []).find(
        c => c.check_name?.toLowerCase().includes(controlName.toLowerCase().split(" ")[0])
      );
      if (check) return check.passed;
    }
    return null;
  };

  return (
    <div className={`${G} rounded-lg overflow-hidden`}>
      <button onClick={() => setOpen(!open)} className="w-full px-5 py-4 flex items-center gap-3 hover:bg-white/[0.02] transition-colors">
        <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center">
          <Icon size={15} className="text-white/40" />
        </div>
        <div className="flex-1 text-left">
          <div className="text-[13px] font-medium text-white/80">{domain.name}</div>
          <div className="text-[10px] text-white/30">{domain.controls.length} controls</div>
        </div>
        {open ? <ChevronDown size={14} className="text-white/25" /> : <ChevronRight size={14} className="text-white/25" />}
      </button>
      {open && (
        <div className="px-5 pb-4 space-y-1">
          {domain.controls.map((c, i) => {
            const status = getStatus(c.name);
            return (
              <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-md bg-white/[0.02]">
                {status === true ? (
                  <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                ) : status === false ? (
                  <XCircle size={12} className="text-red-400 shrink-0" />
                ) : (
                  <div className="w-3 h-3 rounded-full bg-white/[0.08] shrink-0" />
                )}
                <span className="text-[11px] text-white/60 flex-1">{c.name}</span>
                <span className="text-[9px] font-mono text-white/25 px-1.5 py-0.5 rounded bg-white/[0.03]">{c.stage}</span>
                <span className="text-[9px] font-mono text-white/20">{c.rmf}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ComplianceBar({ fw }) {
  const r = fw.coverage >= 80 ? RATING_COLORS.low : fw.coverage >= 50 ? RATING_COLORS.medium : RATING_COLORS.high;
  return (
    <div className={`${G} rounded-lg px-5 py-4`}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-[12px] font-medium text-white/80">{fw.name}</div>
          <div className="text-[9px] font-mono text-white/25">{fw.version}</div>
        </div>
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${r.bg} ${r.tx} border ${r.bd}`}>
          {fw.coverage}%
        </span>
      </div>
      <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden mb-1.5">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            fw.coverage >= 80 ? "bg-emerald-500" : fw.coverage >= 50 ? "bg-amber-500" : "bg-red-500"
          }`}
          style={{ width: `${fw.coverage}%` }}
        />
      </div>
      <div className="text-[10px] text-white/30">{fw.details}</div>
    </div>
  );
}

function RiskScoreGauge({ score, label }) {
  const rating = riskRating(score);
  const r = RATING_COLORS[rating];
  const angle = (score / 100) * 180;

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-14 overflow-hidden">
        <svg viewBox="0 0 120 60" className="w-full h-full">
          <path d="M 10 55 A 50 50 0 0 1 110 55" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" strokeLinecap="round" />
          <path
            d="M 10 55 A 50 50 0 0 1 110 55"
            fill="none"
            stroke={rating === "low" ? "#10b981" : rating === "medium" ? "#f59e0b" : rating === "high" ? "#f97316" : "#ef4444"}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * 157} 157`}
          />
        </svg>
        <div className="absolute inset-0 flex items-end justify-center pb-0.5">
          <span className={`text-lg font-bold font-mono ${r.tx}`}>{score}</span>
        </div>
      </div>
      <span className={`text-[9px] font-mono uppercase tracking-wider mt-1 px-2 py-0.5 rounded ${r.bg} ${r.tx} border ${r.bd}`}>
        {rating}
      </span>
      <span className="text-[10px] text-white/30 mt-1">{label}</span>
    </div>
  );
}


/* ═══════════════════════════════════
   GOVERNANCE PAGE (main export)
   ═══════════════════════════════════ */
export default function GovernancePage({ pid, stats, pipeline }) {
  const [activeTab, setActiveTab] = useState("rmf");
  const [expandedRmf, setExpandedRmf] = useState(null);

  /* Compute overall metrics */
  const totalSubs = RMF_FUNCTIONS.reduce((s, f) => s + f.subCategories.length, 0);
  const metSubs = RMF_FUNCTIONS.reduce((s, f) => s + f.subCategories.filter(sc => sc.status === "met").length, 0);
  const partialSubs = RMF_FUNCTIONS.reduce((s, f) => s + f.subCategories.filter(sc => sc.status === "partial").length, 0);
  const overallPct = Math.round((metSubs / totalSubs) * 100);
  const pipelineHealth = stats?.pipeline_health || 0;

  /* Mock risk scores (in production these come from /api/v2/projects/<id>/risk-scores) */
  const riskScores = {
    adversarial: 33,
    poisoning: 22,
    evasion: 15,
    extraction: 28,
    injection: 45,
    composite: 30,
  };

  const tabs = [
    { id: "rmf", label: "NIST AI RMF", icon: ShieldCheck },
    { id: "controls", label: "Controls", icon: Layers },
    { id: "risk", label: "Risk Scores", icon: BarChart3 },
    { id: "compliance", label: "Compliance", icon: Globe },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white mb-1">AI Risk Management & Governance</h1>
          <p className="text-sm text-white/40">NIST AI RMF alignment, controls framework, and compliance tracking</p>
        </div>
        <div className="flex gap-2">
          <a
            href="/api/atlas/report"
            target="_blank"
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-white/[0.04] text-white/50 text-[11px] hover:bg-white/[0.08] border border-white/[0.06]"
          >
            <Download size={13} />Export Report
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3">
        <div className={`${G} rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck size={14} className="text-emerald-400" />
            <span className="text-[9px] uppercase tracking-widest text-white/25">RMF Coverage</span>
          </div>
          <div className="text-2xl font-bold font-mono text-white">{overallPct}%</div>
          <div className="text-[10px] text-white/30">{metSubs}/{totalSubs} sub-categories met</div>
        </div>
        <div className={`${G} rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <Layers size={14} className="text-cyan-400" />
            <span className="text-[9px] uppercase tracking-widest text-white/25">Pipeline Health</span>
          </div>
          <div className="text-2xl font-bold font-mono text-white">{pipelineHealth}%</div>
          <div className="text-[10px] text-white/30">{stats?.passed_checks || 0}/{stats?.total_checks || 46} controls passing</div>
        </div>
        <div className={`${G} rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-amber-400" />
            <span className="text-[9px] uppercase tracking-widest text-white/25">Partial</span>
          </div>
          <div className="text-2xl font-bold font-mono text-white">{partialSubs}</div>
          <div className="text-[10px] text-white/30">sub-categories need attention</div>
        </div>
        <div className={`${G} rounded-lg p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <Globe size={14} className="text-rose-400" />
            <span className="text-[9px] uppercase tracking-widest text-white/25">Frameworks</span>
          </div>
          <div className="text-2xl font-bold font-mono text-white">{COMPLIANCE_FRAMEWORKS.length}</div>
          <div className="text-[10px] text-white/30">compliance mappings tracked</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-white/[0.06] pb-0">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-[11px] font-medium transition-all border-b-2 ${
              activeTab === t.id
                ? "text-emerald-400 border-emerald-500/50"
                : "text-white/40 border-transparent hover:text-white/60"
            }`}
          >
            <t.icon size={13} />{t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "rmf" && (
        <div className="space-y-3">
          <div className="text-[10px] text-white/25 uppercase tracking-widest">
            NIST AI Risk Management Framework — 4 Core Functions
          </div>
          {RMF_FUNCTIONS.map(fn => (
            <RMFCard
              key={fn.id}
              fn={fn}
              expanded={expandedRmf === fn.id}
              onToggle={() => setExpandedRmf(expandedRmf === fn.id ? null : fn.id)}
            />
          ))}
        </div>
      )}

      {activeTab === "controls" && (
        <div className="space-y-3">
          <div className="text-[10px] text-white/25 uppercase tracking-widest">
            Layered Control Framework — 4 Domains, {CONTROL_DOMAINS.reduce((s, d) => s + d.controls.length, 0)} Controls
          </div>
          {CONTROL_DOMAINS.map((domain, i) => (
            <ControlDomainCard key={i} domain={domain} pipeline={pipeline} />
          ))}
        </div>
      )}

      {activeTab === "risk" && (
        <div className="space-y-5">
          <div className="text-[10px] text-white/25 uppercase tracking-widest">
            Risk Assessment — Quantified Scores from Attack Modules
          </div>

          {/* Composite gauge */}
          <div className={`${G} rounded-lg p-6 flex items-center justify-center`}>
            <RiskScoreGauge score={riskScores.composite} label="Composite Risk Score" />
          </div>

          {/* Per-attack scores */}
          <div className="grid grid-cols-5 gap-3">
            {[
              { key: "adversarial", label: "Adversarial", weight: 1.0 },
              { key: "poisoning", label: "Poisoning", weight: 1.2 },
              { key: "evasion", label: "Evasion", weight: 0.8 },
              { key: "extraction", label: "Extraction", weight: 1.0 },
              { key: "injection", label: "Injection", weight: 1.5 },
            ].map(a => {
              const score = riskScores[a.key];
              const rating = riskRating(score);
              const r = RATING_COLORS[rating];
              return (
                <div key={a.key} className={`${G} rounded-lg p-4 text-center`}>
                  <div className={`text-xl font-bold font-mono ${r.tx}`}>{score}</div>
                  <div className="text-[10px] text-white/50 mt-1">{a.label}</div>
                  <div className="text-[9px] text-white/20 font-mono">weight: {a.weight}</div>
                  <span className={`inline-block mt-2 text-[9px] font-mono px-1.5 py-0.5 rounded ${r.bg} ${r.tx} border ${r.bd}`}>
                    {rating}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Risk formula reference */}
          <div className={`${G} rounded-lg p-5`}>
            <div className="text-[10px] uppercase tracking-widest text-white/25 mb-3">Risk Scoring Formula</div>
            <div className="font-mono text-[11px] text-white/50 space-y-1.5">
              <div><span className="text-emerald-400">project_risk</span> = Σ(weight × risk_score) / Σ(weight)</div>
              <div><span className="text-emerald-400">adjusted_risk</span> = project_risk × (1 - pipeline_health / 200)</div>
            </div>
            <div className="mt-3 text-[10px] text-white/30">
              Pipeline health of {pipelineHealth}% provides a {Math.round(pipelineHealth / 2)}% risk reduction multiplier.
            </div>
          </div>
        </div>
      )}

      {activeTab === "compliance" && (
        <div className="space-y-3">
          <div className="text-[10px] text-white/25 uppercase tracking-widest">
            Multi-Framework Compliance Mapping
          </div>
          {COMPLIANCE_FRAMEWORKS.map((fw, i) => (
            <ComplianceBar key={i} fw={fw} />
          ))}

          {/* Templates reference */}
          <div className={`${G} rounded-lg p-5 mt-4`}>
            <div className="flex items-center gap-2 mb-3">
              <FileText size={14} className="text-white/40" />
              <span className="text-[12px] font-medium text-white/70">Assessment Templates</span>
            </div>
            <div className="space-y-2">
              {[
                { name: "AI Threat Model Template", file: "threat-model-template.md" },
                { name: "AI Risk Assessment Template", file: "risk-assessment-template.md" },
                { name: "AI Security Test Report Template", file: "ai-security-test-report-template.md" },
                { name: "Incident Response Playbook", file: "incident-response-playbook-template.md" },
              ].map((t, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-md bg-white/[0.02] hover:bg-white/[0.04] cursor-pointer transition-colors">
                  <BookOpen size={12} className="text-emerald-500/50 shrink-0" />
                  <span className="text-[11px] text-white/60 flex-1">{t.name}</span>
                  <span className="text-[9px] font-mono text-white/20">{t.file}</span>
                  <ExternalLink size={11} className="text-white/15" />
                </div>
              ))}
            </div>
            <div className="text-[10px] text-white/25 mt-3">
              Templates are available in <span className="font-mono">doc/templates/</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

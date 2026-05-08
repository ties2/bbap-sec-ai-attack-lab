import { useState, useEffect, useCallback } from "react";
import {
  Shield, ShieldCheck, ShieldAlert, Activity, Users, BookOpen, Bell, Settings,
  ChevronRight, Plus, Trash2, Edit3, Search, Check, AlertTriangle,
  Lock, Unlock, Database, Cpu, FileText, Layers, Filter,
  Mail, UserPlus, Key, Globe, Zap, Download, ExternalLink,
  CheckCircle2, XCircle, ChevronDown, LayoutDashboard, Play, Loader2, Target
} from "lucide-react";

/* ── API helpers ── */
const API2 = "/api/v2";
const api = {
  get: u => fetch(API2+u).then(r=>r.json()),
  post: (u,b) => fetch(API2+u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>r.json()),
  put: (u,b) => fetch(API2+u,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(r=>r.json()),
  del: u => fetch(API2+u,{method:"DELETE"}).then(r=>r.json()),
};
/* ATLAS uses /api/atlas (not v2) */
const atlas = { get: u => fetch("/api/atlas"+u).then(r=>r.json()) };

/* ── Design tokens ── */
const G  = "bg-white/[0.04] backdrop-blur-xl border border-white/[0.08]";
const GS = "bg-white/[0.06] backdrop-blur-xl border border-white/[0.1]";
const SV = {
  critical:{bg:"bg-red-500/10",bd:"border-red-500/20",tx:"text-red-400",dt:"bg-red-400"},
  high:{bg:"bg-orange-500/10",bd:"border-orange-500/20",tx:"text-orange-400",dt:"bg-orange-400"},
  medium:{bg:"bg-amber-500/10",bd:"border-amber-500/20",tx:"text-amber-400",dt:"bg-amber-400"},
  low:{bg:"bg-blue-500/10",bd:"border-blue-500/20",tx:"text-blue-400",dt:"bg-blue-400"},
};
const STG = [
  {k:"data_ingestion",l:"Data Ingestion",I:Database},
  {k:"model_validation",l:"Model Validation",I:Cpu},
  {k:"prompt_filtering",l:"Prompt Filtering",I:Filter},
  {k:"api_security",l:"API Security",I:Globe},
  {k:"monitoring",l:"Monitoring",I:Activity},
];
const ATK = [
  {id:"adversarial",l:"Adversarial",t:"ADV",f:[{k:"attack",l:"Method",ty:"select",o:[["fgsm","FGSM"],["pgd","PGD"]],d:"fgsm"},{k:"epsilon",l:"Epsilon",ty:"number",d:0.03,s:0.01}]},
  {id:"data_poisoning",l:"Data Poisoning",t:"PSN",f:[{k:"strategy",l:"Strategy",ty:"select",o:[["label_flip","Label Flip"],["backdoor","Backdoor"]],d:"label_flip"},{k:"poison_rate",l:"Poison Rate",ty:"number",d:0.1,s:0.05}]},
  {id:"evasion",l:"Evasion",t:"EVA",f:[{k:"method",l:"Method",ty:"select",o:[["pixel","Pixel"],["noise","Noise"],["spatial","Spatial"]],d:"pixel"}]},
  {id:"model_extraction",l:"Model Extraction",t:"EXT",f:[{k:"queries",l:"Queries",ty:"number",d:500,s:100}]},
  {id:"prompt_injection",l:"Prompt Injection",t:"INJ",f:[],link:true},
];
const MOD_LABELS = {adversarial:"Adversarial",data_poisoning:"Data Poisoning",evasion:"Evasion",model_extraction:"Model Extraction",prompt_injection:"Prompt Injection"};

/* ═══════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════ */
function Sidebar({page,setPage,project,projects,setProject,setShowNew,ac}){
  const nav=[
    {id:"dashboard",l:"Dashboard",I:LayoutDashboard},
    {id:"pipeline",l:"Secure Pipeline",I:Layers},
    {id:"attacks",l:"Run Attacks",I:ShieldAlert},
    {id:"atlas",l:"ATLAS Intel",I:Target},
    {id:"results",l:"Results & Reports",I:FileText},
    {id:"monitoring",l:"Monitoring",I:Activity},
    {id:"users",l:"Users",I:Users},
    {id:"knowledge",l:"Knowledge Base",I:BookOpen},
    {id:"alerts",l:"Alerts",I:Bell,b:ac},
    {id:"settings",l:"Settings",I:Settings},
  ];
  return(
    <aside className="w-[220px] shrink-0 h-screen flex flex-col border-r border-white/[0.06] bg-white/[0.02]">
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <img src="/logo.png" alt="BBAP-Sec" className="w-9 h-9 rounded-md object-cover" onError={e=>{e.target.style.display='none';e.target.nextSibling.style.display='flex';}}/>
          <div className="w-9 h-9 rounded-md bg-gradient-to-br from-emerald-600 to-emerald-400 items-center justify-center font-mono text-xs font-bold text-white hidden">B</div>
          <div><div className="text-sm font-semibold text-white">BBAP-Sec</div><div className="text-[9px] text-white/30 uppercase tracking-[0.2em]">AI Security</div></div>
        </div>
        <div className="text-[9px] text-white/25 uppercase tracking-widest mb-1.5">Project</div>
        <select value={project?.id||""} onChange={e=>{const p=projects.find(x=>x.id===+e.target.value);if(p)setProject(p);}} className="w-full px-2 py-1.5 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[11px] font-mono focus:outline-none focus:border-emerald-500/30">
          {projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <button onClick={()=>setShowNew(true)} className="w-full mt-1.5 flex items-center justify-center gap-1.5 px-2 py-1 rounded-md border border-dashed border-white/[0.08] text-[10px] text-white/30 hover:text-white/50 hover:border-white/[0.15] transition-colors"><Plus size={10}/>New Project</button>
      </div>
      <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
        {nav.map(n=>(
          <button key={n.id} onClick={()=>setPage(n.id)} className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-[12px] font-medium transition-all ${page===n.id?"bg-emerald-500/12 text-emerald-400 border border-emerald-500/20":"text-white/50 hover:text-white/80 hover:bg-white/[0.04] border border-transparent"}`}>
            <n.I size={15} strokeWidth={1.8}/><span className="flex-1 text-left">{n.l}</span>
            {n.b>0&&<span className="text-[9px] font-mono bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{n.b}</span>}
          </button>
        ))}
      </nav>
    </aside>
  );
}

/* ═══════════════════════════════════
   NEW PROJECT MODAL
   ═══════════════════════════════════ */
function NewProjectModal({onClose,onCreated}){
  const[f,sF]=useState({name:"",description:"",dataset:"mnist",architecture:"simple_cnn"});
  const[sv,sSv]=useState(false);
  const go=async()=>{if(!f.name.trim())return;sSv(true);await api.post("/projects",f);sSv(false);onCreated();onClose();};
  return(
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
      <div className={`${GS} rounded-lg p-6 w-full max-w-md`}>
        <h3 className="text-sm font-semibold text-white mb-4">Create New Project</h3>
        <div className="space-y-3">
          <div><label className="text-[10px] text-white/40 block mb-1">Project Name</label><input value={f.name} onChange={e=>sF({...f,name:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] font-mono focus:outline-none focus:border-emerald-500/30" placeholder="e.g. Production Fraud Model"/></div>
          <div><label className="text-[10px] text-white/40 block mb-1">Description</label><input value={f.description} onChange={e=>sF({...f,description:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[12px] focus:outline-none focus:border-emerald-500/30"/></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-[10px] text-white/40 block mb-1">Dataset</label><select value={f.dataset} onChange={e=>sF({...f,dataset:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[12px] focus:outline-none"><option value="mnist">MNIST</option><option value="cifar10">CIFAR-10</option></select></div>
            <div><label className="text-[10px] text-white/40 block mb-1">Architecture</label><select value={f.architecture} onChange={e=>sF({...f,architecture:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[12px] focus:outline-none"><option value="simple_cnn">Simple CNN</option></select></div>
          </div>
        </div>
        <div className="flex gap-2 mt-5">
          <button onClick={go} disabled={sv||!f.name.trim()} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-40">{sv?"Creating...":"Create Project"}</button>
          <button onClick={onClose} className="px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px]">Cancel</button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════
   OVERLAY (shared for ATLAS detail)
   ═══════════════════════════════════ */
function Overlay({children,onClose}){
  return(
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
      <div className={`${GS} rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto`}>{children}</div>
    </div>
  );
}

/* ═══════════════════════════════════
   DASHBOARD
   ═══════════════════════════════════ */
function DashPage({stats,pipeline,alerts}){
  return(<div className="space-y-5">
    <div><h1 className="text-xl font-semibold text-white mb-1">Security Overview</h1><p className="text-sm text-white/40">Real-time project security posture</p></div>
    <div className="grid grid-cols-4 gap-3">{[
      {l:"Pipeline Health",v:`${stats.pipeline_health}%`,s:`${stats.passed_checks}/${stats.total_checks}`,c:"text-emerald-400",bg:"bg-emerald-500/10",I:ShieldCheck},
      {l:"Active Alerts",v:stats.active_alerts,s:`${stats.total_alerts} total`,c:stats.active_alerts>0?"text-red-400":"text-emerald-400",bg:stats.active_alerts>0?"bg-red-500/10":"bg-emerald-500/10",I:AlertTriangle},
      {l:"Attack Results",v:stats.total_results,s:"tests run",c:"text-amber-400",bg:"bg-amber-500/10",I:Shield},
      {l:"Active Users",v:stats.active_users,s:"accounts",c:"text-blue-400",bg:"bg-blue-500/10",I:Users},
    ].map(x=><div key={x.l} className={`${G} rounded-lg p-4`}><div className={`w-8 h-8 rounded-md ${x.bg} flex items-center justify-center mb-3`}><x.I size={15} className={x.c}/></div><div className={`text-2xl font-semibold ${x.c}`}>{x.v}</div><div className="text-[11px] text-white/40">{x.l}</div><div className="text-[10px] text-white/25 font-mono mt-0.5">{x.s}</div></div>)}</div>
    <div className="grid grid-cols-3 gap-3">
      <div className={`${G} rounded-lg p-5 col-span-2`}><div className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-4">Pipeline Status</div>
        <div className="flex items-center gap-2">{pipeline.map((st,i)=>{const S=STG.find(s=>s.k===st.stage);const pct=st.total>0?st.passed/st.total*100:0;const ok=pct===100;return(<div key={st.stage} className="flex items-center gap-2 flex-1"><div className={`flex-1 ${GS} rounded-md p-3`}><div className="flex items-center gap-2 mb-2">{S&&<S.I size={13} className={ok?"text-emerald-400":"text-amber-400"}/>}<span className="text-[10px] font-medium text-white/70">{S?.l||st.stage}</span></div><div className="flex items-center gap-2"><div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden"><div className={`h-full rounded-full ${ok?"bg-emerald-500":"bg-amber-500"}`} style={{width:`${pct}%`}}/></div><span className="text-[9px] font-mono text-white/40">{st.passed}/{st.total}</span></div></div>{i<pipeline.length-1&&<ChevronRight size={12} className="text-white/15 shrink-0"/>}</div>);})}</div></div>
      <div className={`${G} rounded-lg p-5`}><div className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-3">Recent Alerts</div><div className="space-y-2">{alerts.slice(0,4).map(a=>{const s=SV[a.severity]||SV.medium;return(<div key={a.id} className={`${s.bg} border ${s.bd} rounded-md px-3 py-2`}><div className="flex items-center gap-2"><div className={`w-1.5 h-1.5 rounded-full ${s.dt}`}/><span className="text-[10px] text-white/70 flex-1 truncate">{a.title}</span></div><div className="text-[9px] text-white/30 font-mono mt-1">{a.source}</div></div>);})}{alerts.length===0&&<p className="text-[10px] text-white/25">No alerts</p>}</div></div>
    </div>
  </div>);
}

/* ═══════════════════════════════════
   PIPELINE
   ═══════════════════════════════════ */
function PipelinePage({pipeline,refresh}){
  const[exp,sExp]=useState(null);
  const toggle=async id=>{await api.post(`/pipeline/check/${id}/toggle`);refresh();};
  return(<div className="space-y-5"><div><h1 className="text-xl font-semibold text-white mb-1">Secure AI Pipeline</h1><p className="text-sm text-white/40">Click checks to toggle pass/fail</p></div>
    <div className="space-y-3">{pipeline.map(st=>{const S=STG.find(s=>s.k===st.stage);const pct=st.total>0?Math.round(st.passed/st.total*100):0;const ok=pct===100;return(<div key={st.stage} className={`${G} rounded-lg overflow-hidden`}>
      <button onClick={()=>sExp(exp===st.stage?null:st.stage)} className="w-full flex items-center gap-4 p-5 text-left hover:bg-white/[0.02] transition-colors"><div className={`w-10 h-10 rounded-lg flex items-center justify-center ${ok?"bg-emerald-500/10":"bg-amber-500/10"}`}>{S&&<S.I size={18} className={ok?"text-emerald-400":"text-amber-400"}/>}</div><div className="flex-1"><div className="text-sm font-medium text-white/90">{S?.l||st.stage}</div><div className="text-[11px] text-white/40">{st.passed}/{st.total} passed</div></div><div className="flex items-center gap-3"><div className="w-24 h-1.5 bg-white/[0.06] rounded-full overflow-hidden"><div className={`h-full rounded-full ${ok?"bg-emerald-500":"bg-amber-500"}`} style={{width:`${pct}%`}}/></div><span className={`text-[10px] font-mono px-2 py-0.5 rounded ${ok?"bg-emerald-500/10 text-emerald-400":"bg-amber-500/10 text-amber-400"}`}>{pct}%</span><ChevronDown size={14} className={`text-white/30 transition-transform ${exp===st.stage?"rotate-180":""}`}/></div></button>
      {exp===st.stage&&<div className="px-5 pb-5 border-t border-white/[0.04]"><div className="grid grid-cols-3 gap-2 pt-4">{st.checks.map(ch=><button key={ch.id} onClick={()=>toggle(ch.id)} className={`flex items-center gap-2 px-3 py-2 rounded-md text-left transition-colors ${ch.passed?"bg-emerald-500/[0.05] hover:bg-emerald-500/[0.1]":"bg-red-500/[0.05] hover:bg-red-500/[0.1]"}`}>{ch.passed?<CheckCircle2 size={12} className="text-emerald-500/70"/>:<XCircle size={12} className="text-red-400/70"/>}<span className="text-[11px] text-white/60">{ch.check_name}</span></button>)}</div></div>}
    </div>);})}</div></div>);
}

/* ═══════════════════════════════════
   RUN ATTACKS
   ═══════════════════════════════════ */
function AttacksPage({pid,refresh}){
  const[sel,sSel]=useState(null);const[pr,sPr]=useState({});const[run,sRun]=useState(false);const[res,sRes]=useState(null);
  const pick=a=>{sSel(a);sRes(null);const d={};a.f.forEach(f=>{d[f.k]=f.d;});sPr(d);};
  const go=async()=>{if(!sel||run)return;sRun(true);sRes(null);const r=await api.post(`/projects/${pid}/attack`,{attack_type:sel.id,params:pr});if(r.job_id){const iv=setInterval(async()=>{const s=await api.get(`/attack/status/${r.job_id}`);if(s.status==="completed"){clearInterval(iv);sRes(s.result);sRun(false);refresh();}else if(s.status==="failed"){clearInterval(iv);sRes({error:s.error});sRun(false);}},2000);}else{sRes(r);sRun(false);}};
  return(<div className="space-y-5"><div><h1 className="text-xl font-semibold text-white mb-1">Run Attacks</h1><p className="text-sm text-white/40">Security tests against the selected project</p></div>
    <div className="grid grid-cols-5 gap-3">{ATK.map(a=><div key={a.id} onClick={()=>a.link?window.location.href="/prompt-injection":pick(a)} className={`${G} rounded-lg p-4 cursor-pointer transition-all hover:border-white/[0.15] ${sel?.id===a.id?"border-emerald-500/30 bg-emerald-500/[0.04]":""}`}><span className="text-[9px] font-mono text-orange-300/70 bg-orange-500/10 px-2 py-0.5 rounded">{a.t}</span><div className="text-[12px] font-medium text-white/80 mt-2">{a.l}</div>{a.link&&<div className="text-[10px] text-white/30 mt-1">Open simulator</div>}</div>)}</div>
    {sel&&!sel.link&&<div className={`${G} rounded-lg p-5`}><h3 className="text-sm font-medium text-emerald-400 mb-4">{sel.l} — Configure</h3>
      <div className="grid grid-cols-3 gap-4">{sel.f.map(f=><div key={f.k}><label className="text-[10px] text-white/40 block mb-1">{f.l}</label>{f.ty==="select"?<select value={pr[f.k]||f.d} onChange={e=>sPr({...pr,[f.k]:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[12px] focus:outline-none focus:border-emerald-500/30">{f.o.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>:<input type="number" value={pr[f.k]||f.d} step={f.s} onChange={e=>sPr({...pr,[f.k]:+e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[12px] font-mono focus:outline-none focus:border-emerald-500/30"/>}</div>)}</div>
      <button onClick={go} disabled={run} className="mt-4 flex items-center gap-2 px-5 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500 disabled:opacity-40">{run?<><Loader2 size={13} className="animate-spin"/>Running...</>:<><Play size={13}/>Run Attack</>}</button>
      {res&&<div className={`mt-4 ${GS} rounded-md p-4`}><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Result</div><pre className="text-[11px] text-emerald-400/80 font-mono whitespace-pre-wrap">{JSON.stringify(res,null,2)}</pre></div>}
    </div>}
  </div>);
}

/* ═══════════════════════════════════
   ATLAS INTEL
   ═══════════════════════════════════ */
function AtlasPage(){
  const[stats,sStats]=useState(null);
  const[q,sQ]=useState("");const[sr,sSr]=useState(null);
  const[modTab,sModTab]=useState(null);const[mapping,sMapping]=useState(null);
  const[coverage,sCov]=useState(null);const[tactics,sTactics]=useState([]);
  const[detail,sDetail]=useState(null);

  useEffect(()=>{
    atlas.get("/stats").then(sStats);
    atlas.get("/coverage").then(sCov);
    atlas.get("/tactics").then(sTactics);
  },[]);

  const doSearch=async()=>{if(!q.trim())return;const d=await atlas.get(`/search?q=${encodeURIComponent(q)}`);sSr(d);};
  const showMod=async m=>{sModTab(m);const d=await atlas.get(`/mapping/${m}`);sMapping(d);};
  const showTech=async id=>{const d=await atlas.get(`/technique/${id}`);sDetail({type:"tech",...d});};
  const showCase=async id=>{const d=await atlas.get(`/case-study/${id}`);sDetail({type:"case",...d});};

  return(<div className="space-y-5">
    <div><h1 className="text-xl font-semibold text-white mb-1">MITRE ATLAS Intelligence</h1><p className="text-sm text-white/40">AI/ML threat framework — techniques, mitigations, case studies</p></div>

    {/* Stats */}
    {stats&&<div className="grid grid-cols-5 gap-3">{[
      {l:"Version",v:`v${stats.version}`,c:"text-emerald-400"},
      {l:"Tactics",v:stats.tactics,c:"text-amber-400"},
      {l:"Techniques",v:stats.techniques_total,c:"text-orange-300"},
      {l:"Mitigations",v:stats.mitigations,c:"text-blue-400"},
      {l:"Case Studies",v:stats.case_studies,c:"text-white/70"},
    ].map(x=><div key={x.l} className={`${G} rounded-lg p-4`}><div className="text-[10px] text-white/30 uppercase tracking-widest">{x.l}</div><div className={`text-xl font-semibold mt-1 ${x.c}`}>{x.v}</div></div>)}</div>}

    {/* Search */}
    <div className="flex gap-2"><div className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-md ${G}`}><Search size={14} className="text-white/25"/><input value={q} onChange={e=>sQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&doSearch()} placeholder="Search techniques, mitigations, case studies..." className="flex-1 bg-transparent text-[12px] text-white/70 focus:outline-none placeholder:text-white/20"/></div><button onClick={doSearch} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium hover:bg-emerald-500">Search</button></div>
    {sr&&<div className={`${G} rounded-lg p-4 space-y-3`}>
      {sr.techniques?.length>0&&<div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Techniques ({sr.techniques.length})</div>{sr.techniques.slice(0,8).map(t=><div key={t.id} onClick={()=>showTech(t.id)} className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[90px]">{t.id}</span><span className="text-[11px] text-white/70">{t.name}</span></div>)}</div>}
      {sr.case_studies?.length>0&&<div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Case Studies ({sr.case_studies.length})</div>{sr.case_studies.slice(0,5).map(c=><div key={c.id} onClick={()=>showCase(c.id)} className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[90px]">{c.id}</span><span className="text-[11px] text-white/70">{c.name}</span></div>)}</div>}
      {sr.mitigations?.length>0&&<div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Mitigations ({sr.mitigations.length})</div>{sr.mitigations.slice(0,5).map(m=><div key={m.id} className="flex items-center gap-3 px-3 py-2"><span className="text-[10px] font-mono text-blue-400 min-w-[90px]">{m.id}</span><span className="text-[11px] text-white/70">{m.name}</span></div>)}</div>}
      {!sr.techniques?.length&&!sr.case_studies?.length&&!sr.mitigations?.length&&<p className="text-[11px] text-white/30">No results found.</p>}
    </div>}

    {/* Module Mappings */}
    <div><div className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-3">Module Mappings</div>
    <div className="flex gap-2 flex-wrap mb-3">{Object.entries(MOD_LABELS).map(([k,v])=><button key={k} onClick={()=>showMod(k)} className={`px-3 py-1.5 rounded-md text-[11px] font-medium transition-all ${modTab===k?`bg-emerald-500/12 text-emerald-400 border border-emerald-500/20`:`${G} text-white/50 hover:text-white/70`}`}>{v}</button>)}</div>
    {mapping&&<div className={`${G} rounded-lg p-5`}>
      <h3 className="text-sm font-medium text-emerald-400 mb-1">{mapping.name}</h3>
      <p className="text-[11px] text-white/40 mb-4">{mapping.description}</p>
      <div className="space-y-4">
        <div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Techniques ({mapping.techniques?.length||0})</div>{mapping.techniques?.map(t=><div key={t.id} onClick={()=>showTech(t.id)} className="flex gap-3 px-3 py-2 rounded-md hover:bg-white/[0.04] cursor-pointer mb-1"><span className="text-[10px] font-mono text-orange-300 min-w-[100px] shrink-0">{t.id}</span><div className="flex-1"><div className="text-[11px] text-white/70 font-medium">{t.name}</div><div className="text-[10px] text-white/35 mt-0.5">{t.relevance}</div>{t.bbap_functions?.length>0&&<div className="text-[10px] text-emerald-400/60 font-mono mt-0.5">{t.bbap_functions.join(", ")}</div>}</div></div>)}</div>
        <div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Mitigations ({mapping.mitigations?.length||0})</div>{mapping.mitigations?.map(m=><div key={m.id} className="flex gap-3 px-3 py-1.5"><span className="text-[10px] font-mono text-blue-400 min-w-[100px]">{m.id}</span><span className="text-[11px] text-white/60">{m.name}</span></div>)}</div>
        <div><div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Case Studies ({mapping.case_studies?.length||0})</div>{mapping.case_studies?.map(c=><div key={c.id} onClick={()=>showCase(c.id)} className="flex gap-3 px-3 py-1.5 rounded-md hover:bg-white/[0.04] cursor-pointer"><span className="text-[10px] font-mono text-orange-300 min-w-[100px]">{c.id}</span><span className="text-[11px] text-white/60">{c.name}</span></div>)}</div>
      </div>
    </div>}</div>

    {/* Coverage Matrix */}
    {coverage&&tactics.length>0&&<div><div className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-3">Tactic Coverage</div>
    <div className={`${G} rounded-lg overflow-hidden`}>{tactics.map(t=>{const mods=coverage[t.name]||[];const has=mods.length>0;return(
      <div key={t.id} className={`flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.04] last:border-b-0 ${has?"bg-emerald-500/[0.02]":""}`}>
        <span className="text-[10px] font-mono text-orange-300/60 min-w-[90px]">{t.id}</span>
        <span className="text-[11px] text-white/70 flex-1">{t.name}</span>
        <div className="flex gap-1.5">{has?mods.map(m=><span key={m} className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400">{MOD_LABELS[m]||m}</span>):<span className="text-[9px] text-white/20">not covered</span>}</div>
      </div>);})}</div></div>}

    {/* Detail Overlay */}
    {detail&&<Overlay onClose={()=>sDetail(null)}>
      <div className="p-5">
        {detail.type==="tech"&&detail.technique&&<>
          <div className="flex items-center gap-3 mb-4"><span className="text-[10px] font-mono text-orange-300 bg-orange-500/10 px-2 py-1 rounded">{detail.technique.id}</span><h3 className="text-sm font-semibold text-white">{detail.technique.name}</h3></div>
          <p className="text-[12px] text-white/50 leading-relaxed mb-4">{detail.technique.description?.slice(0,500)}{detail.technique.description?.length>500?"...":""}</p>
          {detail.technique.tactics&&<div className="mb-3"><span className="text-[10px] text-white/30">Tactics: </span><span className="text-[10px] text-white/50">{detail.technique.tactics.join(", ")}</span></div>}
          {detail.subtechniques?.length>0&&<div className="mb-3"><div className="text-[10px] text-white/30 mb-1">Sub-techniques ({detail.subtechniques.length})</div>{detail.subtechniques.map(s=><div key={s.id} className="text-[10px] text-white/50 ml-2 mb-0.5"><span className="text-orange-300/60 font-mono">{s.id}</span> {s.name}</div>)}</div>}
          {detail.mitigations?.length>0&&<div className="mb-3"><div className="text-[10px] text-white/30 mb-1">Mitigations ({detail.mitigations.length})</div>{detail.mitigations.map(m=><div key={m.id} className="text-[10px] text-white/50 ml-2 mb-0.5"><span className="text-blue-400/60 font-mono">{m.id}</span> {m.name}</div>)}</div>}
          <a href={`https://atlas.mitre.org/techniques/${detail.technique.id}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 mt-2 text-[11px] text-emerald-400 hover:underline"><ExternalLink size={11}/>View on atlas.mitre.org</a>
        </>}
        {detail.type==="case"&&detail.case_study&&<>
          <div className="flex items-center gap-3 mb-4"><span className="text-[10px] font-mono text-orange-300 bg-orange-500/10 px-2 py-1 rounded">{detail.case_study.id}</span><h3 className="text-sm font-semibold text-white">{detail.case_study.name}</h3></div>
          <p className="text-[12px] text-white/50 leading-relaxed mb-4">{detail.case_study.summary}</p>
          {detail.case_study["incident-date"]&&<div className="text-[10px] text-white/30 mb-3">Date: {detail.case_study["incident-date"]}</div>}
          {detail.attack_chain?.length>0&&<div><div className="text-[10px] text-white/30 mb-2">Attack Chain ({detail.attack_chain.length} steps)</div>{detail.attack_chain.map((s,i)=><div key={i} className="flex gap-3 mb-3"><div className="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0">{i+1}</div><div><div className="text-[9px] text-amber-400 uppercase tracking-wider">{s.tactic_name}</div><div onClick={()=>showTech(s.technique_id)} className="text-[11px] text-emerald-400 cursor-pointer hover:underline">{s.technique_id}: {s.technique_name}</div><div className="text-[10px] text-white/35 mt-0.5">{s.description?.slice(0,150)}</div></div></div>)}</div>}
          <a href={`https://atlas.mitre.org/studies/${detail.case_study.id}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 mt-2 text-[11px] text-emerald-400 hover:underline"><ExternalLink size={11}/>View on atlas.mitre.org</a>
        </>}
      </div>
    </Overlay>}
  </div>);
}

/* ═══════════════════════════════════
   RESULTS & REPORTS
   ═══════════════════════════════════ */
function ResultsPage({pid}){
  const[results,sR]=useState([]);
  const[expanded,sExp]=useState(null);
  useEffect(()=>{api.get(`/projects/${pid}/results`).then(sR);},[pid]);

  const exportAll=()=>{
    const report={project_id:pid,exported_at:new Date().toISOString(),total_tests:results.length,results};
    const blob=new Blob([JSON.stringify(report,null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");a.href=url;a.download=`bbap-sec-report-${pid}-${Date.now()}.json`;a.click();URL.revokeObjectURL(url);
  };
  const exportOne=(r)=>{
    const blob=new Blob([JSON.stringify(r,null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");a.href=url;a.download=`bbap-sec-${r.attack_type}-${r.id}.json`;a.click();URL.revokeObjectURL(url);
  };

  return(<div className="space-y-5">
    <div className="flex items-center justify-between">
      <div><h1 className="text-xl font-semibold text-white mb-1">Results & Reports</h1><p className="text-sm text-white/40">{results.length} test results for this project</p></div>
      {results.length>0&&<button onClick={exportAll} className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30"><Download size={13}/>Export All as JSON</button>}
    </div>
    {results.length===0?<div className={`${G} rounded-lg p-10 text-center`}><Shield size={32} className="text-white/10 mx-auto mb-3"/><p className="text-sm text-white/30">No results yet. Run an attack to generate reports.</p></div>:
    <div className="space-y-2">{results.map(r=>{
      const rd=r.result_data||{};const isErr=!!rd.error;
      return(<div key={r.id} className={`${G} rounded-lg overflow-hidden`}>
        <button onClick={()=>sExp(expanded===r.id?null:r.id)} className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-white/[0.02] transition-colors">
          <div className={`w-8 h-8 rounded-md flex items-center justify-center ${isErr?"bg-red-500/10":"bg-emerald-500/10"}`}>{isErr?<XCircle size={14} className="text-red-400"/>:<CheckCircle2 size={14} className="text-emerald-400"/>}</div>
          <div className="flex-1 min-w-0">
            <div className="text-[12px] font-medium text-white/80">{r.attack_type}</div>
            <div className="text-[10px] text-white/35 font-mono">{r.created_at}</div>
          </div>
          <div className="flex items-center gap-3">
            {rd.clean_accuracy&&<span className="text-[9px] font-mono text-white/30">clean: {rd.clean_accuracy}%</span>}
            {rd.adversarial_accuracy!=null&&<span className="text-[9px] font-mono text-amber-400">adv: {rd.adversarial_accuracy}%</span>}
            {rd.fidelity!=null&&<span className="text-[9px] font-mono text-blue-400">fidelity: {rd.fidelity}%</span>}
            {rd.evasion_rate!=null&&<span className="text-[9px] font-mono text-orange-400">evasion: {rd.evasion_rate}%</span>}
            <span className={`text-[9px] font-mono px-2 py-0.5 rounded ${isErr?"bg-red-500/10 text-red-400":"bg-emerald-500/10 text-emerald-400"}`}>{r.status}</span>
            <button onClick={e=>{e.stopPropagation();exportOne(r);}} className="p-1.5 rounded hover:bg-white/[0.06] text-white/25 hover:text-white/60"><Download size={12}/></button>
            <ChevronDown size={14} className={`text-white/30 transition-transform ${expanded===r.id?"rotate-180":""}`}/>
          </div>
        </button>
        {expanded===r.id&&<div className="px-5 pb-4 border-t border-white/[0.04]">
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div><div className="text-[9px] text-white/25 uppercase tracking-widest mb-1">Parameters</div><pre className="text-[10px] font-mono text-white/40 bg-black/20 rounded p-3">{JSON.stringify(r.attack_params,null,2)}</pre></div>
            <div><div className="text-[9px] text-white/25 uppercase tracking-widest mb-1">Results</div><pre className="text-[10px] font-mono text-emerald-400/70 bg-black/20 rounded p-3">{JSON.stringify(rd,null,2)}</pre></div>
          </div>
        </div>}
      </div>);
    })}</div>}
  </div>);
}

/* ═══════════════════════════════════
   MONITORING
   ═══════════════════════════════════ */
function MonitoringPage(){
  const metrics=[{l:"Queries / min",v:"842",t:"+12%",s:"normal"},{l:"Avg Latency",v:"45ms",t:"-3ms",s:"normal"},{l:"Error Rate",v:"0.02%",t:"stable",s:"normal"},{l:"Blocked",v:"23",t:"+5 today",s:"warning"},{l:"Accuracy",v:"97.8%",t:"-0.3%",s:"normal"},{l:"Drift Score",v:"0.04",t:"below threshold",s:"normal"}];
  return(<div className="space-y-5"><div><h1 className="text-xl font-semibold text-white mb-1">Monitoring</h1><p className="text-sm text-white/40">System metrics and activity</p></div>
    <div className="grid grid-cols-3 gap-3">{metrics.map(m=><div key={m.l} className={`${G} rounded-lg p-4`}><div className="text-[10px] text-white/35 uppercase tracking-wider mb-2">{m.l}</div><div className="text-xl font-semibold text-white/90 mb-1">{m.v}</div><div className={`text-[10px] font-mono ${m.s==="warning"?"text-amber-400":"text-white/30"}`}>{m.t}</div></div>)}</div>
  </div>);
}

/* ═══════════════════════════════════
   USERS
   ═══════════════════════════════════ */
function UsersPage(){
  const[us,sU]=useState([]);const[sh,sSh]=useState(false);const[f,sF]=useState({name:"",email:"",role:"viewer"});const[eid,sEid]=useState(null);
  const ld=()=>api.get("/users").then(sU);useEffect(()=>{ld();},[]);
  const R={admin:"bg-red-500/10 text-red-400 border-red-500/20",analyst:"bg-blue-500/10 text-blue-400 border-blue-500/20",viewer:"bg-white/[0.06] text-white/50 border-white/10"};
  const sv=async()=>{if(!f.name||!f.email)return;if(eid)await api.put(`/users/${eid}`,f);else await api.post("/users",f);sSh(false);sF({name:"",email:"",role:"viewer"});sEid(null);ld();};
  return(<div className="space-y-5"><div className="flex items-center justify-between"><div><h1 className="text-xl font-semibold text-white mb-1">User Management</h1></div><button onClick={()=>{sSh(true);sEid(null);sF({name:"",email:"",role:"viewer"});}} className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30"><UserPlus size={13}/>Add User</button></div>
    {sh&&<div className={`${G} rounded-lg p-5`}><div className="grid grid-cols-3 gap-4"><div><label className="text-[10px] text-white/40 block mb-1">Name</label><input value={f.name} onChange={e=>sF({...f,name:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] focus:outline-none focus:border-emerald-500/30"/></div><div><label className="text-[10px] text-white/40 block mb-1">Email</label><input value={f.email} onChange={e=>sF({...f,email:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-[12px] font-mono focus:outline-none focus:border-emerald-500/30"/></div><div><label className="text-[10px] text-white/40 block mb-1">Role</label><select value={f.role} onChange={e=>sF({...f,role:e.target.value})} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/70 text-[12px] focus:outline-none"><option value="viewer">Viewer</option><option value="analyst">Analyst</option><option value="admin">Admin</option></select></div></div><div className="flex gap-2 mt-4"><button onClick={sv} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium">Save</button><button onClick={()=>sSh(false)} className="px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px]">Cancel</button></div></div>}
    <div className={`${G} rounded-lg overflow-hidden`}><table className="w-full"><thead><tr className="border-b border-white/[0.06]">{["User","Email","Role","Status","MFA","Actions"].map(h=><th key={h} className="text-left px-4 py-3 text-[9px] font-semibold text-white/30 uppercase tracking-widest">{h}</th>)}</tr></thead><tbody>{us.map(u=><tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.02]"><td className="px-4 py-3"><div className="flex items-center gap-3"><div className="w-7 h-7 rounded-full bg-white/[0.06] flex items-center justify-center text-[10px] font-medium text-white/50">{u.name.split(" ").map(n=>n[0]).join("")}</div><span className="text-[12px] text-white/80">{u.name}</span></div></td><td className="px-4 py-3 text-[11px] text-white/50 font-mono">{u.email}</td><td className="px-4 py-3"><span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${R[u.role]||R.viewer}`}>{u.role}</span></td><td className="px-4 py-3"><span className={`text-[9px] font-mono ${u.status==="active"?"text-emerald-400":"text-red-400"}`}>{u.status}</span></td><td className="px-4 py-3">{u.mfa?<Lock size={12} className="text-emerald-500/60"/>:<Unlock size={12} className="text-white/20"/>}</td><td className="px-4 py-3"><div className="flex gap-1.5"><button onClick={()=>{sF({name:u.name,email:u.email,role:u.role});sEid(u.id);sSh(true);}} className="p-1.5 rounded hover:bg-white/[0.06] text-white/30 hover:text-white/60"><Edit3 size={12}/></button><button onClick={async()=>{await api.del(`/users/${u.id}`);ld();}} className="p-1.5 rounded hover:bg-red-500/10 text-white/20 hover:text-red-400"><Trash2 size={12}/></button></div></td></tr>)}</tbody></table></div></div>);
}

/* ═══════════════════════════════════
   KNOWLEDGE BASE
   ═══════════════════════════════════ */
function KnowledgePage({pid}){
  const[ns,sN]=useState([]);const[sh,sSh]=useState(false);const[f,sF]=useState({title:"",content:"",tags:""});const[eid,sEid]=useState(null);const[q,sQ]=useState("");
  const ld=()=>api.get(`/notes?project_id=${pid}`).then(sN);useEffect(()=>{ld();},[pid]);
  const sv=async()=>{if(!f.title)return;const tags=f.tags.split(",").map(t=>t.trim()).filter(Boolean);if(eid)await api.put(`/notes/${eid}`,{title:f.title,content:f.content,tags});else await api.post("/notes",{title:f.title,content:f.content,tags,project_id:pid});sSh(false);sF({title:"",content:"",tags:""});sEid(null);ld();};
  const fil=ns.filter(n=>!q||n.title.toLowerCase().includes(q.toLowerCase())||n.content.toLowerCase().includes(q.toLowerCase()));
  return(<div className="space-y-5"><div className="flex items-center justify-between"><div><h1 className="text-xl font-semibold text-white mb-1">Knowledge Base</h1></div><button onClick={()=>{sSh(true);sEid(null);sF({title:"",content:"",tags:""});}} className="flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium hover:bg-emerald-600/30"><Plus size={13}/>New Note</button></div>
    <div className={`flex items-center gap-2 px-3 py-2 rounded-md ${G}`}><Search size={13} className="text-white/25"/><input value={q} onChange={e=>sQ(e.target.value)} placeholder="Search..." className="flex-1 bg-transparent text-[12px] text-white/70 focus:outline-none placeholder:text-white/20"/></div>
    {sh&&<div className={`${G} rounded-lg p-5`}><input value={f.title} onChange={e=>sF({...f,title:e.target.value})} placeholder="Title..." className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/80 text-sm mb-3 focus:outline-none focus:border-emerald-500/30"/><textarea value={f.content} onChange={e=>sF({...f,content:e.target.value})} placeholder="Content..." rows={5} className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[12px] leading-relaxed mb-3 focus:outline-none focus:border-emerald-500/30 resize-none font-mono"/><input value={f.tags} onChange={e=>sF({...f,tags:e.target.value})} placeholder="Tags (comma-separated)" className="w-full px-3 py-2 rounded-md bg-black/30 border border-white/[0.08] text-white/60 text-[11px] font-mono mb-3 focus:outline-none focus:border-emerald-500/30"/><div className="flex gap-2"><button onClick={sv} className="px-4 py-2 rounded-md bg-emerald-600 text-white text-[11px] font-medium">Save</button><button onClick={()=>sSh(false)} className="px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px]">Cancel</button></div></div>}
    <div className="space-y-3">{fil.map(n=><div key={n.id} className={`${G} rounded-lg p-5 ${n.pinned?"border-l-2 border-l-emerald-500/40":""}`}><div className="flex items-start justify-between mb-2"><h3 className="text-sm font-medium text-white/90">{n.title}</h3><div className="flex gap-1"><button onClick={async()=>{await api.put(`/notes/${n.id}`,{pinned:n.pinned?0:1});ld();}} className={`p-1.5 rounded hover:bg-white/[0.06] ${n.pinned?"text-emerald-400":"text-white/20"}`}><BookOpen size={11}/></button><button onClick={()=>{sF({title:n.title,content:n.content,tags:(n.tags||[]).join(", ")});sEid(n.id);sSh(true);}} className="p-1.5 rounded hover:bg-white/[0.06] text-white/25 hover:text-white/60"><Edit3 size={11}/></button><button onClick={async()=>{await api.del(`/notes/${n.id}`);ld();}} className="p-1.5 rounded hover:bg-red-500/10 text-white/15 hover:text-red-400"><Trash2 size={11}/></button></div></div><p className="text-[12px] text-white/50 leading-relaxed mb-3 whitespace-pre-wrap">{n.content}</p><div className="flex items-center justify-between"><div className="flex gap-1.5">{(n.tags||[]).map(t=><span key={t} className="text-[9px] font-mono px-2 py-0.5 rounded bg-white/[0.04] text-white/35 border border-white/[0.06]">{t}</span>)}</div><span className="text-[9px] font-mono text-white/20">{n.created_at?.split("T")[0]}</span></div></div>)}</div></div>);
}

/* ═══════════════════════════════════
   ALERTS
   ═══════════════════════════════════ */
function AlertsPage({alerts,refresh}){
  const ack=async id=>{await api.post(`/alerts/${id}/ack`);refresh();};
  const ackAll=async()=>{await api.post("/alerts/ack-all");refresh();};
  const un=alerts.filter(a=>!a.acknowledged).length;
  return(<div className="space-y-5"><div className="flex items-center justify-between"><div><h1 className="text-xl font-semibold text-white mb-1">Alerts</h1><p className="text-sm text-white/40">{un} unacknowledged</p></div>{un>0&&<button onClick={ackAll} className="flex items-center gap-2 px-4 py-2 rounded-md bg-white/[0.06] text-white/50 text-[11px] hover:bg-white/[0.08]"><Check size={13}/>Ack All</button>}</div>
    <div className="space-y-2">{alerts.map(a=>{const s=SV[a.severity]||SV.medium;return(<div key={a.id} className={`${G} rounded-lg px-5 py-4 flex items-center gap-4 ${a.acknowledged?"opacity-40":""}`}><div className={`w-2 h-2 rounded-full shrink-0 ${s.dt}`}/><div className="flex-1 min-w-0"><div className="text-[12px] text-white/80 mb-0.5">{a.title}</div><div className="text-[9px] font-mono text-white/30">{a.source} — {a.created_at}</div></div><span className={`text-[9px] font-mono px-2 py-0.5 rounded ${s.bg} ${s.tx} border ${s.bd}`}>{a.severity}</span>{!a.acknowledged&&<button onClick={()=>ack(a.id)} className="px-3 py-1.5 rounded-md bg-white/[0.04] text-white/40 text-[10px] hover:bg-white/[0.08]">Ack</button>}</div>);})}</div></div>);
}

/* ═══════════════════════════════════
   SETTINGS
   ═══════════════════════════════════ */
function SettingsPage(){return(<div className="space-y-5"><div><h1 className="text-xl font-semibold text-white mb-1">Settings</h1></div><div className="grid grid-cols-2 gap-4">{[{t:"API Configuration",d:"Keys, rate limits, tokens",I:Key},{t:"Email / SMTP",d:"Alert delivery",I:Mail},{t:"Authentication",d:"SSO, MFA, sessions",I:Lock},{t:"Integrations",d:"SIEM, ticketing",I:Zap},{t:"Backup",d:"Database export",I:Database},{t:"Audit Log",d:"Access history",I:FileText}].map(s=><div key={s.t} className={`${G} rounded-lg p-5 hover:bg-white/[0.06] cursor-pointer transition-all`}><div className="flex items-center gap-3"><div className="w-9 h-9 rounded-lg bg-white/[0.04] flex items-center justify-center"><s.I size={16} className="text-white/40"/></div><div><div className="text-[13px] font-medium text-white/80">{s.t}</div><div className="text-[10px] text-white/35">{s.d}</div></div></div></div>)}</div></div>);}

/* ═══════════════════════════════════
   MAIN APP
   ═══════════════════════════════════ */
export default function App(){
  const[page,sPage]=useState("dashboard");
  const[projects,sProjects]=useState([]);
  const[project,sProject]=useState(null);
  const[showNew,sShowNew]=useState(false);
  const[stats,sStats]=useState({pipeline_health:0,total_checks:0,passed_checks:0,active_alerts:0,total_alerts:0,total_results:0,active_users:0});
  const[pipeline,sPipeline]=useState([]);
  const[alerts,sAlerts]=useState([]);

  const ldProjects=useCallback(async()=>{const ps=await api.get("/projects");sProjects(ps);if(ps.length>0&&!project)sProject(ps[0]);if(ps.length===0)sShowNew(true);},[project]);
  const ldData=useCallback(async()=>{if(!project)return;const[s,p,a]=await Promise.all([api.get(`/projects/${project.id}/stats`),api.get(`/projects/${project.id}/pipeline`),api.get(`/projects/${project.id}/alerts`)]);sStats(s);sPipeline(p);sAlerts(a);},[project]);
  useEffect(()=>{ldProjects();},[]);
  useEffect(()=>{if(project)ldData();},[project,page]);
  const refresh=()=>ldData();

  if(!project&&projects.length===0)return(
    <div className="flex h-screen bg-[#080b12] items-center justify-center" style={{fontFamily:"'DM Sans',system-ui,sans-serif"}}>
      <div className="fixed inset-0 pointer-events-none" style={{background:"radial-gradient(ellipse 60% 40% at 20% 10%,rgba(46,204,113,0.03),transparent)"}}/>
      {showNew&&<NewProjectModal onClose={()=>{}} onCreated={ldProjects}/>}
      <div className="text-center relative z-10">
        <img src="/frontend/public/logo.png" alt="BBAP-Sec" className="w-16 h-16 rounded-xl mx-auto mb-4 object-cover" onError={e=>{e.target.style.display='none';}}/>
        <h1 className="text-lg font-semibold text-white mb-2">Welcome to BBAP-Sec</h1>
        <p className="text-sm text-white/40 mb-4">Create your first project to get started</p>
        <button onClick={()=>sShowNew(true)} className="px-5 py-2 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-500">Create Project</button>
      </div>
    </div>
  );

  const P={
    dashboard:<DashPage stats={stats} pipeline={pipeline} alerts={alerts}/>,
    pipeline:<PipelinePage pipeline={pipeline} refresh={refresh}/>,
    attacks:<AttacksPage pid={project?.id} refresh={refresh}/>,
    atlas:<AtlasPage/>,
    results:<ResultsPage pid={project?.id}/>,
    monitoring:<MonitoringPage/>,
    users:<UsersPage/>,
    knowledge:<KnowledgePage pid={project?.id}/>,
    alerts:<AlertsPage alerts={alerts} refresh={refresh}/>,
    settings:<SettingsPage/>,
  };

  return(
    <div className="flex h-screen bg-[#080b12] text-white overflow-hidden" style={{fontFamily:"'DM Sans',system-ui,sans-serif"}}>
      <div className="fixed inset-0 pointer-events-none" style={{background:"radial-gradient(ellipse 60% 40% at 20% 10%,rgba(46,204,113,0.03),transparent),radial-gradient(ellipse 50% 50% at 80% 80%,rgba(184,115,51,0.02),transparent)"}}/>
      <Sidebar page={page} setPage={sPage} project={project} projects={projects} setProject={sProject} setShowNew={sShowNew} ac={stats.active_alerts}/>
      <main className="flex-1 overflow-y-auto relative z-10 p-6 pb-20">{P[page]}</main>
      {showNew&&<NewProjectModal onClose={()=>sShowNew(false)} onCreated={ldProjects}/>}
    </div>
  );
}

import { useState, useEffect, useRef, useMemo } from "react";
import axios from "axios";
import {
  AreaChart, Area,
  BarChart, Bar,
  PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend,
} from "recharts";

/* ─── Config ─────────────────────────────────────────────────────────── */
const API = "http://localhost:8000";

/* ─── Design tokens ──────────────────────────────────────────────────── */
const C = {
  bg:      "#0D0D0D",
  card:    "#141414",
  border:  "#2a1a1a",
  primary: "#8B0000",
  danger:  "#B22222",
  warning: "#fca311",
  success: "#52b788",
  muted:   "#666666",
  text:    "#F5F5F5",
  sub:     "#B0B0B0",
};

const THREAT_CATS = ["DDoS", "SQL Injection", "Port Scan", "Phishing", "Brute Force", "Malware"];

/* ─── Helpers ─────────────────────────────────────────────────────────── */
const randInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const randIP  = () => `${randInt(1,254)}.${randInt(0,255)}.${randInt(0,255)}.${randInt(1,254)}`;

const genHourlyData = () =>
  Array.from({ length: 24 }, (_, i) => {
    const d = new Date();
    d.setHours(d.getHours() - (23 - i));
    return {
      hour:     `${String(d.getHours()).padStart(2, "0")}:00`,
      attempts: randInt(5, 80),
      blocked:  randInt(2, 40),
    };
  });

const riskColor = (r) => r > 80 ? C.danger : r > 50 ? C.warning : C.success;

/**
 * Normalise the ML model response into { risk (0-100), status, category }.
 *
 * Current model returns: { risk: 0.0-1.0, status: "High Risk" | "Normal" }
 * Also handles future model shapes (risk_score, confidence, label, prediction, etc.)
 */
const parseResponse = (data) => {
  let risk     = null;
  let status   = null;
  let category = THREAT_CATS[randInt(0, THREAT_CATS.length - 1)];

  // ── current model: { risk: 0.8, status: "High Risk" } ──
  if (typeof data.risk === "number") {
    risk = data.risk <= 1 ? data.risk * 100 : data.risk;
  }
  if (typeof data.status === "string") {
    status = data.status; // "High Risk" | "Normal" (passed straight through)
  }

  // ── future model fallbacks ──
  if (risk === null) {
    if (typeof data.risk_score   === "number") risk = data.risk_score;
    else if (typeof data.score        === "number") risk = data.score <= 1 ? data.score * 100 : data.score;
    else if (typeof data.probability  === "number") risk = data.probability  * 100;
    else if (typeof data.confidence   === "number") risk = data.confidence   * 100;
  }

  // ── label / prediction fallbacks ──
  if (status === null) {
    const rawLabel = data.prediction ?? data.label ?? data.result ?? null;
    if (rawLabel !== null) {
      const ls = String(rawLabel).toLowerCase();
      if (["0", "normal", "benign"].includes(ls))                    { status = "Normal";    if (risk === null) risk = randInt(10, 40); }
      else if (["1", "attack", "anomaly", "malicious"].includes(ls)) { status = "High Risk"; if (risk === null) risk = randInt(75, 95); }
      else { category = String(rawLabel); status = "High Risk";      if (risk === null) risk = randInt(55, 90); }
    }
  }

  // ── explicit attack type ──
  const rawType = data.attack_type ?? data.type ?? data.class_name ?? null;
  if (rawType) category = String(rawType);

  if (risk   === null) risk   = randInt(20, 70);
  if (status === null) status = risk > 80 ? "High Risk" : risk > 50 ? "Suspicious" : "Normal";

  return { risk: Math.round(Math.max(0, Math.min(100, risk))), status, category };
};

/**
 * Generate a realistic network-traffic sample to send to /predict.
 * Ranges are calibrated to CIC-IDS 2017 normal traffic baseline:
 *   mean_pps ≈ 0.033 ± 0.067  |  mean_bps ≈ 1.1 ± 3.9
 *   total_packets ≈ 585 ± 748  |  total_bytes ≈ 106498 ± 135711
 *   var_pps ≈ 0.026 ± 0.064
 */
const randFloat = (min, max, decimals = 6) =>
  parseFloat((Math.random() * (max - min) + min).toFixed(decimals));

const genSample = (highLoad = false) => ({
  mean_pps:       highLoad ? randFloat(0.15, 0.5)       : randFloat(0.0,   0.1),
  mean_bps:       highLoad ? randFloat(10.0, 30.0,  4)  : randFloat(0.0,   5.0, 4),
  total_packets:  highLoad ? randInt(1500, 4000)         : randInt(100,    1300),
  total_bytes:    highLoad ? randInt(400000, 900000)     : randInt(10000, 240000),
  var_pps:        highLoad ? randFloat(0.2,  0.5)        : randFloat(0.0,   0.09),
});

/* ─── Sub-components ─────────────────────────────────────────────────── */
function StatCard({ label, value, color, icon }) {
  return (
    <div style={{
      background: C.card, border: `1px solid ${color}33`,
      borderRadius: 14, padding: "20px 24px",
      flex: 1, minWidth: 150, boxShadow: `0 0 24px ${color}18`,
    }}>
      <div style={{ color: C.sub, fontSize: 11, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
        {icon}&nbsp;{label}
      </div>
      <div style={{ color, fontSize: 34, fontWeight: 800, fontFamily: "monospace", lineHeight: 1 }}>
        {value}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    "High Risk":  { bg: C.danger  + "22", color: C.danger,  border: C.danger  + "55" },
    "Suspicious": { bg: C.warning + "22", color: C.warning, border: C.warning + "55" },
    "Normal":     { bg: C.success + "22", color: C.success, border: C.success + "55" },
  };
  const s = map[status] ?? map["Normal"];
  return (
    <span style={{
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      borderRadius: 6, padding: "2px 10px", fontSize: 11, fontWeight: 700,
    }}>
      {status}
    </span>
  );
}

function SourceBadge({ source }) {
  const online = source === "backend";
  return (
    <span style={{
      background: online ? C.primary + "18" : C.muted + "18",
      color:      online ? C.primary        : C.muted,
      border: `1px solid ${online ? C.primary + "44" : C.muted + "44"}`,
      borderRadius: 6, padding: "2px 8px", fontSize: 10, fontWeight: 600,
    }}>
      {online ? "⚡ API" : "~ SIM"}
    </span>
  );
}

function ChartCard({ title, sub, children, style = {} }) {
  return (
    <div style={{
      background: C.card, borderRadius: 16, border: `1px solid ${C.border}`,
      padding: 24, ...style,
    }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 700, fontSize: 14 }}>{title}</div>
        <div style={{ color: C.sub, fontSize: 12, marginTop: 2 }}>{sub}</div>
      </div>
      {children}
    </div>
  );
}

const tooltipStyle = {
  contentStyle: { background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, color: C.text, fontSize: 12 },
  labelStyle:   { color: C.sub },
  itemStyle:    { color: C.text },
  wrapperStyle: { outline: "none" },
  cursor:       { stroke: C.border, strokeWidth: 1 },
};

const axisProps = { tick: { fill: C.muted, fontSize: 10 }, tickLine: false, axisLine: false };

/* ─── Main App ───────────────────────────────────────────────────────── */
export default function App() {
  const [page,        setPage]        = useState("home");
  const [showLogs,    setShowLogs]    = useState(false);
  const [riskData,    setRiskData]    = useState([]);
  const [trafficData, setTrafficData] = useState([]);
  const [threats,     setThreats]     = useState([]);
  const [running,     setRunning]     = useState(false);
  const [stats,       setStats]       = useState({ total: 0, high: 0, suspicious: 0, blocked: 0 });
  const [vectorData,  setVectorData]  = useState(THREAT_CATS.map(type => ({ type, score: randInt(5, 35) })));
  const [hourlyData]                  = useState(genHourlyData);
  const [clock,       setClock]       = useState(new Date());
  const [progress,    setProgress]    = useState(0);

  // "checking" | "online" | "offline"
  const [backendStatus, setBackendStatus] = useState("checking");
  // keep a ref so the interval closure always reads the latest value
  const backendRef = useRef("checking");
  const setBackend = (v) => { backendRef.current = v; setBackendStatus(v); };

  /* clock */
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  /* health-check — runs once when dashboard mounts, then every 15 s */
  useEffect(() => {
    if (page !== "dashboard") return;
    const check = async () => {
      try {
        await axios.get(`${API}/`, { timeout: 3000 });
        setBackend("online");
      } catch {
        setBackend("offline");
      }
    };
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, [page]);

  /* core data loop */
  useEffect(() => {
    if (!running) return;

    const tick = async () => {
      const time = new Date().toLocaleTimeString();
      let risk, category, source, status, packets;

      if (backendRef.current === "online") {
        try {
          // Use real CIC-IDS windows from the backend (cycles through windows.csv)
          const res    = await axios.get(`${API}/next_window`, { timeout: 3000 });
          const d      = res.data;
          const parsed = parseResponse(d.prediction);
          risk     = parsed.risk;
          status   = parsed.status;
          category = d.label && d.label !== "UNKNOWN" && d.label !== "BENIGN"
            ? d.label   // use actual attack label from dataset when available
            : parsed.category;
          source   = d.source === "csv" ? "backend" : "simulated";
          packets  = d.window.mean_pps;
        } catch {
          const sample = genSample();
          risk     = Math.max(0, Math.min(100, (riskData.at(-1)?.risk ?? 50) + randInt(-10, 10)));
          status   = risk > 80 ? "High Risk" : risk > 50 ? "Suspicious" : "Normal";
          category = THREAT_CATS[randInt(0, THREAT_CATS.length - 1)];
          source   = "simulated";
          packets  = sample.mean_pps;
        }
      } else {
        const sample = genSample();
        risk     = Math.max(0, Math.min(100, (riskData.at(-1)?.risk ?? 50) + randInt(-10, 10)));
        status   = risk > 80 ? "High Risk" : risk > 50 ? "Suspicious" : "Normal";
        category = THREAT_CATS[randInt(0, THREAT_CATS.length - 1)];
        source   = "simulated";
        packets  = sample.mean_pps;
      }

      const blocked = Math.floor(packets * risk / 180);
      const ip      = randIP();

      setRiskData(p    => [...p, { time, risk }].slice(-30));
      setTrafficData(p => [...p, { time, packets, blocked }].slice(-20));

      if (risk > 50) {
        setThreats(p => [{ time, risk, status, category, ip, source }, ...p].slice(0, 20));
        setStats(p => ({
          total:      p.total + 1,
          high:       p.high       + (risk > 80 ? 1 : 0),
          suspicious: p.suspicious + (risk > 50 && risk <= 80 ? 1 : 0),
          blocked:    p.blocked    + (risk > 70 ? 1 : 0),
        }));
        setVectorData(pv => pv.map(d =>
          d.type === category
            ? { ...d, score: Math.min(100, d.score + randInt(4, 10)) }
            : { ...d, score: Math.max(0,   d.score - 1) }
        ));
      }
    };

    const id = setInterval(tick, 1500);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running]);

  /* pie data */
  const pieData = useMemo(() => {
    const hasData = stats.high + stats.suspicious + stats.blocked > 0;
    if (!hasData) return [
      { name: "No data yet", value: 1, color: C.border },
    ];
    return [
      { name: "High Risk",  value: stats.high,        color: C.danger  },
      { name: "Suspicious", value: stats.suspicious,  color: C.warning },
      { name: "Blocked",    value: stats.blocked,     color: C.success },
    ].filter(d => d.value > 0);
  }, [stats]);

  /* loading animation */
  const startSimulation = () => {
    setPage("loading");
    let p = 0;
    const id = setInterval(() => {
      p += randInt(6, 18);
      if (p >= 100) {
        p = 100; clearInterval(id);
        setTimeout(() => { setPage("dashboard"); setRunning(true); }, 300);
      }
      setProgress(Math.min(100, p));
    }, 150);
  };

  /* simulate attack — use high-load sample if backend is online */
  const simulateAttack = async () => {
    const time   = new Date().toLocaleTimeString();
    const sample = genSample(true);
    let risk, category, source;

    if (backendRef.current === "online") {
      try {
        const res = await axios.post(`${API}/predict`, sample, { timeout: 3000 });
        const p  = parseResponse(res.data);
        risk     = Math.max(p.risk, 85);
        category = p.category;
        source   = "backend";
      } catch {
        risk = randInt(90, 99); category = THREAT_CATS[randInt(0, THREAT_CATS.length - 1)]; source = "simulated";
      }
    } else {
      risk = randInt(90, 99); category = THREAT_CATS[randInt(0, THREAT_CATS.length - 1)]; source = "simulated";
    }

    const ip = randIP();
    setRiskData(p    => [...p, { time, risk }].slice(-30));
    setTrafficData(p => [...p, { time, packets: sample.mean_pps, blocked: Math.floor(sample.mean_pps * 0.85) }].slice(-20));
    setThreats(p     => [{ time, risk, status: "High Risk", category, ip, source }, ...p].slice(0, 20));
    setStats(p       => ({ ...p, total: p.total + 1, high: p.high + 1, blocked: p.blocked + 1 }));
  };

  const resetAll = () => {
    setRunning(false);
    setRiskData([]); setTrafficData([]); setThreats([]);
    setStats({ total: 0, high: 0, suspicious: 0, blocked: 0 });
    setVectorData(THREAT_CATS.map(type => ({ type, score: randInt(5, 35) })));
  };

  const currentRisk = riskData.at(-1)?.risk ?? 0;
  const rc = riskColor(currentRisk);

  /* backend status pill config */
  const bsCfg = {
    checking: { color: C.muted,   label: "● Connecting…"  },
    online:   { color: C.success, label: "● Backend Online" },
    offline:  { color: C.warning, label: "● Backend Offline — Simulating" },
  }[backendStatus];

  /* ══════════════════════ HOME ══════════════════════ */
  if (page === "home") return (
    <div style={{
      background: `radial-gradient(ellipse 80% 60% at 50% -10%, #2a0000 0%, ${C.bg} 65%)`,
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      fontFamily: "system-ui, -apple-system, Arial, sans-serif",
      color: C.text, padding: 40, position: "relative", overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: `linear-gradient(${C.border}55 1px, transparent 1px),
                          linear-gradient(90deg, ${C.border}55 1px, transparent 1px)`,
        backgroundSize: "44px 44px",
      }} />
      <div style={{
        position: "absolute", width: 500, height: 500, borderRadius: "50%",
        background: `${C.primary}0a`, filter: "blur(80px)",
        top: "50%", left: "50%", transform: "translate(-50%,-50%)", pointerEvents: "none",
      }} />

      <div style={{ position: "relative", zIndex: 1, textAlign: "center", maxWidth: 620 }}>
        <div style={{
          width: 96, height: 96, borderRadius: "50%",
          background: `${C.primary}18`, border: `2px solid ${C.primary}55`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 42, margin: "0 auto 32px",
          boxShadow: `0 0 48px ${C.primary}44, inset 0 0 24px ${C.primary}11`,
        }}>🛡️</div>

        <div style={{ color: C.primary, fontSize: 12, letterSpacing: 5, textTransform: "uppercase", marginBottom: 14, fontFamily: "monospace" }}>
          GDG Hack  ◆  Security Platform
        </div>

        <h1 style={{
          fontSize: "clamp(2rem, 5vw, 3.2rem)", fontWeight: 800,
          margin: "0 0 18px", lineHeight: 1.2,
          background: `linear-gradient(135deg, ${C.text} 40%, #B22222)`,
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
        }}>
          Intrusion Detection<br />System
        </h1>

        <p style={{ color: C.sub, fontSize: 17, marginBottom: 44, lineHeight: 1.7 }}>
          Real-time anomaly detection &amp; risk monitoring powered by AI-driven threat intelligence.
        </p>

        <button
          onClick={startSimulation}
          style={{
            padding: "14px 40px", borderRadius: 12, cursor: "pointer",
            background: `linear-gradient(135deg, ${C.primary}, #5a0000)`,
            border: "none", color: "white", fontSize: 16, fontWeight: 700,
            boxShadow: `0 0 36px ${C.primary}55`, transition: "transform 0.15s, box-shadow 0.15s",
          }}
          onMouseOver={e => { e.target.style.transform = "scale(1.04)"; e.target.style.boxShadow = `0 0 50px ${C.primary}77`; }}
          onMouseOut={e  => { e.target.style.transform = "scale(1)";    e.target.style.boxShadow = `0 0 36px ${C.primary}55`; }}
        >
          Launch Dashboard →
        </button>

        <div style={{ display: "flex", gap: 28, marginTop: 56, justifyContent: "center", flexWrap: "wrap" }}>
          {[["⚡","Real-time Detection"],["📊","5 Live Charts"],["🔌","FastAPI Backend"],["🚨","Instant Alerts"]].map(([ic, lb]) => (
            <div key={lb} style={{ color: C.sub, fontSize: 13, display: "flex", alignItems: "center", gap: 6 }}>
              <span>{ic}</span>{lb}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  /* ══════════════════════ LOADING ══════════════════════ */
  if (page === "loading") return (
    <div style={{
      background: C.bg, minHeight: "100vh",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      fontFamily: "monospace", color: C.text, gap: 20,
    }}>
      <div style={{ fontSize: 52 }}>🛡️</div>
      <div style={{ color: C.primary, fontSize: 13, letterSpacing: 4, textTransform: "uppercase" }}>
        Initializing System
      </div>
      <div style={{ width: 320, background: C.card, borderRadius: 99, height: 5, overflow: "hidden", border: `1px solid ${C.border}` }}>
        <div style={{
          width: `${progress}%`, height: "100%",
          background: `linear-gradient(90deg, ${C.primary}, #5a0000)`,
          borderRadius: 99, transition: "width 0.15s ease", boxShadow: `0 0 12px ${C.primary}`,
        }} />
      </div>
      <div style={{ color: C.sub, fontSize: 13 }}>
        {progress < 30 ? "Loading threat intelligence..." :
         progress < 60 ? "Initializing network monitors..." :
         progress < 85 ? "Configuring detection algorithms..." : "System ready…"}
      </div>
      <div style={{ color: C.muted, fontSize: 12 }}>{progress}%</div>
    </div>
  );

  /* ══════════════════════ DASHBOARD ══════════════════════ */
  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: "system-ui, -apple-system, Arial, sans-serif", color: C.text }}>

      {/* ── HEADER ── */}
      <header style={{
        background: `${C.card}dd`, backdropFilter: "blur(12px)",
        borderBottom: `1px solid ${C.border}`,
        padding: "12px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 22 }}>🛡️</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>IDS Dashboard</div>
            <div style={{ color: C.sub, fontSize: 11 }}>GDG Hack Security Platform</div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>

          {/* backend status */}
          <div style={{ color: bsCfg.color, fontSize: 11, fontFamily: "monospace", fontWeight: 600 }}>
            {bsCfg.label}
          </div>

          {/* live / paused */}
          <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12 }}>
            <span style={{
              width: 8, height: 8, borderRadius: "50%",
              background: running ? C.success : C.muted,
              boxShadow: running ? `0 0 8px ${C.success}` : "none",
              display: "inline-block",
              animation: running ? "pulseDot 1.5s infinite" : "none",
            }} />
            <span style={{ color: running ? C.success : C.muted, fontWeight: 700, letterSpacing: 1 }}>
              {running ? "LIVE" : "PAUSED"}
            </span>
          </div>

          {/* current risk */}
          <div style={{
            padding: "4px 14px", borderRadius: 99,
            background: `${rc}22`, border: `1px solid ${rc}66`,
            color: rc, fontSize: 12, fontFamily: "monospace", fontWeight: 700,
          }}>
            Risk: {currentRisk}
          </div>

          <div style={{ color: C.sub, fontSize: 12, fontFamily: "monospace" }}>
            {clock.toLocaleTimeString()}
          </div>
        </div>
      </header>

      <div style={{ padding: "24px 32px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ── STAT CARDS ── */}
        <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
          <StatCard label="Total Threats"  value={stats.total}      color={C.text} icon="📡" />
          <StatCard label="High Risk"      value={stats.high}       color={C.danger}  icon="🔴" />
          <StatCard label="Suspicious"     value={stats.suspicious} color={C.warning} icon="⚠️" />
          <StatCard label="Blocked"        value={stats.blocked}    color={C.success} icon="🛡️" />
        </div>

        {/* ── ROW 1: Area + Donut ── */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 14, marginBottom: 14 }}>
          <ChartCard title="Live Risk Score" sub="Real-time threat level — last 30 ticks">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={riskData}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#e05c5c" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#e05c5c" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={C.border} strokeDasharray="3 3" />
                <XAxis dataKey="time" {...axisProps} />
                <YAxis domain={[0, 100]} {...axisProps} />
                <Tooltip {...tooltipStyle} />
                <Area type="monotone" dataKey="risk" name="Risk Score"
                  stroke="#e05c5c" fill="url(#riskGrad)" strokeWidth={2} dot={false} animationDuration={300} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Threat Distribution" sub="By severity level">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="45%" innerRadius={62} outerRadius={92}
                  paddingAngle={4} dataKey="value" animationDuration={500}>
                  {pieData.map((e, i) => <Cell key={i} fill={e.color} stroke="none" />)}
                </Pie>
                <Tooltip {...tooltipStyle} />
                <Legend iconType="circle" iconSize={8}
                  formatter={v => <span style={{ color: C.sub, fontSize: 11 }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* ── ROW 2: Traffic + Radar ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
          <ChartCard title="Network Traffic" sub="Packets / second — total vs blocked">
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={trafficData} barGap={3}>
                <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="time" {...axisProps} />
                <YAxis {...axisProps} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="packets" name="Total"   fill={C.primary + "99"} radius={[3,3,0,0]} isAnimationActive={false} />
                <Bar dataKey="blocked" name="Blocked" fill={C.danger  + "99"} radius={[3,3,0,0]} isAnimationActive={false} />
                <Legend iconType="circle" iconSize={8}
                  formatter={v => <span style={{ color: C.sub, fontSize: 11 }}>{v}</span>} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Attack Vector Analysis" sub="Active threat type intensity">
            <ResponsiveContainer width="100%" height={210}>
              <RadarChart data={vectorData}>
                <PolarGrid stroke={C.border} />
                <PolarAngleAxis dataKey="type" tick={{ fill: C.sub, fontSize: 10 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="score"
                  stroke={C.warning} fill={C.warning + "33"} strokeWidth={2} animationDuration={500} />
                <Tooltip {...tooltipStyle} />
              </RadarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* ── ROW 3: 24h chart ── */}
        <ChartCard title="24-Hour Intrusion Attempts" sub="Hourly access attempts vs blocked events" style={{ marginBottom: 14 }}>
          <ResponsiveContainer width="100%" height={170}>
            <BarChart data={hourlyData} barGap={1}>
              <CartesianGrid stroke={C.border} strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="hour" {...axisProps} />
              <YAxis {...axisProps} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="attempts" name="Attempts" fill={C.warning + "88"} radius={[2,2,0,0]} isAnimationActive={false} />
              <Bar dataKey="blocked"  name="Blocked"  fill={C.danger  + "88"} radius={[2,2,0,0]} isAnimationActive={false} />
              <Legend iconType="circle" iconSize={8}
                formatter={v => <span style={{ color: C.sub, fontSize: 11 }}>{v}</span>} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* ── CONTROLS ── */}
        <div style={{
          background: C.card, borderRadius: 14, border: `1px solid ${C.border}`,
          padding: "14px 20px", display: "flex", gap: 10, marginBottom: 14,
          alignItems: "center", flexWrap: "wrap",
        }}>
          <span style={{ color: C.sub, fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginRight: 4 }}>
            Controls
          </span>
          {[
            { label: running ? "⏸  Pause" : "▶  Resume", color: running ? C.warning : C.success, action: () => setRunning(r => !r) },
            { label: "🚨  Simulate Attack", color: C.danger,  action: simulateAttack },
            { label: "🔄  Reset",           color: C.muted,   action: resetAll },
            { label: "← Home",             color: C.sub,     action: () => setPage("home") },
          ].map(({ label, color, action }) => (
            <button key={label} onClick={action}
              style={{
                padding: "8px 18px", borderRadius: 8, cursor: "pointer",
                background: `${color}18`, border: `1px solid ${color}55`,
                color, fontSize: 13, fontWeight: 600, transition: "background 0.15s",
              }}
              onMouseOver={e => e.currentTarget.style.background = `${color}30`}
              onMouseOut={e  => e.currentTarget.style.background = `${color}18`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* ── THREAT LOGS ── */}
        <div style={{
          background: C.card, borderRadius: 16, border: `1px solid ${C.border}`,
          padding: 24, marginBottom: 40,
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>Threat Logs</div>
              <div style={{ color: C.sub, fontSize: 12, marginTop: 2 }}>Latest detected intrusion attempts</div>
            </div>
            <span style={{
              padding: "3px 12px", borderRadius: 99,
              background: `${C.danger}18`, border: `1px solid ${C.danger}44`,
              color: C.danger, fontSize: 12, fontFamily: "monospace",
            }}>
              {threats.length} events
            </span>
          </div>

          {threats.length === 0 ? (
            <div style={{ textAlign: "center", color: C.muted, padding: "36px 0", fontSize: 14 }}>
              No threats detected yet — start the simulation above.
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {["Time", "Source IP", "Category", "Risk Score", "Status", "Source"].map(h => (
                      <th key={h} style={{
                        padding: "8px 14px", textAlign: "left",
                        color: C.muted, fontWeight: 600, fontSize: 11,
                        textTransform: "uppercase", letterSpacing: 0.8,
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {threats.map((t, i) => (
                    <tr key={i}
                      style={{ borderBottom: `1px solid ${C.border}22`, transition: "background 0.15s" }}
                      onMouseOver={e => e.currentTarget.style.background = `${C.border}44`}
                      onMouseOut={e  => e.currentTarget.style.background = "transparent"}
                    >
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: C.sub,  fontSize: 12 }}>{t.time}</td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: C.text, fontSize: 12 }}>{t.ip}</td>
                      <td style={{ padding: "10px 14px", color: C.sub }}>{t.category}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{ height: 5, width: 64, background: C.border, borderRadius: 99, overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${t.risk}%`, background: riskColor(t.risk), borderRadius: 99 }} />
                          </div>
                          <span style={{ fontFamily: "monospace", fontWeight: 700, color: riskColor(t.risk), minWidth: 26 }}>
                            {t.risk}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: "10px 14px" }}><StatusBadge status={t.status} /></td>
                      <td style={{ padding: "10px 14px" }}><SourceBadge source={t.source} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* View Full Logs button */}
          {threats.length > 0 && (
            <div style={{ textAlign: "center", marginTop: 16 }}>
              <button
                onClick={() => setShowLogs(true)}
                style={{
                  padding: "9px 28px", borderRadius: 8, cursor: "pointer",
                  background: `${C.primary}18`, border: `1px solid ${C.primary}55`,
                  color: C.primary, fontSize: 13, fontWeight: 600,
                  transition: "background 0.15s",
                }}
                onMouseOver={e => e.currentTarget.style.background = `${C.primary}30`}
                onMouseOut={e  => e.currentTarget.style.background = `${C.primary}18`}
              >
                View Full Logs ({threats.length})
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── FULL LOGS MODAL ── */}
      {showLogs && (
        <div
          onClick={() => setShowLogs(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 200,
            background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)",
            display: "flex", alignItems: "center", justifyContent: "center",
            padding: 24,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: C.card, border: `1px solid ${C.border}`,
              borderRadius: 18, width: "100%", maxWidth: 900,
              maxHeight: "80vh", display: "flex", flexDirection: "column",
              boxShadow: `0 0 60px ${C.primary}22`,
            }}
          >
            {/* Modal header */}
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "18px 24px", borderBottom: `1px solid ${C.border}`,
            }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>Full Threat Logs</div>
                <div style={{ color: C.sub, fontSize: 12, marginTop: 2 }}>All {threats.length} recorded events</div>
              </div>
              <button
                onClick={() => setShowLogs(false)}
                style={{
                  background: `${C.muted}22`, border: `1px solid ${C.border}`,
                  color: C.sub, borderRadius: 8, padding: "6px 14px",
                  cursor: "pointer", fontSize: 13, fontWeight: 600,
                }}
              >
                ✕ Close
              </button>
            </div>

            {/* Scrollable table */}
            <div style={{ overflowY: "auto", padding: "0 24px 24px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 16 }}>
                <thead style={{ position: "sticky", top: 0, background: C.card }}>
                  <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                    {["#", "Time", "Source IP", "Category", "Risk Score", "Status", "Source"].map(h => (
                      <th key={h} style={{
                        padding: "8px 14px", textAlign: "left",
                        color: C.muted, fontWeight: 600, fontSize: 11,
                        textTransform: "uppercase", letterSpacing: 0.8,
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {threats.map((t, i) => (
                    <tr key={i}
                      style={{ borderBottom: `1px solid ${C.border}22`, transition: "background 0.15s" }}
                      onMouseOver={e => e.currentTarget.style.background = `${C.border}44`}
                      onMouseOut={e  => e.currentTarget.style.background = "transparent"}
                    >
                      <td style={{ padding: "10px 14px", color: C.muted, fontFamily: "monospace", fontSize: 11 }}>{i + 1}</td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: C.sub,  fontSize: 12 }}>{t.time}</td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: C.text, fontSize: 12 }}>{t.ip}</td>
                      <td style={{ padding: "10px 14px", color: C.sub }}>{t.category}</td>
                      <td style={{ padding: "10px 14px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <div style={{ height: 5, width: 64, background: C.border, borderRadius: 99, overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${t.risk}%`, background: riskColor(t.risk), borderRadius: 99 }} />
                          </div>
                          <span style={{ fontFamily: "monospace", fontWeight: 700, color: riskColor(t.risk), minWidth: 26 }}>
                            {t.risk}
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: "10px 14px" }}><StatusBadge status={t.status} /></td>
                      <td style={{ padding: "10px 14px" }}><SourceBadge source={t.source} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes pulseDot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.4; transform: scale(0.8); }
        }
      `}</style>
    </div>
  );
}

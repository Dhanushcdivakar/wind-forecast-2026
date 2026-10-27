import { useEffect, useMemo, useState } from "react";
import { Activity, BarChart3, CalendarDays, Database, Gauge, Leaf, RefreshCw, Wind, Zap, CircleHelp } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, AreaChart, Area, ReferenceLine } from "recharts";
import { getOverview, getGeneration, getAccuracy, getHistory, getData } from "./api";

const nav = [
  { id: "overview", label: "Overview", icon: Gauge },
  { id: "forecast", label: "Forecast analysis", icon: Wind },
  { id: "accuracy", label: "Forecast accuracy", icon: BarChart3 },
  { id: "explorer", label: "Data explorer", icon: Database }
];
const fmt = (v, d = 0) => v == null || Number.isNaN(Number(v)) ? "—" : Number(v).toLocaleString("en-GB", { maximumFractionDigits: d });
const stamp = v => new Date(v).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }) + " UTC";
const short = v => new Date(v).toLocaleString("en-GB", { day: "2-digit", hour: "2-digit", timeZone: "UTC" });

function Metric({ label, value, unit, hint, icon: Icon, tone = "" }) {
  return <article className={`metric ${tone}`}><div className="metric-head">{label}<span><Icon size={17}/></span></div><div className="metric-value">{value}<small>{unit}</small></div><p>{hint}</p></article>;
}
function Panel({ title, subtitle, children }) {
  return <section className="panel"><div className="panel-head"><div><h2>{title}</h2><p>{subtitle}</p></div></div>{children}</section>;
}
function Table({ rows, history = false }) {
  if (!rows?.length) return <div className="empty">No records for this selection.</div>;
  return <div className="table-scroll"><table><thead><tr><th>Target time (UTC)</th>{history && <th>Published at (UTC)</th>}<th>Forecast (MW)</th>{!history && <><th>Actual (MW)</th><th>Error (MW)</th><th>Absolute error (MW)</th></>}</tr></thead><tbody>{rows.slice(0, 500).map((r, i) => <tr key={`${r.start_time}-${r.publish_time || i}`}><td>{stamp(r.start_time)}</td>{history && <td>{stamp(r.publish_time)}</td>}<td>{fmt(r.forecast, 1)}</td>{!history && <><td>{fmt(r.actual, 1)}</td><td className={r.error > 0 ? "positive" : r.error < 0 ? "negative" : ""}>{r.error > 0 ? "+" : ""}{fmt(r.error, 1)}</td><td>{fmt(r.absolute_error, 1)}</td></>}</tr>)}</tbody></table>{rows.length > 500 && <p className="table-note">Showing first 500 records.</p>}</div>;
}
export default function App() {
  const [page, setPage] = useState("overview");
  const [overview, setOverview] = useState(null), [generation, setGeneration] = useState(null), [accuracy, setAccuracy] = useState(null), [history, setHistory] = useState([]), [table, setTable] = useState([]);
  const [date, setDate] = useState("2026-01-15"), [target, setTarget] = useState(""), [loading, setLoading] = useState(true), [refreshing, setRefreshing] = useState(false), [error, setError] = useState(""), [search, setSearch] = useState("");
  async function load() {
    setError("");
    try {
      const [o, g, a] = await Promise.all([getOverview(), getGeneration(), getAccuracy()]);
      setOverview(o); setGeneration(g); setAccuracy(a);
    } catch (e) { setError(e.message || "Unable to load data."); }
    finally { setLoading(false); setRefreshing(false); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => {
    Promise.all([getHistory(date), getData(date)]).then(([h, d]) => {
      setHistory(h.records || []); setTable(d.records || []);
    }).catch(e => setError(e.message || "Could not load selected date."));
  }, [date]);
  const rows = generation?.selected_forecasts || [];
  const filteredRows = useMemo(() => rows.filter(r => r.start_time.startsWith(date)), [rows, date]);
  const chartRows = useMemo(() => rows.map(r => ({ ...r, label: short(r.start_time) })), [rows]);
  const targetOptions = [...new Set(history.map(r => r.start_time))].sort();
  useEffect(() => { if (targetOptions.length && !targetOptions.includes(target)) setTarget(targetOptions[Math.floor(targetOptions.length / 2)]); }, [history]);
  const selectedHistory = history.filter(r => r.start_time === target);
  const selectedForecast = filteredRows.find(r => r.start_time === target);
  const s = overview?.summary || {};

  const active = nav.find(n => n.id === page);
  const displayTable = table.filter(r => `${r.start_time} ${r.publish_time} ${r.forecast} ${r.actual}`.toLowerCase().includes(search.toLowerCase()));

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-icon"><Wind size={22}/></div><div><b>gridbricks</b><span>ENERGY INTELLIGENCE</span></div></div>
      <p className="section-label">WORKSPACE</p>
      <nav>{nav.map(({id,label,icon:Icon}) => <button key={id} className={`nav-button ${page===id?"active":""}`} onClick={() => setPage(id)}><Icon size={18}/>{label}</button>)}</nav>
      <div className="side-bottom"><div className="help"><CircleHelp size={18}/><b>Forecast guide</b><p>Understand forecast accuracy and decision cutoffs.</p><button onClick={() => setPage("accuracy")}>Explore metrics →</button></div><div className="profile"><span>WF</span><div><b>Wind analytics</b><small>UK national view</small></div></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><div>Analytics <span>/</span> <b>{active?.label}</b></div><div className="top-actions"><span className="badge live">● ELEXON DATA</span><button className="refresh" onClick={() => {setRefreshing(true);load();}} title="Refresh"><RefreshCw size={16} className={refreshing?"spin":""}/></button><span className="month"><CalendarDays size={15}/> January 2026</span></div></header>
      <div className="content">
        <div className="title-row"><div><div className="eyebrow">UK POWER SYSTEMS / WIND</div><h1>{page==="overview"?"Wind forecast overview":active?.label}</h1><p className="subtitle">{page==="overview"?"A clear view of renewable generation forecasts and their accuracy.":page==="forecast"?"Explore forecast vintages and how predictions evolve before delivery.":page==="accuracy"?"Quantify forecast error and understand systematic over- or underestimation.":"Inspect matched forecast and actual observations behind the metrics."}</p></div><span className="period">● January 1–31, 2026</span></div>

        {error && <div className="error"><strong>Could not load data.</strong> {error} <button onClick={load}>Retry</button></div>}
        {loading ? <div className="loader-wrap"><div className="spinner"/></div> : <>
          {page==="overview" && <Overview summary={s} rows={chartRows} decisionRule={overview?.decision_rule} goAccuracy={() => setPage("accuracy")} />}
          {page==="forecast" && <Forecast rows={filteredRows} history={history} date={date} setDate={setDate} target={target} setTarget={setTarget} selectedHistory={selectedHistory} selectedForecast={selectedForecast}/>}
          {page==="accuracy" && <Accuracy summary={s} rows={chartRows} rule={accuracy?.decision_rule}/>}
          {page==="explorer" && <Explorer rows={displayTable} date={date} setDate={setDate} search={search} setSearch={setSearch}/>}
        </>}
        <footer>WIND FORECAST ANALYTICS · JANUARY 2026 <span>Data source: Elexon BMRS · Timestamps shown in UTC</span></footer>
      </div>
    </main>
  </div>;
}
function Overview({summary:s, rows, decisionRule, goAccuracy}) {
  const chart = rows.filter((_,i)=>i%4===0);
  return <>
    <div className="metrics">
      <Metric label="Average actual generation" value={fmt(s.average_actual_mw)} unit="MW" hint="Across January actual intervals" icon={Zap}/>
      <Metric label="Average forecast" value={fmt(s.average_selected_forecast_mw)} unit="MW" hint="Selected eligible forecasts" icon={Wind} tone="purple"/>
      <Metric label="Mean absolute error" value={fmt(s.mae_mw)} unit="MW" hint="Average absolute difference" icon={Activity} tone="orange"/>
      <Metric label="Forecast bias" value={`${s.mbe_mw>0?"+":""}${fmt(s.mbe_mw)}`} unit="MW" hint="Forecast minus actual" icon={Gauge} tone="green"/>
    </div>
    <div className="grid two">
      <Panel title="Actual vs forecast generation" subtitle="Selected day-ahead forecast compared with observed wind generation">
        {chart.length ? <ResponsiveContainer width="100%" height={310}><LineChart data={chart} margin={{top:10,right:12,left:0,bottom:4}}><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e9edf3"/><XAxis dataKey="label" tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false} interval={Math.max(0,Math.floor(chart.length/7))}/><YAxis tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false} width={52} tickFormatter={v=>`${Math.round(v/1000)}k`}/><Tooltip labelFormatter={(v,p)=>p?.[0]?.payload?.start_time?stamp(p[0].payload.start_time):v} formatter={(v,n)=>[`${fmt(v)} MW`,n]}/><Legend wrapperStyle={{fontSize:11,paddingTop:10}}/><Line dataKey="actual" name="Actual generation" stroke="#20a879" strokeWidth={2.2} dot={false}/><Line dataKey="forecast" name="Selected forecast" stroke="#7866e8" strokeWidth={2.2} dot={false} strokeDasharray="5 4"/></LineChart></ResponsiveContainer>:<div className="empty">No observations available.</div>}
      </Panel>
      <Panel title="Accuracy snapshot" subtitle="How close are forecasts to actual generation?">
        <div className="metric-list"><MetricLine label="MAE" name="Mean absolute error" value={s.mae_mw}/><MetricLine label="RMSE" name="Root mean squared error" value={s.rmse_mw}/><MetricLine label="BIAS" name="Mean bias error" value={s.mbe_mw}/></div>
        <div className="mini"><div><small>Matched intervals</small><b>{fmt(s.matched_intervals)}</b></div><div><small>Forecast history records</small><b>{fmt(s.forecast_history_records)}</b></div></div>
        <button className="link" onClick={goAccuracy}>Explore forecast accuracy →</button>
      </Panel>
    </div>
    <div className="grid two bottom">
      <Panel title="How to read this dashboard" subtitle="A quick guide for procurement teams"><div className="guide"><p><b>01 · Compare generation</b><span>See how selected forecasts track actual wind generation.</span></p><p><b>02 · Measure error</b><span>MAE and RMSE help quantify typical and larger errors.</span></p><p><b>03 · Check bias</b><span>Positive bias means forecasts are higher than actuals on average.</span></p></div></Panel>
      <Panel title="Analysis methodology" subtitle="Forecast selection rule"><div className="method"><CalendarDays size={20}/><div><b>Day-ahead forecast vintage</b><p>{decisionRule}</p><em>Provisional rule — validate the correct procurement cutoff before submission.</em></div></div></Panel>
    </div>
  </>;
}
function MetricLine({label,name,value}) { return <div className="metric-line"><span>{label}</span><div><b>{name}</b><small>{label==="MAE"?"Typical forecast difference":label==="RMSE"?"Highlights larger errors":"Direction of forecast error"}</small></div><strong>{fmt(value)} <small>MW</small></strong></div>; }
function Forecast({rows,history,date,setDate,target,setTarget,selectedHistory,selectedForecast}) {
  return <>
    <div className="filters"><label>Delivery date<input type="date" min="2026-01-01" max="2026-01-31" value={date} onChange={e=>setDate(e.target.value)}/></label><label className="wide">Target interval<select value={target} onChange={e=>setTarget(e.target.value)}>{[...new Set(history.map(r=>r.start_time))].sort().map(t=><option key={t} value={t}>{stamp(t)}</option>)}</select></label><span className="count">{history.length} publication records</span></div>
    <div className="metrics three"><Metric label="Forecast publications" value={fmt(selectedHistory.length)} unit="" hint="For selected target interval" icon={Activity}/><Metric label="Selected forecast" value={fmt(selectedForecast?.forecast)} unit="MW" hint="Eligible before cutoff" icon={Wind} tone="purple"/><Metric label="Actual generation" value={fmt(selectedForecast?.actual)} unit="MW" hint="Observed generation" icon={Zap} tone="green"/></div>
    <Panel title="Forecast evolution" subtitle="Forecast generation by publication time for the selected target interval">{selectedHistory.length?<ResponsiveContainer width="100%" height={290}><LineChart data={selectedHistory} margin={{top:12,right:15,left:5,bottom:10}}><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e9edf3"/><XAxis dataKey="publish_time" tickFormatter={v=>new Date(v).toLocaleString("en-GB",{day:"2-digit",hour:"2-digit",timeZone:"UTC"})} tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false}/><YAxis tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false}/><Tooltip labelFormatter={stamp} formatter={v=>[`${fmt(v)} MW`,"Forecast"]}/><Line dataKey="forecast" stroke="#7866e8" strokeWidth={2.5} dot={{r:3}}/>{selectedForecast&&<ReferenceLine y={selectedForecast.actual} stroke="#20a879" strokeDasharray="5 5" label="Actual"/>}</LineChart></ResponsiveContainer>:<div className="empty">No forecast history for this interval.</div>}</Panel>
    <Panel title="Publication history" subtitle="Forecast vintages returned for this target interval"><Table rows={selectedHistory.map(r=>({...r,actual:selectedForecast?.actual}))} history/></Panel>
    <div className="notice"><b>i</b><div><strong>Why publication time matters</strong><p>A forecast published after the purchasing decision cutoff was not available to the team at decision time. Accuracy must use an eligible forecast vintage.</p></div></div>
  </>;
}
function Accuracy({summary:s,rows,rule}) {
  const chart=rows.filter((_,i)=>i%4===0);
  return <>
    <div className="metrics three"><Metric label="Mean absolute error" value={fmt(s.mae_mw)} unit="MW" hint="Average absolute difference" icon={Activity} tone="purple"/><Metric label="Root mean squared error" value={fmt(s.rmse_mw)} unit="MW" hint="Penalizes larger errors" icon={BarChart3} tone="orange"/><Metric label="Mean bias error" value={`${s.mbe_mw>0?"+":""}${fmt(s.mbe_mw)}`} unit="MW" hint={s.mbe_mw>0?"Overestimation on average":s.mbe_mw<0?"Underestimation on average":"Average signed error"} icon={Gauge} tone="green"/></div>
    <Panel title="Forecast error over time" subtitle="Error = selected forecast − actual. Positive values indicate overestimation.">{chart.length?<ResponsiveContainer width="100%" height={320}><AreaChart data={chart} margin={{top:12,right:12,left:0,bottom:4}}><CartesianGrid strokeDasharray="3 5" vertical={false} stroke="#e9edf3"/><XAxis dataKey="label" tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false} interval={Math.max(0,Math.floor(chart.length/7))}/><YAxis tick={{fontSize:10,fill:"#8793a5"}} axisLine={false} tickLine={false}/><ReferenceLine y={0} stroke="#aab2c0"/><Tooltip formatter={v=>[`${fmt(v)} MW`,"Forecast error"]}/><Area dataKey="error" stroke="#e79b44" fill="#f7d7ad" fillOpacity={0.55}/></AreaChart></ResponsiveContainer>:<div className="empty">No observations available.</div>}</Panel>
    <div className="grid two bottom"><Panel title="Metric definitions" subtitle="How to interpret the numbers"><div className="guide"><p><b>MAE</b><span>Average error magnitude, ignoring whether it is positive or negative. Lower is generally better.</span></p><p><b>RMSE</b><span>Larger errors have more influence on the result.</span></p><p><b>MBE / Bias</b><span>Average forecast minus actual. Positive means overestimation; negative means underestimation.</span></p></div></Panel><Panel title="Methodology notes" subtitle="Interpret metrics with care"><div className="method"><CircleHelp size={20}/><div><b>Matched intervals only</b><p>Metrics include only intervals with both an eligible forecast and an actual observation.</p><em>{rule}</em></div></div></Panel></div>
  </>;
}
function Explorer({rows,date,setDate,search,setSearch}) {
  return <><div className="filters"><label>Delivery date<input type="date" min="2026-01-01" max="2026-01-31" value={date} onChange={e=>setDate(e.target.value)}/></label><label className="search">Search records<input type="search" placeholder="Search time or values…" value={search} onChange={e=>setSearch(e.target.value)}/></label><span className="count">{rows.length} rows</span></div><Panel title="Matched observations" subtitle="Selected eligible forecast compared with actual generation"><Table rows={rows}/></Panel><div className="notice"><b>i</b><div><strong>Data interpretation</strong><p>Only intervals with both selected forecasts and actual generation are included in accuracy metrics. Validate publication timestamps and the decision cutoff.</p></div></div></>;
}

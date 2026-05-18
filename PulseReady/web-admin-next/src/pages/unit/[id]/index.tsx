import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";

const LiveUnit = dynamic<{ unitId: string }>(
  () => import("../../../components/LiveUnit"),
  { ssr: false }
);

type Metric = {
  user_id: string; unit_id: string; mrs: number; ori: string;
  components: Record<string, number>; ts: string;
};

function parseTs(s: string): number {
  if (!s) return NaN;
  const fixed = s.replace("+00:00Z", "Z");
  const t = Date.parse(fixed);
  return isNaN(t) ? Date.parse(fixed.replace("Z", "+00:00")) : t;
}

export default function UnitView() {
  const unitId = "alpha";
  const [err, setErr] = useState("");
  const [latestByUser, setLatestByUser] = useState<Record<string, Metric>>({});
  const wsRef = useRef<WebSocket | null>(null);

  // ---- 1) Fast poll every 1s: use /series to refresh cards (same as charts) ----
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const tok = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";

    let timer: any;
    const tick = async () => {
      try {
        const res = await fetch(`${base}/series/unit/${unitId}?seconds=60`, {
          headers: { Authorization: "Bearer " + tok },
        });
        if (!res.ok) return;
        const data = await res.json();
        // build latest derived per user_id
        const latest: Record<string, Metric> = {};
        for (const d of (data.derived || []) as any[]) {
          const m: Metric = {
            user_id: d.user_id,
            unit_id: unitId,
            mrs: d.mrs,
            ori: d.ori,
            components: d.components || {},
            ts: d.ts,
          };
          const t = parseTs(m.ts);
          const prev = latest[m.user_id];
          if (!prev || t > parseTs(prev.ts)) latest[m.user_id] = m;
        }
        // only update state if changed to avoid extra re-renders
        setLatestByUser(prev => {
          const prevKeys = Object.keys(prev).sort().join(",");
          const newKeys = Object.keys(latest).sort().join(",");
          if (prevKeys !== newKeys) return latest;
          let changed = false;
          for (const k of Object.keys(latest)) {
            if (parseTs(latest[k].ts) !== parseTs(prev[k]?.ts)) { changed = true; break; }
            if (latest[k].mrs !== prev[k].mrs || latest[k].ori !== prev[k].ori) { changed = true; break; }
          }
          return changed ? latest : prev;
        });
      } catch {}
    };

    tick();
    timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [unitId]);

  // ---- 2) Slow poll /metrics (5s) as extra safety ----
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const tok = typeof window !== "undefined" ? localStorage.getItem("token") || "" : "";
    let id: any;

    const pollOnce = async () => {
      try {
        const res = await fetch(`${base}/metrics?unitId=${unitId}&limit=200`, {
          headers: { Authorization: "Bearer " + tok },
        });
        if (!res.ok) { setErr("Failed to load metrics"); return; }
        const data = await res.json();
        const map: Record<string, Metric> = {};
        (data.items || []).forEach((m: Metric) => {
          const t = parseTs(m.ts);
          const prev = map[m.user_id];
          if (!prev || t > parseTs(prev.ts)) map[m.user_id] = m;
        });
        setLatestByUser(prev => Object.keys(prev).length ? prev : map); // don’t overwrite if series already populated
      } catch { setErr("Network error"); }
    };

    pollOnce();
    id = setInterval(pollOnce, 5000);
    return () => clearInterval(id);
  }, [unitId]);

  // ---- 3) WS (optional). If it works, it will “win” with freshest timestamps ----
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";
    const url = `${base}/ws/units/${unitId}`;
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          const p = msg?.payload;
          if (msg.type === "derived" && p) {
            const m: Metric = {
              user_id: p.user_id, unit_id: p.unit_id, mrs: p.mrs, ori: p.ori,
              components: { fatigue: p.fatigue, recovery: p.recovery, heat: p.heat, altitude: p.altitude, sleep: p.sleep },
              ts: p.ts,
            };
            setLatestByUser(prev => {
              const prevM = prev[m.user_id];
              if (!prevM || parseTs(m.ts) >= parseTs(prevM.ts)) return { ...prev, [m.user_id]: m };
              return prev;
            });
          }
        } catch {}
      };
    } catch {}
    const ping = setInterval(() => { try { ws?.readyState === 1 && ws.send("ping"); } catch {} }, 20000);
    return () => { clearInterval(ping); try { ws?.close(); } catch {} };
  }, [unitId]);

  const users = useMemo(() => Object.keys(latestByUser).sort(), [latestByUser]);

  function color(ori: string) {
    if (!ori) return "#6b7280";
    const v = ori.toLowerCase();
    if (v === "red") return "#ef4444";
    if (v === "amber" || v === "yellow") return "#f59e0b";
    return "#22c55e";
  }

  return (
    <main style={{ maxWidth: 1100, margin: "40px auto", fontFamily: "ui-sans-serif" }}>
      <h1>Unit: {unitId}</h1>
      <p style={{ marginBottom: 16 }}>
        <Link href={`/unit/${unitId}/weights`}>Weights</Link>
      </p>
      {err && <p style={{ color: "red" }}>{err}</p>}

      {/* Cards — now driven by /series (1s) + WS (optional) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(260px,1fr))", gap: 16 }}>
        {users.map((uid) => {
          const m = latestByUser[uid];
          const t = parseTs(m.ts);
          return (
            <div key={uid} style={{ border: "1px solid #e5e7eb", borderRadius: 12, padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: 18 }}>{uid}</strong>
                <span style={{ background: color(m.ori), color: "white", borderRadius: 999, padding: "4px 10px", fontWeight: 700 }}>
                  {(m.ori || "—").toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: 40, fontWeight: 800, marginTop: 8 }}>{Math.round(m.mrs)}</div>
              <div style={{ fontSize: 12, color: "#6b7280" }}>
                {isNaN(t) ? "—" : new Date(t).toLocaleTimeString()}
              </div>
              <details style={{ marginTop: 8 }}>
                <summary>Components</summary>
                <ul>
                  {Object.entries(m.components || {}).map(([k, v]) => (
                    <li key={k}>{k}: {typeof v === "number" ? v.toFixed(1) : String(v)}</li>
                  ))}
                </ul>
              </details>
            </div>
          );
        })}
      </div>

      {/* Charts (already polling /series every 1s) */}
      <LiveUnit unitId={unitId} />
    </main>
  );
}

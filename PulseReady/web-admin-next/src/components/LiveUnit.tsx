"use client";
import { useEffect, useRef, useState } from "react";
import {
  Chart, LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, CategoryScale,
} from "chart.js";
import "chartjs-adapter-date-fns";
import { Line } from "react-chartjs-2";

Chart.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, CategoryScale);

function parseTs(s: string): number {
  if (!s) return NaN;
  const fixed = s.replace("+00:00Z", "Z");
  const t = Date.parse(fixed);
  return isNaN(t) ? Date.parse(fixed.replace("Z", "+00:00")) : t;
}

type LivePoint = { x: number; y: number };

export default function LiveUnit({ unitId }: { unitId: string }) {
  const [hrSeries, setHrSeries] = useState<Record<string, LivePoint[]>>({});
  const [mrsSeries, setMrsSeries] = useState<Record<string, LivePoint[]>>({});

  // polling fallback each 1s
  useEffect(() => {
    let timer: any;
    async function tick() {
      try {
        const tok = localStorage.getItem("token") || "";
        const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
        const res = await fetch(`${base}/series/unit/${unitId}?seconds=60`, {
          headers: { Authorization: "Bearer " + tok },
        });
        if (!res.ok) return;
        const data = await res.json();

        // HR
        const hr: Record<string, LivePoint[]> = {};
        for (const p of data.raw as any[]) {
          const t = parseTs(p.ts); if (isNaN(t)) continue;
          (hr[p.user_id] ||= []).push({ x: t, y: p.hr });
        }
        // MRS
        const mrs: Record<string, LivePoint[]> = {};
        for (const q of data.derived as any[]) {
          const t = parseTs(q.ts); if (isNaN(t)) continue;
          (mrs[q.user_id] ||= []).push({ x: t, y: q.mrs });
        }

        setHrSeries(hr);
        setMrsSeries(mrs);
      } catch {}
    }
    tick();
    timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [unitId]);

  // datasets
  const hrDatasets = Object.keys(hrSeries).sort().map((uid, idx) => ({
    label: `HR – ${uid}`,
    data: hrSeries[uid],
    borderWidth: 2,
    pointRadius: 0,
  }));
  const mrsDatasets = Object.keys(mrsSeries).sort().map((uid, idx) => ({
    label: `MRS – ${uid}`,
    data: mrsSeries[uid],
    borderWidth: 2,
    pointRadius: 0,
  }));

  const commonOpts = {
    responsive: true,
    animation: false as const,
    scales: {
      x: { type: "time" as const, time: { unit: "second" as const } },
      y: { beginAtZero: true },
    },
    plugins: { legend: { display: true } },
  };

  return (
    <div style={{ marginTop: 24 }}>
      <h3>Live Heart Rate</h3>
      <Line data={{ datasets: hrDatasets }} options={{ ...commonOpts, scales: { ...commonOpts.scales, y: { beginAtZero: true, suggestedMax: 200 } } }} />
      <h3 style={{ marginTop: 24 }}>Live Mission Readiness Score (MRS)</h3>
      <Line data={{ datasets: mrsDatasets }} options={{ ...commonOpts, scales: { ...commonOpts.scales, y: { beginAtZero: true, suggestedMax: 100 } } }} />
    </div>
  );
}

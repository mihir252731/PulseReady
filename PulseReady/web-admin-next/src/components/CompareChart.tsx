import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS, LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, CategoryScale
} from "chart.js";

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, CategoryScale);

export type SeriesPoint = { t: number; y: number };
type Props = {
  title?: string;
  labelA: string;
  dataA: SeriesPoint[];
  labelB: string;
  dataB: SeriesPoint[];
};

export default function CompareChart({ title = "Comparison", labelA, dataA, labelB, dataB }: Props) {
  const data = {
    labels: dataA.map(p => new Date(p.t).toLocaleTimeString()),
    datasets: [
      {
        label: labelA,
        data: dataA.map(p => p.y),
        borderColor: "#2563eb",   // blue-600
        backgroundColor: "rgba(37, 99, 235, 0.2)",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: labelB,
        data: dataB.map(p => p.y),
        borderColor: "#ef4444",   // red-500
        backgroundColor: "rgba(239, 68, 68, 0.2)",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
      },
    ],
  };

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" as const },
      tooltip: { intersect: false, mode: "index" as const },
      title: { display: !!title, text: title },
    },
    scales: {
      x: { grid: { display: false }},
      y: { grid: { color: "rgba(0,0,0,0.06)" }, beginAtZero: true }
    }
  };

  return (
    <div className="w-full h-80 p-4 rounded-2xl shadow-sm border">
      <Line data={data} options={options} />
    </div>
  );
}

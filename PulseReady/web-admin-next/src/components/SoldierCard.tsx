import React from "react";

type Props = {
  id: string;
  name?: string;
  latestHr?: number;
  latestMrs?: number;
  selected?: boolean;
  compareMode?: boolean;
  onToggleSelect?: (id: string) => void;
  onShowLive?: (id: string) => void;
};

export default function SoldierCard({
  id, name, latestHr, latestMrs, selected = false, compareMode = false, onToggleSelect, onShowLive
}: Props) {
  return (
    <div className={`p-4 rounded-xl border shadow-sm flex items-center justify-between ${selected ? "ring-2 ring-blue-500" : ""}`}>
      <div>
        <div className="font-semibold">{name ?? id}</div>
        <div className="text-sm text-gray-600">HR: {latestHr ?? "—"} | MRS: {latestMrs ?? "—"}</div>
      </div>

      <div className="flex items-center gap-3">
        {compareMode && (
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onToggleSelect?.(id)}
            />
            <span className="text-sm">Compare</span>
          </label>
        )}

        <div className="relative">
          <button className="px-3 py-1 rounded-lg border hover:bg-gray-50">Actions ▾</button>
          <div className="absolute right-0 mt-2 w-44 bg-white border rounded-xl shadow z-10 hidden group-hover:block"></div>
        </div>

        <div className="dropdown">
          <button className="px-3 py-1 rounded-lg border hover:bg-gray-50">⋮</button>
          <div className="absolute bg-white border rounded-xl shadow p-2 hidden"></div>
        </div>

        <button
          className="px-3 py-1 rounded-lg border hover:bg-gray-50"
          onClick={() => onShowLive?.(id)}
        >
          Show live chart
        </button>
      </div>
    </div>
  );
}


import { useEffect, useState } from "react";
import Link from "next/link";

const KEYS = ["fatigue","recovery","heat","altitude","sleep"] as const;
type Weights = Record<typeof KEYS[number], number>;

export default function WeightsEditor() {
  const [w,setW]=useState<Weights>({fatigue:.3,recovery:.3,heat:.2,altitude:.1,sleep:.1});
  const [err,setErr]=useState("");
  const [ok,setOk]=useState("");

  async function load() {
    const tok = localStorage.getItem("token") || "";
    const res = await fetch(process.env.NEXT_PUBLIC_API_BASE + "/weights/alpha", {
      headers: { "Authorization": "Bearer " + tok }
    });
    if (!res.ok) { setErr("Failed to load weights"); return; }
    const data = await res.json(); setW(data);
  }

  async function save() {
    const tok = localStorage.getItem("token") || "";
    setErr(""); setOk("");
    const res = await fetch(process.env.NEXT_PUBLIC_API_BASE + "/weights/alpha", {
      method: "PUT",
      headers: { "Content-Type":"application/json", "Authorization": "Bearer " + tok },
      body: JSON.stringify(w)
    });
    if (!res.ok) { setErr("Failed to save"); return; }
    setOk("Saved");
  }

  useEffect(()=>{ load(); },[]);
  const total = KEYS.reduce((a,k)=>a+w[k],0);
  const disabled = Math.abs(total-1)>0.02;

  return (
    <main style={{maxWidth:600, margin:"40px auto", fontFamily:"ui-sans-serif"}}>
      <h1>Weights (alpha)</h1>
      <p><Link href="/unit/alpha">← Back</Link></p>
      {KEYS.map(k=>(
        <div key={k} style={{margin:"12px 0"}}>
          <label style={{display:"block"}}>{k} ({w[k].toFixed(2)})</label>
          <input type="range" min="0" max="1" step="0.05" value={w[k]}
            onChange={e=>setW({...w, [k]: parseFloat(e.target.value)})} style={{width:"100%"}}/>
        </div>
      ))}
      <p>Total: {total.toFixed(2)} {disabled && <span style={{color:"red"}}> (must be ≈ 1.00)</span>}</p>
      <button onClick={save} disabled={disabled}>Save</button>
      {err && <p style={{color:"red"}}>{err}</p>}
      {ok && <p style={{color:"green"}}>{ok}</p>}
    </main>
  )
}

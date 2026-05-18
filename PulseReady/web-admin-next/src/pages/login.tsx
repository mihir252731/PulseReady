import { useState } from "react";

export default function Login() {
  const [u,setU]=useState(""); const [p,setP]=useState(""); const [err,setErr]=useState("");

  function apiBase() {
    // fallback if env is missing
    return process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  }

  async function go() {
    setErr("");
    try {
      const res = await fetch(apiBase() + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({username:u, password:p})
      });
      if (!res.ok) {
        const text = await res.text().catch(()=> "");
        setErr(`Login failed (${res.status}). ${text || "Check backend URL and credentials."}`);
        return;
      }
      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      window.location.href="/unit/alpha";
    } catch (e:any) {
      setErr(`Network error. Is the API running at ${apiBase()} ?`);
    }
  }

  return (
    <main style={{maxWidth:420, margin:"80px auto", fontFamily:"ui-sans-serif"}}>
      <h1>HPPMS Admin</h1>
      <label>Username</label>
      <input value={u} onChange={e=>setU(e.target.value)} style={{display:"block", width:"100%", marginBottom:8}}/>
      <label>Password</label>
      <input type="password" value={p} onChange={e=>setP(e.target.value)} style={{display:"block", width:"100%", marginBottom:8}}/>
      <button onClick={go}>Login</button>
      {err && <p style={{color:"red", marginTop:12}}>{err}</p>}
      <p style={{fontSize:12, color:"#6b7280", marginTop:8}}>
        API base: {process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"}
      </p>
    </main>
  );
}

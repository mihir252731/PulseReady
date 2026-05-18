import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    // if already logged in, go to unit page; else go to login
    const tok = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    window.location.href = tok ? "/unit/alpha" : "/login";
  }, []);
  return null;
}

import os, sqlite3, asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from jose import jwt, JWTError

# ------------------ Config ------------------
TEAM_KEY = os.getenv("TEAM_KEY", "CHANGE_ME")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = "HS256"
TOKEN_TTL_MIN = int(os.getenv("TOKEN_TTL_MIN", "480"))
DB_PATH = os.getenv("DB_PATH", "db.sqlite")

# Optional comma-separated device whitelist to double-lock
ENV_DEVICE_WHITELIST = {d.strip() for d in os.getenv("DEVICE_WHITELIST", "").split(",") if d.strip()}

# ------------------ App ------------------
app = FastAPI(
    title="HPPMS Backend (FastAPI)",
    description="Hackathon backend for Human Physical Performance Management",
    version="0.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# ------------------ SQLite helpers ------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        unit_id TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        user_id TEXT,
        last_seen DATETIME
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS raw_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        user_id TEXT,
        unit_id TEXT,
        ts DATETIME,
        hr INTEGER,
        rr REAL,
        spo2 REAL,
        temp REAL,
        accel_json TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS derived_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        user_id TEXT,
        unit_id TEXT,
        ts DATETIME,
        mrs INTEGER,
        ori TEXT,
        fatigue REAL,
        recovery REAL,
        heat REAL,
        altitude REAL,
        sleep REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS weights (
        unit_id TEXT PRIMARY KEY,
        fatigue REAL, recovery REAL, heat REAL, altitude REAL, sleep REAL
    )""")
    # seed defaults
    cur.execute("INSERT OR IGNORE INTO users (id,name,unit_id) VALUES ('u123','Demo User','alpha')")
    cur.execute("INSERT OR IGNORE INTO users (id,name,unit_id) VALUES ('u_judge','Judge','alpha')")
    cur.execute("INSERT OR IGNORE INTO weights (unit_id,fatigue,recovery,heat,altitude,sleep) VALUES ('alpha',0.3,0.3,0.2,0.1,0.1)")
    conn.commit()
    conn.close()

create_tables()

def norm_ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def now_iso() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def device_is_allowed(device_id: str) -> bool:
    if not device_id:
        return False
    # ENV list blocks anything not present when provided
    if ENV_DEVICE_WHITELIST and device_id not in ENV_DEVICE_WHITELIST:
        return False
    # If a device row exists, it's allowed; else disallow until registered
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT 1 FROM devices WHERE device_id=?", (device_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def touch_device(device_id: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO devices (device_id, user_id, last_seen)
                   VALUES (?, NULL, ?)
                   ON CONFLICT(device_id) DO UPDATE SET last_seen=excluded.last_seen
                """, (device_id, now_iso()))
    conn.commit(); conn.close()

# ------------------ Auth helpers ------------------
class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    exp: int

def create_token(sub: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MIN)
    payload = {"sub": sub, "exp": int(exp.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_token(auth_header: Optional[str]) -> str:
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        scheme, token = auth_header.split(" ", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload.get("sub") or "unknown"
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn):
    if body.username == ADMIN_USER and body.password == ADMIN_PASS:
        tok = create_token("admin")
        exp = int((datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MIN)).timestamp())
        return TokenOut(access_token=tok, exp=exp)
    raise HTTPException(status_code=401, detail="Bad credentials")

# ------------------ Models ------------------
class Weights(BaseModel):
    fatigue: float
    recovery: float
    heat: float
    altitude: float
    sleep: float

class RawSampleIn(BaseModel):
    device_id: str
    user_id: str
    unit_id: str
    ts: datetime
    hr: int
    rr: Optional[float] = None
    spo2: Optional[float] = None
    temp: Optional[float] = None
    accel_json: Optional[str] = None

class DerivedIn(BaseModel):
    device_id: str
    user_id: str
    unit_id: str
    ts: datetime
    mrs: int = Field(ge=0, le=100)
    ori: str
    fatigue: float
    recovery: float
    heat: float
    altitude: float
    sleep: float

# ------------------ WebSocket manager ------------------
class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, unit_id: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms.setdefault(unit_id, []).append(websocket)

    async def disconnect(self, unit_id: str, websocket: WebSocket):
        if unit_id in self.rooms and websocket in self.rooms[unit_id]:
            self.rooms[unit_id].remove(websocket)

    async def broadcast(self, unit_id: str, message: dict):
        conns = self.rooms.get(unit_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(unit_id, ws)

manager = ConnectionManager()

@app.websocket("/ws/units/{unit_id}")
async def ws_units(websocket: WebSocket, unit_id: str):
    await manager.connect(unit_id, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(unit_id, websocket)

@app.get("/series/unit/{unit_id}")
def series_unit(unit_id: str, seconds: int = 60, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    since = now - timedelta(seconds=seconds)
    since_s = norm_ts(since)

    conn = get_conn(); cur = conn.cursor()

    cur.execute("""
        SELECT ts, user_id, hr
        FROM raw_samples
        WHERE unit_id=? AND ts >= ?
        ORDER BY ts ASC
    """, (unit_id, since_s))
    raw_rows = cur.fetchall()

    cur.execute("""
        SELECT ts, user_id, mrs, ori, fatigue, recovery, heat, altitude, sleep
        FROM derived_samples
        WHERE unit_id=? AND ts >= ?
        ORDER BY ts ASC
    """, (unit_id, since_s))
    der_rows = cur.fetchall()

    conn.close()

    raw = [{"ts": r["ts"], "user_id": r["user_id"], "hr": r["hr"]} for r in raw_rows]
    derived = [{
        "ts": d["ts"], "user_id": d["user_id"], "mrs": d["mrs"], "ori": d["ori"],
        "components": {
            "fatigue": d["fatigue"], "recovery": d["recovery"], "heat": d["heat"],
            "altitude": d["altitude"], "sleep": d["sleep"]
        }
    } for d in der_rows]

    return {"raw": raw, "derived": derived}

# ------------------ Routes ------------------
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h2>HPPMS API</h2>
    <ul>
      <li><a href="/health">/health</a></li>
      <li><a href="/docs">/docs</a></li>
    </ul>
    """

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/users")
def list_users(unitId: Optional[str] = None, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_conn(); cur = conn.cursor()
    if unitId:
        cur.execute("SELECT * FROM users WHERE unit_id=?", (unitId,))
    else:
        cur.execute("SELECT * FROM users")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/weights/{unitId}", response_model=Weights)
def get_weights(unitId: str, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT fatigue,recovery,heat,altitude,sleep FROM weights WHERE unit_id=?", (unitId,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return Weights(fatigue=0.3, recovery=0.3, heat=0.2, altitude=0.1, sleep=0.1)
    return Weights(**dict(row))

@app.put("/weights/{unitId}")
def put_weights(unitId: str, w: Weights, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    total = w.fatigue + w.recovery + w.heat + w.altitude + w.sleep
    if abs(total - 1.0) > 0.02:
        raise HTTPException(status_code=400, detail="weights must sum ≈ 1.0")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO weights (unit_id,fatigue,recovery,heat,altitude,sleep)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(unit_id) DO UPDATE SET
                     fatigue=excluded.fatigue,
                     recovery=excluded.recovery,
                     heat=excluded.heat,
                     altitude=excluded.altitude,
                     sleep=excluded.sleep
                """, (unitId, w.fatigue, w.recovery, w.heat, w.altitude, w.sleep))
    conn.commit(); conn.close()
    return {"ok": True, "weights": w.dict()}

# ---------- Device registration (admin) ----------
class DeviceIn(BaseModel):
    device_id: str
    user_id: Optional[str] = None

@app.post("/devices/register")
def register_device(d: DeviceIn, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    if not d.device_id:
        raise HTTPException(400, "device_id required")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO devices (device_id,user_id,last_seen)
                   VALUES (?,?,?)
                   ON CONFLICT(device_id) DO UPDATE SET user_id=excluded.user_id""",
                (d.device_id, d.user_id, now_iso()))
    conn.commit(); conn.close()
    return {"ok": True}

# ---------- Ingest (device) ----------
@app.post("/sample/raw")
async def post_raw(s: RawSampleIn, x_device_key: Optional[str] = Header(None)):
    if x_device_key != TEAM_KEY:
        raise HTTPException(401, "Bad device key")
    if not device_is_allowed(s.device_id):
        raise HTTPException(403, f"Device {s.device_id} not whitelisted")
    # normalize/cast just in case watch sends 59.9 → 60
    hr = int(round(s.hr))
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """INSERT INTO raw_samples (device_id,user_id,unit_id,ts,hr,rr,spo2,temp,accel_json)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (s.device_id, s.user_id, s.unit_id, norm_ts(s.ts), hr, s.rr, s.spo2, s.temp, s.accel_json)
    )
    cur.execute("""UPDATE devices SET last_seen=? WHERE device_id=?""", (now_iso(), s.device_id))
    conn.commit(); conn.close()
    await manager.broadcast(s.unit_id, {"type": "raw", "payload": {
        "device_id": s.device_id, "user_id": s.user_id, "unit_id": s.unit_id, "ts": norm_ts(s.ts),
        "hr": hr, "rr": s.rr, "spo2": s.spo2, "temp": s.temp
    }})
    return {"ok": True}

@app.post("/sample/derived")
async def post_derived(d: DerivedIn, x_device_key: Optional[str] = Header(None)):
    if x_device_key != TEAM_KEY:
        raise HTTPException(401, "Bad device key")
    if not device_is_allowed(d.device_id):
        raise HTTPException(403, f"Device {d.device_id} not whitelisted")
    conn = get_conn(); cur = conn.cursor()
    cur.execute(
        """INSERT INTO derived_samples (device_id,user_id,unit_id,ts,mrs,ori,fatigue,recovery,heat,altitude,sleep)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (d.device_id, d.user_id, d.unit_id, norm_ts(d.ts), d.mrs, d.ori, d.fatigue, d.recovery, d.heat, d.altitude, d.sleep)
    )
    cur.execute("""UPDATE devices SET last_seen=? WHERE device_id=?""", (now_iso(), d.device_id))
    conn.commit(); conn.close()
    await manager.broadcast(d.unit_id, {"type": "derived", "payload": {
        **d.dict(), "ts": norm_ts(d.ts)
    }})
    return {"ok": True}

@app.get("/samples/raw")
def get_raw(device_id: str, since: Optional[str] = None, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_conn(); cur = conn.cursor()
    if since:
        cur.execute("SELECT * FROM raw_samples WHERE device_id=? AND ts>=? ORDER BY ts", (device_id, since))
    else:
        cur.execute("SELECT * FROM raw_samples WHERE device_id=? ORDER BY ts DESC LIMIT 1000", (device_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"items": rows}

@app.get("/samples/derived")
def get_derived(device_id: str, since: Optional[str] = None, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_conn(); cur = conn.cursor()
    if since:
        cur.execute("SELECT * FROM derived_samples WHERE device_id=? AND ts>=? ORDER BY ts", (device_id, since))
    else:
        cur.execute("SELECT * FROM derived_samples WHERE device_id=? ORDER BY ts DESC LIMIT 1000", (device_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"items": rows}

@app.get("/metrics")
def list_metrics(unitId: str, limit: int = 200, authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT user_id, unit_id, ts, mrs, ori, fatigue, recovery, heat, altitude, sleep
        FROM derived_samples
        WHERE unit_id=?
        ORDER BY ts ASC
        LIMIT ?
    """, (unitId, limit))
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        items.append({
            "user_id": d["user_id"],
            "unit_id": d["unit_id"],
            "mrs": d["mrs"],
            "ori": d["ori"],
            "components": {
                "fatigue": d["fatigue"],
                "recovery": d["recovery"],
                "heat": d["heat"],
                "altitude": d["altitude"],
                "sleep": d["sleep"],
            },
            "ts": d["ts"],
        })
    return {"items": items}

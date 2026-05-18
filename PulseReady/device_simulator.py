import os, time, random, datetime, requests, math

API = os.getenv("API","http://localhost:8000")
KEY = os.getenv("TEAM_KEY","CHANGE_ME")
USER = os.getenv("USER_ID","u123")
UNIT = os.getenv("UNIT_ID","alpha")
DEVICE = os.getenv("DEVICE_ID","dev_u123")

def compute_mrs(fatigue, recovery, heat, altitude=10, sleep=10):
    penalty = 0.3*fatigue + 0.3*recovery + 0.2*heat + 0.1*altitude + 0.1*sleep
    return max(0, 100 - int(round(penalty)))

while True:
    t = time.time()
    hr = int(70 + 40*max(0, math.sin(t/6.0)) + random.uniform(-3,3))
    fatigue = 40 + 20*math.sin(t/30.0) + random.uniform(-5,5)
    recovery = 30 + 15*math.sin(t/45.0+1) + random.uniform(-4,4)
    heat = 10 + 25*max(0, math.sin(t/60.0-1)) + random.uniform(-3,3)
    altitude = 10; sleep = 10
    mrs = compute_mrs(fatigue, recovery, heat, altitude, sleep)
    ori = "green" if mrs>=75 else ("amber" if mrs>=60 else "red")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # RAW
    raw = {
        "device_id": DEVICE, "user_id": USER, "unit_id": UNIT,
        "ts": now, "hr": hr, "rr": 14.0, "spo2": 98.0, "temp": 36.6, "accel_json": None
    }
    requests.post(f"{API}/sample/raw", json=raw, headers={"x-device-key": KEY, "Content-Type":"application/json"})

    # DERIVED
    der = {
        "device_id": DEVICE, "user_id": USER, "unit_id": UNIT, "ts": now,
        "mrs": mrs, "ori": ori,
        "fatigue": float(fatigue), "recovery": float(recovery), "heat": float(heat),
        "altitude": float(altitude), "sleep": float(sleep)
    }
    requests.post(f"{API}/sample/derived", json=der, headers={"x-device-key": KEY, "Content-Type":"application/json"})

    time.sleep(1)

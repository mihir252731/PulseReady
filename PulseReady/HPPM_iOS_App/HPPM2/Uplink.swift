import Foundation

struct API {
    // set this to your Windows machine LAN IP + :8000
    static var base = "http://10.37.1.21:8000"
    static var teamKey = "CHANGE_ME"
    static var deviceId = "mih_u123"
    static var userId   = "mih123"
    static var unitId   = "alpha"
}

final class Poster {
    static let shared = Poster()
    private let session = URLSession(configuration: .default)

    func postRaw(ts: String, hr: Double?, rr: Double?, spo2: Double?, temp: Double?) {
        // backend requires hr; skip if none
        guard let hr = hr else { return }

        var body: [String: Any] = [
            "device_id": API.deviceId,
            "user_id": API.userId,
            "unit_id": API.unitId,
            "ts": ts,
            "hr": Int(hr.rounded())
        ]
        if let rr { body["rr"] = rr }
        if let spo2 { body["spo2"] = spo2 }
        if let temp { body["temp"] = temp }

        var req = URLRequest(url: URL(string: "\(API.base)/sample/raw")!)
        req.httpMethod = "POST"
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        req.addValue(API.teamKey, forHTTPHeaderField: "x-device-key")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        session.dataTask(with: req).resume()
    }

    func postDerived(ts: String, mrs: Double, ori: String,
                     fatigue: Double, recovery: Double, heat: Double, altitude: Double, sleep: Double) {
        let body: [String: Any] = [
            "device_id": API.deviceId, "user_id": API.userId, "unit_id": API.unitId, "ts": ts,
            "mrs": Int(mrs.rounded()), "ori": ori,
            "fatigue": fatigue, "recovery": recovery, "heat": heat, "altitude": altitude, "sleep": sleep
        ]
        var req = URLRequest(url: URL(string: "\(API.base)/sample/derived")!)
        req.httpMethod = "POST"
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        req.addValue(API.teamKey, forHTTPHeaderField: "x-device-key")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        session.dataTask(with: req).resume()
    }
}

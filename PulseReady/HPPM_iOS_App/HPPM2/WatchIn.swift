import WatchConnectivity
import Foundation

final class WatchIn: NSObject, WCSessionDelegate {
    static let shared = WatchIn()

    func activate() {
        guard WCSession.isSupported() else { return }
        let s = WCSession.default
        s.delegate = self
        s.activate()
    }

    func session(_ session: WCSession,
                 activationDidCompleteWith activationState: WCSessionActivationState,
                 error: (any Error)?) {}

    func session(_ session: WCSession, didReceiveMessage message: [String : Any]) {
        // Only forward while workout is active
        guard WorkoutManager.shared.isActive else { return }

        guard let type = message["type"] as? String,
              let ts = message["ts"] as? String else { return }

        if type == "raw" {
            let kind = message["kind"] as? String ?? ""
            let value = message["value"] as? Double
            var hr: Double? = nil, rr: Double? = nil, spo2: Double? = nil

            switch kind {
            case "hr": hr = value
            case "rr": rr = value
            case "spo2": spo2 = value
            default: break
            }

            // Only send /sample/raw when HR is present (backend requires hr)
            if let hr = hr {
                Poster.shared.postRaw(ts: ts, hr: hr, rr: rr, spo2: spo2, temp: nil)
            }
            DerivedComputer.shared.ingest(ts: ts, hr: hr, rr: rr, spo2: spo2, kcal: nil)
        }
    }

    // required stubs
    func sessionDidBecomeInactive(_ session: WCSession) {}
    func sessionDidDeactivate(_ session: WCSession) { WCSession.default.activate() }
    func sessionReachabilityDidChange(_ session: WCSession) {}
}

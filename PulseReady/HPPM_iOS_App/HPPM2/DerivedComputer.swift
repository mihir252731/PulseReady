import Foundation

final class DerivedComputer {
    static let shared = DerivedComputer()
    private var lastPost = Date.distantPast
    private var hrBuf: [Double] = []
    private var latestTS: String = ISO8601DateFormatter().string(from: Date())

    func ingest(ts: String, hr: Double?, rr: Double?, spo2: Double?, kcal: Double?) {
        latestTS = ts
        if let h = hr, h.isFinite {
            hrBuf.append(h)
            if hrBuf.count > 30 { hrBuf.removeFirst() }
        }
        // throttle ~3s
        if Date().timeIntervalSince(lastPost) < 3 { return }
        lastPost = Date()

        let hrAvg = hrBuf.isEmpty ? 0 : hrBuf.reduce(0,+) / Double(hrBuf.count)
        // toy math — you can later replace with your chosen logic
        let fatigue = min(100, max(0, (hrAvg - 60) * 1.2))
        let recovery = max(0, 100 - fatigue)
        let heat = 20.0, altitude = 10.0, sleep = 70.0
        let mrs = max(0, min(100, 100 - (0.5*fatigue + 0.3*(100-recovery) + 0.1*heat + 0.1*altitude)))
        let ori = (mrs < 60) ? "red" : (mrs < 75 ? "amber" : "green")

        Poster.shared.postDerived(ts: latestTS, mrs: mrs, ori: ori,
                                  fatigue: fatigue, recovery: recovery, heat: heat, altitude: altitude, sleep: sleep)
    }
}

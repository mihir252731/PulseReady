import Foundation
import HealthKit
import Combine

final class HeartStreamer: ObservableObject {
    static let shared = HeartStreamer()

    private let store = HKHealthStore()
    private var query: HKAnchoredObjectQuery?
    private let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
    @Published var latestBPM: Double = 0

    private init() {}

    // Ask for permission to read heart rate
    func requestAuthorization() async throws {
        try await store.requestAuthorization(toShare: [], read: [hrType])
    }

    // Start live streaming heart rate from Apple Watch via HealthKit
    func startStreaming() {
        // only allow while workout is active
        guard WorkoutManager.shared.isActive else { return }

        let oneHourAgo = Date().addingTimeInterval(-3600)
        let predicate = HKQuery.predicateForSamples(withStart: oneHourAgo, end: nil, options: .strictStartDate)

        query = HKAnchoredObjectQuery(type: hrType,
                                      predicate: predicate,
                                      anchor: nil,
                                      limit: HKObjectQueryNoLimit) { [weak self] _, samples, _, _, _ in
            self?.handle(samples: samples)
        }

        query?.updateHandler = { [weak self] _, samples, _, _, _ in
            self?.handle(samples: samples)
        }

        if let q = query { store.execute(q) }

        // stop automatically when workout stops
        NotificationCenter.default.addObserver(self, selector: #selector(stopIfWorkoutEnded),
                                               name: .WorkoutDidEnd, object: nil)
    }

    @objc private func stopIfWorkoutEnded() {
        if !WorkoutManager.shared.isActive {
            stopStreaming()
        }
    }

    private func handle(samples: [HKSample]?) {
        guard WorkoutManager.shared.isActive else { return } // hard gate
        guard let quantitySamples = samples as? [HKQuantitySample],
              let last = quantitySamples.last else { return }

        let bpmUnit = HKUnit.count().unitDivided(by: HKUnit.minute())
        let bpm = last.quantity.doubleValue(for: bpmUnit)
        let ts = ISO8601DateFormatter().string(from: last.startDate)

        DispatchQueue.main.async { self.latestBPM = bpm }

        // Only send raw when HR exists (backend requires hr)
        Poster.shared.postRaw(ts: ts, hr: bpm, rr: nil, spo2: nil, temp: nil)
        DerivedComputer.shared.ingest(ts: ts, hr: bpm, rr: nil, spo2: nil, kcal: nil)
    }

    func stopStreaming() {
        if let q = query { store.stop(q) }
        query = nil
        NotificationCenter.default.removeObserver(self, name: .WorkoutDidEnd, object: nil)
    }
}

extension Notification.Name {
    static let WorkoutDidEnd = Notification.Name("WorkoutDidEnd")
}

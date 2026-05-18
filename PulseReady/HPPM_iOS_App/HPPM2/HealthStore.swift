import HealthKit

final class HealthStore {
    static let shared = HealthStore()
    let store = HKHealthStore()
    var readTypes: Set<HKObjectType> {
        [
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .respiratoryRate)!,
            HKObjectType.quantityType(forIdentifier: .oxygenSaturation)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!,
            HKObjectType.quantityType(forIdentifier: .bodyTemperature)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.workoutType()
        ]
    }
    var shareTypes: Set<HKSampleType> { [HKObjectType.workoutType()] }

    func requestAuth() async throws {
        try await store.requestAuthorization(toShare: shareTypes, read: readTypes)
    }
}

import SwiftUI

struct ContentView: View {
    @ObservedObject private var heart = HeartStreamer.shared
    @State private var authorized = false
    @State private var isStreaming = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationView {
            VStack(spacing: 24) {
                Text("HPPM – Live Watch HR")
                    .font(.title2)

                Text("\(Int(heart.latestBPM)) bpm")
                    .font(.system(size: 48, weight: .bold))
                    .padding()

                if let msg = errorMessage {
                    Text(msg)
                        .foregroundColor(.red)
                        .font(.footnote)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                Button(buttonTitle) {
                    Task {
                        if !authorized {
                            do {
                                try await HeartStreamer.shared.requestAuthorization()
                                authorized = true
                                WatchIn.shared.activate()
                            } catch {
                                errorMessage = "HealthKit auth failed: \(error.localizedDescription)"
                            }
                        } else {
                            if isStreaming {
                                HeartStreamer.shared.stopStreaming()
                                isStreaming = false
                                // (Optional) post a notice or end workout in your WorkoutManager
                            } else {
                                // Ensure workout is started by your WorkoutManager elsewhere
                                if WorkoutManager.shared.isActive {
                                    HeartStreamer.shared.startStreaming()
                                    isStreaming = true
                                } else {
                                    errorMessage = "Start a workout to stream HR."
                                }
                            }
                        }
                    }
                }
                .buttonStyle(.borderedProminent)

                Text(WorkoutManager.shared.isActive ? "Workout Active" : "Workout Not Active")
                    .font(.footnote)
                    .foregroundColor(.secondary)

                Spacer()
            }
            .padding()
        }
        .onAppear {
            if authorized { WatchIn.shared.activate() }
        }
    }

    private var buttonTitle: String {
        if !authorized { return "Authorize HealthKit" }
        return isStreaming ? "Stop Streaming" : "Start Streaming"
    }
}

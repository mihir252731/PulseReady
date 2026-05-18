//
//  HPPM2App.swift
//  HPPM2
//
//  Created by Vrund Shah on 11/9/25.
//

import SwiftUI
import CoreData

@main
struct HPPM2App: App {
    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
        }
    }
}

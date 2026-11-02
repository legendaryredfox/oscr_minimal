// SPDX-License-Identifier: GPL-3.0-or-later
import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
    kotlin("jvm")
    kotlin("plugin.compose")
    id("org.jetbrains.compose")
}

dependencies {
    implementation(project(":shared"))
    implementation(compose.desktop.currentOs)
    implementation(compose.material3)
    implementation("com.fazecast:jSerialComm:2.11.4")   // porta serial em Linux, macOS e Windows
}

compose.desktop {
    application {
        mainClass = "oscr.MainKt"
        nativeDistributions {
            targetFormats(TargetFormat.Deb, TargetFormat.Dmg, TargetFormat.Msi)
            packageName = "oscr-dumper"
            packageVersion = "1.0.0"
        }
    }
}

// SPDX-License-Identifier: GPL-3.0-or-later
plugins {
    kotlin("jvm")
    application
}

dependencies {
    implementation(project(":shared"))
}

application {
    mainClass = "oscr.cli.MainKt"
    applicationDefaultJvmArgs = listOf("--enable-native-access=ALL-UNNAMED")   // jSerialComm: sem aviso em stderr
    applicationName = "dumper"          // ./gradlew :cliApp:installDist -> cliApp/build/install/dumper/bin/dumper
}

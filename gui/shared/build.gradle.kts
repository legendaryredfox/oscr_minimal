// SPDX-License-Identifier: GPL-3.0-or-later
plugins { kotlin("multiplatform") }

kotlin {
    jvm()
    sourceSets {
        commonTest.dependencies { implementation(kotlin("test")) }
        jvmMain {
            resources.srcDir("../../database")                    // base de jogos do projeto (database/oscr/*.txt) como recurso: oscr/INDEX.txt
        }
        jvmMain.dependencies {
            implementation("com.fazecast:jSerialComm:2.11.4")   // porta serial em Linux, macOS e Windows (GUI e CLI)
        }
    }
}

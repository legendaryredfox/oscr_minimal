// SPDX-License-Identifier: GPL-3.0-or-later
plugins { kotlin("multiplatform") }

kotlin {
    jvm()
    sourceSets {
        commonTest.dependencies { implementation(kotlin("test")) }
    }
}

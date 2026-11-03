// SPDX-License-Identifier: GPL-3.0-or-later
rootProject.name = "oscr-gui"
include(":shared")
include(":desktopApp")
include(":cliApp")

pluginManagement {
    repositories { gradlePluginPortal(); google(); mavenCentral() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}

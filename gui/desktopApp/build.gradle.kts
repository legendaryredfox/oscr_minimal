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

// H-7: o instalador leva as imagens do firmware (firmware/images, gerada por tools/build_images.py) e o avrdude. O avrdude não é baixado aqui:
// coloque o executável de cada sistema em gui/desktopApp/avrdude/<linux-x64|macos-arm64|macos-x64|windows-x64>/avrdude[.exe] (veja docs/referencia/empacotamento.md).
// Sem esses arquivos o instalador sai igual, e a gravação do firmware cai nos caminhos de sempre (PATH, PlatformIO).
val appResourcesDir = layout.buildDirectory.dir("appResources")
val bundleFirmwareAndAvrdude = tasks.register<Sync>("bundleFirmwareAndAvrdude") {
    into(appResourcesDir)
    from(rootProject.projectDir.parentFile.resolve("firmware/images")) { include("manifest.tsv", "*.hex"); into("common/firmware") }
    projectDir.resolve("avrdude").listFiles { f -> f.isDirectory }?.forEach { os -> from(os) { into("${os.name}/avrdude") } }
}
tasks.matching { it.name == "prepareAppResources" }.configureEach { dependsOn(bundleFirmwareAndAvrdude) }

compose.desktop {
    application {
        mainClass = "oscr.MainKt"
        nativeDistributions {
            appResourcesRootDir.set(project.layout.buildDirectory.dir("appResources"))
            targetFormats(TargetFormat.Deb, TargetFormat.Dmg, TargetFormat.Msi)
            packageName = "oscr-dumper"
            packageVersion = "1.0.0"
        }
    }
}

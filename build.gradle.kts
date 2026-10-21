// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.compose.compiler) apply false
}

// dist<BuildType>: copies the installable APKs into build/dist/<buildType>/:
//   SloppyShock-App-<version>.apk               the watch app, all faces bundled (Wear OS 6+)
//   SloppyShock-Face-<Layout>-<version>.apk     each face on its own (any Wear OS 5+ watch)
val distVersion = (findProperty("versionName") as String?) ?: "dev"
val faceLayouts = listOf("compact", "detailed", "dual")
fun cap(s: String) = s.replaceFirstChar(Char::uppercase)

listOf("debug", "release").forEach { type ->
    tasks.register<Copy>("dist${cap(type)}") {
        group = "distribution"
        description = "Collects the $type app and face APKs into build/dist/$type."
        dependsOn(":app:assemble${cap(type)}")
        dependsOn(faceLayouts.map { ":watchface:assemble${cap(it)}${cap(type)}" })
        val version = distVersion
        from(file("app/build/outputs/apk/$type/app-$type.apk")) {
            rename { "SloppyShock-App-$version.apk" }
        }
        faceLayouts.forEach { face ->
            val name = "SloppyShock-Face-${cap(face)}-$version.apk"
            from(file("watchface/build/outputs/apk/$face/$type/watchface-$face-$type.apk")) {
                rename { name }
            }
        }
        into(layout.buildDirectory.dir("dist/$type"))
    }
}

// SloppyShock watch app: carries the three watch faces and installs them with
// Watch Face Push (Wear OS 6+). Faces come from :watchface, validated at build
// time (see ValidateWatchFaceTask there).
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.compose.compiler)
}

// Release signing comes from the environment (set by CI from repository
// secrets); without it release APKs are left unsigned.
val signingKeystore: String? = System.getenv("SIGNING_KEYSTORE")

android {
    namespace = "dev.stackon.sloppyshock"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "dev.stackon.sloppyshock"
        minSdk = 36 // Watch Face Push needs Wear OS 6
        targetSdk = 37
        versionCode = (findProperty("versionCode") as String?)?.toInt() ?: 1
        versionName = (findProperty("versionName") as String?) ?: "1.0"
    }

    signingConfigs {
        if (signingKeystore != null) {
            create("release") {
                storeFile = file(signingKeystore)
                storePassword = System.getenv("SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            if (signingKeystore != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation(libs.watchface.push)
    implementation(libs.wear.compose.material3)
    implementation(libs.wear.compose.foundation)
    implementation(libs.activity.compose)
    implementation(libs.lifecycle.runtime.compose)
}

// Faces bundled into the app. The first one is also the default face that
// Wear OS installs together with the app (asset default_watchface.apk, token in
// the DEFAULT_WATCHFACE_VALIDATION_TOKEN manifest meta-data).
val bundledFaces = listOf("compact", "detailed", "dual")
val defaultFace = bundledFaces.first()
fun cap(s: String) = s.replaceFirstChar(Char::uppercase)
fun assetName(face: String) = if (face == defaultFace) "default_watchface" else face

/** Writes the default face's validation token as a string resource. */
abstract class DefaultFaceTokenTask : DefaultTask() {
    @get:InputFile @get:PathSensitive(PathSensitivity.NONE) abstract val tokenFile: RegularFileProperty
    @get:OutputDirectory abstract val outputDir: DirectoryProperty

    @TaskAction
    fun write() {
        val values = outputDir.get().asFile.resolve("values").apply { mkdirs() }
        values.resolve("default_watchface_token.xml").writeText(
            """
            |<resources>
            |    <string name="default_wf_token" translatable="false">${tokenFile.get().asFile.readText().trim()}</string>
            |</resources>
            |""".trimMargin()
        )
    }
}

androidComponents.onVariants { variant ->
    val buildType = variant.buildType!!
    val facesDir = rootProject.layout.projectDirectory.dir("watchface/build/watchfacepush")
    val assetsDir = layout.buildDirectory.dir("generated/watchfaces/${variant.name}/assets")
    val resDir = layout.buildDirectory.dir("generated/watchfaces/${variant.name}/res")

    val collect = tasks.register<Sync>("collectWatchFaces${cap(variant.name)}") {
        bundledFaces.forEach { face ->
            dependsOn(":watchface:validate${cap(face)}${cap(buildType)}")
            val target = assetName(face) // plain String: the lambda must not reference the script
            from(facesDir.dir("$face${cap(buildType)}")) {
                rename { it.replace(face, target) }
            }
        }
        into(assetsDir)
    }
    val token = tasks.register<DefaultFaceTokenTask>("defaultFaceToken${cap(variant.name)}") {
        dependsOn(collect)
        tokenFile.set(assetsDir.map { it.file("default_watchface_token.txt") })
        outputDir.set(resDir)
    }

    variant.sources.assets?.addStaticSourceDirectory(assetsDir.get().asFile.absolutePath)
    variant.sources.res?.addStaticSourceDirectory(resDir.get().asFile.absolutePath)
    afterEvaluate {
        tasks.named("pre${cap(variant.name)}Build") { dependsOn(collect, token) }
    }
}

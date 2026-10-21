package dev.stackon.sloppyshock

import android.content.Context
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.wear.watchfacepush.WatchFacePushManager
import androidx.wear.watchfacepush.WatchFacePushManager.SetWatchFaceAsActiveException
import androidx.wear.watchfacepush.WatchFacePushManagerFactory
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** A watch face APK shipped in this app's assets, with its validation token. */
class BundledFace(
    val apk: File,
    val packageName: String,
    val label: String,
    val versionCode: Long,
    val preview: ImageBitmap?,
    val token: String,
)

/** State of a bundled face on the watch. */
data class FaceState(
    val face: BundledFace,
    val slotId: String?,
    val installedVersion: Long?,
    val active: Boolean,
) {
    val installed get() = slotId != null
    val updateAvailable get() = installedVersion != null && installedVersion < face.versionCode
}

data class Overview(val faces: List<FaceState>, val remainingSlots: Int)

/** Outcome of [Faces.use]; [message] is shown to the user. */
data class UseResult(val message: String)

private const val TAG = "SloppyShock"

class Faces(private val context: Context) {
    private val push: WatchFacePushManager =
        WatchFacePushManagerFactory.createWatchFacePushManager(context)

    private var bundled: List<BundledFace>? = null
    private val loading = Mutex()

    /**
     * Faces in the assets (default face first). APKs are copied to the cache
     * once; the lock keeps concurrent callers from reading a half-copied APK.
     */
    suspend fun bundled(): List<BundledFace> = loading.withLock {
        bundled ?: withContext(Dispatchers.IO) {
            val assets = context.assets.list("").orEmpty().filter { it.endsWith(".apk") }
            assets.sortedBy { if (it == "default_watchface.apk") "" else it }
                .mapNotNull { loadBundled(it) }
        }.also { bundled = it }
    }

    private fun loadBundled(asset: String): BundledFace? {
        val apk = File(context.cacheDir, asset)
        context.assets.open(asset).use { input -> apk.outputStream().use { input.copyTo(it) } }
        val pm = context.packageManager
        val info = pm.getPackageArchiveInfo(apk.path, PackageManager.PackageInfoFlags.of(0))
            ?: return null
        val appInfo = info.applicationInfo!!.apply {
            sourceDir = apk.path
            publicSourceDir = apk.path
        }
        val res = pm.getResourcesForApplication(appInfo)
        val previewId = res.getIdentifier("preview", "drawable", info.packageName)
        val preview = if (previewId != 0) {
            res.openRawResource(previewId).use { BitmapFactory.decodeStream(it) }?.asImageBitmap()
        } else {
            null
        }
        val token = context.assets.open(asset.removeSuffix(".apk") + "_token.txt")
            .use { it.readBytes().decodeToString().trim() }
        return BundledFace(
            apk = apk,
            packageName = info.packageName,
            label = pm.getApplicationLabel(appInfo).toString(),
            versionCode = info.longVersionCode,
            preview = preview,
            token = token,
        )
    }

    suspend fun overview(): Overview {
        val response = push.listWatchFaces()
        val bySlot = response.installedWatchFaceDetails.associateBy { it.packageName }
        val states = bundled().map { face ->
            val installed = bySlot[face.packageName]
            FaceState(
                face = face,
                slotId = installed?.slotId,
                installedVersion = installed?.versionCode,
                active = installed != null && push.isWatchFaceActive(face.packageName),
            )
        }
        Log.i(TAG, "free slots: ${response.remainingSlotCount}; " + states.joinToString { s ->
            "${s.face.packageName.substringAfterLast('.')}=" +
                (if (s.installed) "v${s.installedVersion}/${if (s.active) "active" else "installed"}" else "absent")
        })
        return Overview(states, response.remainingSlotCount)
    }

    /**
     * Makes [face] the active watch face: installs it (or updates an outdated
     * copy) and activates it. With no free slot, the face replaces the one this
     * app installed before.
     */
    suspend fun use(face: BundledFace, canActivate: Boolean): UseResult {
        val current = overview()
        val state = current.faces.first { it.face.packageName == face.packageName }
        val slotId = when {
            state.installed && !state.updateAvailable -> state.slotId!!
            state.installed -> fd(face) { push.updateWatchFace(state.slotId!!, it, face.token) }.slotId
            current.remainingSlots > 0 -> fd(face) { push.addWatchFace(it, face.token) }.slotId
            else -> {
                // No free slot: replace one of ours, preferring a face that isn't active.
                val replaced = current.faces.filter { it.installed }
                    .minByOrNull { if (it.active) 1 else 0 }
                    ?: return UseResult("No free watch face slot. Remove a face installed by another app.")
                fd(face) { push.updateWatchFace(replaced.slotId!!, it, face.token) }.slotId
            }
        }
        if (push.isWatchFaceActive(face.packageName)) {
            // Updated in place or already active: activating again would only
            // use up one of the limited setWatchFaceAsActive attempts.
            return UseResult("${face.label} is your watch face.")
        }
        if (!canActivate) {
            return UseResult("${face.label} installed. Select it in the watch face list.")
        }
        return try {
            push.setWatchFaceAsActive(slotId)
            UseResult("${face.label} is now your watch face.")
        } catch (e: SetWatchFaceAsActiveException) {
            Log.w(TAG, "setWatchFaceAsActive failed: errorCode=${e.errorCode}", e)
            val why = if (e.errorCode == SetWatchFaceAsActiveException.ERROR_MAXIMUM_ATTEMPTS_REACHED) {
                "Wear OS limits how often an app may switch the watch face. "
            } else {
                ""
            }
            UseResult("${face.label} installed. ${why}Select it in the watch face list.")
        }
    }

    suspend fun remove(state: FaceState) {
        push.removeWatchFace(state.slotId!!)
    }

    private suspend fun <T> fd(face: BundledFace, block: suspend (ParcelFileDescriptor) -> T): T =
        ParcelFileDescriptor.open(face.apk, ParcelFileDescriptor.MODE_READ_ONLY).use { block(it) }
}

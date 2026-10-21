package dev.stackon.sloppyshock

import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import androidx.wear.compose.foundation.lazy.TransformingLazyColumn
import androidx.wear.compose.foundation.lazy.rememberTransformingLazyColumnState
import androidx.wear.compose.material3.AppScaffold
import androidx.wear.compose.material3.Button
import androidx.wear.compose.material3.ButtonDefaults
import androidx.wear.compose.material3.Card
import androidx.wear.compose.material3.CircularProgressIndicator
import androidx.wear.compose.material3.ListHeader
import androidx.wear.compose.material3.MaterialTheme
import androidx.wear.compose.material3.OutlinedButton
import androidx.wear.compose.material3.ScreenScaffold
import androidx.wear.compose.material3.Text
import kotlinx.coroutines.launch

private const val SET_ACTIVE_PERMISSION =
    "com.google.wear.permission.SET_PUSHED_WATCH_FACE_AS_ACTIVE"

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        faces = Faces(applicationContext)
        setContent { MaterialTheme { AppScaffold { FaceList(faces) } } }
        handleTestIntent(intent)
    }

    private lateinit var faces: Faces

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleTestIntent(intent)
    }

    /**
     * Debug builds only: `am start -n dev.stackon.sloppyshock/.MainActivity
     * --es use <compact|detailed|dual>` (or `--es remove <face>`) runs the same
     * code as the buttons and logs the result, for scripted tests over adb.
     */
    private fun handleTestIntent(intent: Intent) {
        if (applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE == 0) return
        val use = intent.getStringExtra("use")
        val remove = intent.getStringExtra("remove")
        if (use == null && remove == null) return
        lifecycleScope.launch {
            val result = runCatching {
                val states = faces.overview().faces
                fun find(name: String) = states.first { it.face.packageName.endsWith(".$name") }
                if (use != null) {
                    val canActivate = ContextCompat.checkSelfPermission(this@MainActivity, SET_ACTIVE_PERMISSION) ==
                        PackageManager.PERMISSION_GRANTED
                    faces.use(find(use).face, canActivate).message
                } else {
                    faces.remove(find(remove!!))
                    "removed $remove"
                }
            }.getOrElse { "FAILED: $it" }
            Log.i("SloppyShock", "test: $result")
            faces.overview()
        }
    }
}

@Composable
private fun FaceList(faces: Faces) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val scope = rememberCoroutineScope()
    var overview by remember { mutableStateOf<Overview?>(null) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var pending by remember { mutableStateOf<BundledFace?>(null) }

    fun refresh() = scope.launch {
        overview = runCatching { faces.overview() }
            .onFailure { message = "Watch Face Push unavailable: ${it.message}" }
            .getOrNull()
    }

    fun run(action: suspend () -> String?) = scope.launch {
        busy = true
        message = runCatching { action() }.getOrElse { "Failed: ${it.message}" }
        overview = runCatching { faces.overview() }.getOrNull() ?: overview
        busy = false
    }

    val permissionLauncher =
        rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            pending?.let { face -> run { faces.use(face, canActivate = granted).message } }
            pending = null
        }

    fun use(face: BundledFace) {
        val granted = ContextCompat.checkSelfPermission(context, SET_ACTIVE_PERMISSION) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) {
            run { faces.use(face, canActivate = true).message }
        } else {
            pending = face
            permissionLauncher.launch(SET_ACTIVE_PERMISSION)
        }
    }

    LaunchedEffect(Unit) { refresh() }

    val listState = rememberTransformingLazyColumnState()
    ScreenScaffold(scrollState = listState) { contentPadding ->
        TransformingLazyColumn(state = listState, contentPadding = contentPadding) {
            item { ListHeader { Text("SloppyShock") } }
            message?.let { text ->
                item {
                    Text(
                        text,
                        style = MaterialTheme.typography.bodySmall,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp),
                    )
                }
            }
            val current = overview
            if (current == null) {
                item { CircularProgressIndicator() }
            } else {
                current.faces.forEach { state ->
                    item {
                        FaceCard(
                            state = state,
                            busy = busy,
                            onUse = { use(state.face) },
                            onRemove = { run { faces.remove(state); "${state.face.label} removed." } },
                        )
                    }
                }
                item {
                    Text(
                        "Free slots: ${current.remainingSlots}",
                        style = MaterialTheme.typography.labelSmall,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun FaceCard(state: FaceState, busy: Boolean, onUse: () -> Unit, onRemove: () -> Unit) {
    val status = when {
        state.active && !state.updateAvailable -> "Active"
        state.updateAvailable -> "Update available"
        state.installed -> "Installed"
        else -> "Not installed"
    }
    Card(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.fillMaxWidth(),
        ) {
            state.face.preview?.let {
                Image(
                    bitmap = it,
                    contentDescription = state.face.label,
                    modifier = Modifier.size(96.dp).clip(CircleShape),
                )
            }
            Text(state.face.label, style = MaterialTheme.typography.titleSmall)
            Text(status, style = MaterialTheme.typography.labelSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.padding(top = 4.dp)) {
                Button(
                    onClick = onUse,
                    enabled = !busy && !(state.active && !state.updateAvailable),
                    contentPadding = ButtonDefaults.CompactButtonContentPadding,
                ) { Text(if (state.updateAvailable) "Update" else "Use") }
                if (state.installed) {
                    OutlinedButton(
                        onClick = onRemove,
                        enabled = !busy,
                        contentPadding = ButtonDefaults.CompactButtonContentPadding,
                    ) { Text("Remove") }
                }
            }
        }
    }
}

package com.gautamnc.smartblindstick

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.net.http.SslError
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.webkit.ConsoleMessage
import android.webkit.GeolocationPermissions
import android.webkit.PermissionRequest
import android.webkit.SslErrorHandler
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.gautamnc.smartblindstick.bridge.AndroidHardwareBridge
import com.gautamnc.smartblindstick.data.AppPreferences
import com.gautamnc.smartblindstick.hardware.BluetoothStickManager
import com.gautamnc.smartblindstick.hardware.WifiStickManager
import com.gautamnc.smartblindstick.ui.HardwareBottomSheet
import com.gautamnc.smartblindstick.ui.ServerUrlDialog
import org.json.JSONObject

class MainActivity : AppCompatActivity(), BluetoothStickManager.Listener {

    private lateinit var prefs: AppPreferences
    private lateinit var btManager: BluetoothStickManager
    private lateinit var wifiManager: WifiStickManager
    private var hardwareSheet: HardwareBottomSheet? = null

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var layoutLoading: LinearLayout
    private lateinit var layoutError: View
    private lateinit var tvLoadingUrl: TextView
    private lateinit var tvErrorTargetUrl: TextView
    private lateinit var tvHardwareStatus: TextView
    private lateinit var dotHardwareStatus: View

    private var hasLoadedSuccessfully = false
    private var backPressedTime: Long = 0

    // Permissions launcher
    private val requestPermissionsLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions.entries.all { it.value }
        if (!granted) {
            Log.w(TAG, "Some runtime permissions were not granted: $permissions")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = AppPreferences(this)
        btManager = BluetoothStickManager(this)
        btManager.setListener(this)
        wifiManager = WifiStickManager()

        initViews()
        setupWebView()
        setupHardwareControls()
        checkAndRequestPermissions()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    if (System.currentTimeMillis() - backPressedTime < 2000) {
                        finish()
                    } else {
                        backPressedTime = System.currentTimeMillis()
                        Toast.makeText(this@MainActivity, "Press back again to exit", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })

        loadBackendApp(prefs.serverUrl)
    }

    private fun initViews() {
        webView = findViewById(R.id.web_view)
        swipeRefresh = findViewById(R.id.swipe_refresh)
        layoutLoading = findViewById(R.id.layout_loading)
        layoutError = findViewById(R.id.layout_error)
        tvLoadingUrl = findViewById(R.id.tv_loading_url)
        tvErrorTargetUrl = findViewById(R.id.tv_error_target_url)
        tvHardwareStatus = findViewById(R.id.tv_hardware_status)
        dotHardwareStatus = findViewById(R.id.dot_hardware_status)

        val pillHardware = findViewById<LinearLayout>(R.id.pill_hardware_status)
        val btnHardware = findViewById<ImageButton>(R.id.btn_hardware)
        val btnSettings = findViewById<ImageButton>(R.id.btn_settings)

        val btnRetry = findViewById<Button>(R.id.btn_retry_connection)
        val btnChangeUrl = findViewById<Button>(R.id.btn_change_url)
        val btnOpenHw = findViewById<Button>(R.id.btn_open_hardware)

        pillHardware.setOnClickListener { openHardwareSheet() }
        btnHardware.setOnClickListener { openHardwareSheet() }
        btnSettings.setOnClickListener { openServerUrlDialog() }

        btnRetry.setOnClickListener {
            showLoading(prefs.serverUrl)
            webView.reload()
        }

        btnChangeUrl.setOnClickListener { openServerUrlDialog() }
        btnOpenHw.setOnClickListener { openHardwareSheet() }

        swipeRefresh.setColorSchemeColors(ContextCompat.getColor(this, R.color.brand_primary))
        swipeRefresh.setOnRefreshListener {
            webView.reload()
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings = webView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.databaseEnabled = true
        settings.allowFileAccess = false
        settings.allowContentAccess = true
        settings.mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
        settings.setSupportZoom(false)
        settings.builtInZoomControls = false
        settings.displayZoomControls = false
        settings.useWideViewPort = true
        settings.loadWithOverviewMode = true
        settings.cacheMode = WebSettings.LOAD_DEFAULT

        val baseAgent = settings.userAgentString
        settings.userAgentString = "$baseAgent SmartBlindStickApp/1.0.0 (Android Native Companion)"

        // Inject Native JavaScript Bridge
        val bridge = AndroidHardwareBridge(
            context = this,
            prefs = prefs,
            btManager = btManager,
            onOpenHardwareSettings = { openHardwareSheet() },
            onOpenServerSettings = { openServerUrlDialog() },
            onReloadRequested = { newUrl -> loadBackendApp(newUrl) }
        )
        webView.addJavascriptInterface(bridge, "AndroidHardwareBridge")

        webView.webChromeClient = object : WebChromeClient() {
            override fun onGeolocationPermissionsShowPrompt(
                origin: String?,
                callback: GeolocationPermissions.Callback?
            ) {
                callback?.invoke(origin, true, false)
            }

            override fun onPermissionRequest(request: PermissionRequest?) {
                request?.grant(request.resources)
            }

            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                Log.d(TAG, "[WebView Console] ${consoleMessage?.message()} -- line ${consoleMessage?.lineNumber()}")
                return true
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                if (!hasLoadedSuccessfully) {
                    showLoading(url ?: prefs.serverUrl)
                }
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                swipeRefresh.isRefreshing = false
                showContent()
                hasLoadedSuccessfully = true

                // Inject hardware telemetry callback hook and styles into page
                val initJs = """
                    (function() {
                        window.isAndroidNativeApp = true;
                        if (!window.onHardwareTelemetry) {
                            window.onHardwareTelemetry = function(data) {
                                console.log('[Native HW Stream]', data);
                            };
                        }
                    })();
                """.trimIndent()
                view?.evaluateJavascript(initJs, null)
            }

            override fun onReceivedError(
                view: WebView?,
                request: WebResourceRequest?,
                error: WebResourceError?
            ) {
                super.onReceivedError(view, request, error)
                if (request?.isForMainFrame == true) {
                    showError(request.url.toString())
                }
            }

            override fun onReceivedHttpError(
                view: WebView?,
                request: WebResourceRequest?,
                errorResponse: WebResourceResponse?
            ) {
                super.onReceivedHttpError(view, request, errorResponse)
                if (request?.isForMainFrame == true && (errorResponse?.statusCode ?: 200) >= 400) {
                    showError(request.url.toString())
                }
            }

            override fun onReceivedSslError(
                view: WebView?,
                handler: SslErrorHandler?,
                error: SslError?
            ) {
                // Strict TLS validation - do not bypass SSL certificate verification
                super.onReceivedSslError(view, handler, error)
                Log.e(TAG, "SSL Certificate Error on ${error?.url}: $error")
            }
        }
    }

    private fun loadBackendApp(url: String) {
        showLoading(url)
        tvErrorTargetUrl.text = url
        webView.loadUrl(url)
    }

    private fun showLoading(url: String) {
        layoutLoading.visibility = View.VISIBLE
        layoutError.visibility = View.GONE
        tvLoadingUrl.text = url
    }

    private fun showContent() {
        layoutLoading.visibility = View.GONE
        layoutError.visibility = View.GONE
        webView.visibility = View.VISIBLE
    }

    private fun showError(url: String) {
        hasLoadedSuccessfully = false
        layoutLoading.visibility = View.GONE
        layoutError.visibility = View.VISIBLE
        tvErrorTargetUrl.text = url
        swipeRefresh.isRefreshing = false
    }

    private fun setupHardwareControls() {
        updateHardwareStatusBadge(btManager.currentState, null)
    }

    private fun openHardwareSheet() {
        if (hardwareSheet == null) {
            hardwareSheet = HardwareBottomSheet(this, btManager, wifiManager)
        }
        hardwareSheet?.show { selectedDevice ->
            btManager.connect(selectedDevice)
        }
    }

    private fun openServerUrlDialog() {
        ServerUrlDialog.show(this, prefs) { newUrl ->
            loadBackendApp(newUrl)
        }
    }

    private fun updateHardwareStatusBadge(state: BluetoothStickManager.State, deviceName: String?) {
        when (state) {
            BluetoothStickManager.State.CONNECTED -> {
                tvHardwareStatus.text = "BT: ${deviceName ?: "Stick"}"
                dotHardwareStatus.backgroundTintList =
                    ContextCompat.getColorStateList(this, R.color.status_success)
            }
            BluetoothStickManager.State.CONNECTING -> {
                tvHardwareStatus.text = "Connecting…"
                dotHardwareStatus.backgroundTintList =
                    ContextCompat.getColorStateList(this, R.color.status_warning)
            }
            BluetoothStickManager.State.DISCONNECTED -> {
                tvHardwareStatus.text = "Awaiting HW"
                dotHardwareStatus.backgroundTintList =
                    ContextCompat.getColorStateList(this, R.color.status_offline)
            }
        }
    }

    // BluetoothStickManager.Listener implementation
    override fun onStateChanged(state: BluetoothStickManager.State, deviceName: String?, message: String) {
        updateHardwareStatusBadge(state, deviceName)
        Log.i(TAG, "HW State: $state, $deviceName, $message")
        hardwareSheet?.let {
            // Can update UI if open
        }
    }

    override fun onDeviceDiscovered(device: BluetoothDevice) {
        hardwareSheet?.addDiscoveredDevice(device)
    }

    override fun onTelemetryData(rawLine: String) {
        // Forward raw telemetry directly into web application
        val quoted = JSONObject.quote(rawLine)
        webView.evaluateJavascript("if (window.onHardwareTelemetry) { window.onHardwareTelemetry($quoted); }", null)
    }

    override fun onLog(message: String) {
        Log.d(TAG, "[HW Log] $message")
    }

    private fun checkAndRequestPermissions() {
        val permissions = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.BLUETOOTH_SCAN)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
            }
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.RECORD_AUDIO)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            permissions.add(Manifest.permission.CAMERA)
        }

        if (permissions.isNotEmpty()) {
            requestPermissionsLauncher.launch(permissions.toTypedArray())
        }
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onDestroy() {
        super.onDestroy()
        btManager.onDestroy()
        webView.destroy()
    }

    override fun dispatchKeyEvent(event: android.view.KeyEvent): Boolean {
        // Accessibility directive: do not hijack keystrokes while the user is editing a text input
        val focused = currentFocus
        if (focused is android.widget.EditText) {
            return super.dispatchKeyEvent(event)
        }

        if (event.action == android.view.KeyEvent.ACTION_DOWN) {
            when (event.keyCode) {
                android.view.KeyEvent.KEYCODE_H -> {
                    webView.evaluateJavascript("if (window.switchTab) { window.switchTab('home'); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_C -> {
                    openHardwareSheet()
                    return true
                }
                android.view.KeyEvent.KEYCODE_N -> {
                    webView.evaluateJavascript("if (window.switchTab) { window.switchTab('location'); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_S -> {
                    webView.evaluateJavascript("if (window.switchTab) { window.switchTab('settings'); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_SLASH -> {
                    if (event.isShiftPressed) { // '?' key
                        webView.evaluateJavascript("if (window.openKeyboardGuide) { window.openKeyboardGuide(); }", null)
                        return true
                    }
                }
                android.view.KeyEvent.KEYCODE_F1 -> {
                    webView.evaluateJavascript("if (window.openKeyboardGuide) { window.openKeyboardGuide(); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_ESCAPE -> {
                    webView.evaluateJavascript("if (window.closeActiveModal) { window.closeActiveModal(); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_DPAD_UP -> {
                    webView.evaluateJavascript("if (window.navigateControl) { window.navigateControl(-1); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_DPAD_DOWN -> {
                    webView.evaluateJavascript("if (window.navigateControl) { window.navigateControl(1); }", null)
                    return true
                }
                android.view.KeyEvent.KEYCODE_ENTER,
                android.view.KeyEvent.KEYCODE_NUMPAD_ENTER,
                android.view.KeyEvent.KEYCODE_DPAD_CENTER -> {
                    webView.evaluateJavascript("if (window.activateCurrentControl) { window.activateCurrentControl(); }", null)
                    return true
                }
            }
        }
        return super.dispatchKeyEvent(event)
    }

    companion object {
        private const val TAG = "SmartStickMain"
    }
}
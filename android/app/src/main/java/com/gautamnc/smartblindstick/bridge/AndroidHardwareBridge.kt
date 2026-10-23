package com.gautamnc.smartblindstick.bridge

import android.content.Context
import android.os.Build
import android.os.CombinedVibration
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.webkit.JavascriptInterface
import com.gautamnc.smartblindstick.data.AppPreferences
import com.gautamnc.smartblindstick.hardware.BluetoothStickManager

class AndroidHardwareBridge(
    private val context: Context,
    private val prefs: AppPreferences,
    private val btManager: BluetoothStickManager,
    private val onOpenHardwareSettings: () -> Unit,
    private val onOpenServerSettings: () -> Unit,
    private val onReloadRequested: (String) -> Unit
) {
    private val mainHandler = Handler(Looper.getMainLooper())

    @JavascriptInterface
    fun isHardwareConnected(): Boolean {
        return btManager.currentState == BluetoothStickManager.State.CONNECTED
    }

    @JavascriptInterface
    fun getHardwareType(): String {
        return when (btManager.currentState) {
            BluetoothStickManager.State.CONNECTED -> "BLUETOOTH"
            BluetoothStickManager.State.CONNECTING -> "CONNECTING"
            else -> "DISCONNECTED"
        }
    }

    @JavascriptInterface
    fun getConnectedDeviceName(): String {
        return btManager.connectedDeviceName ?: ""
    }

    @JavascriptInterface
    fun getConnectedDeviceAddress(): String {
        return btManager.connectedDeviceAddress ?: ""
    }

    @JavascriptInterface
    fun openHardwareSettings() {
        mainHandler.post {
            onOpenHardwareSettings()
        }
    }

    @JavascriptInterface
    fun openServerSettings() {
        mainHandler.post {
            onOpenServerSettings()
        }
    }

    @JavascriptInterface
    fun triggerHaptic(durationMs: Long) {
        val safeDuration = durationMs.coerceIn(50, 2000)
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vm?.defaultVibrator?.vibrate(VibrationEffect.createOneShot(safeDuration, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                @Suppress("DEPRECATION")
                v?.vibrate(safeDuration)
            }
        } catch (e: Exception) {
            // Ignore
        }

        // Also if Bluetooth stick is connected, pass haptic pulse command to the physical motor
        if (btManager.currentState == BluetoothStickManager.State.CONNECTED) {
            btManager.sendCommand("VIBRATE:$safeDuration")
        }
    }

    @JavascriptInterface
    fun sendHardwareCommand(command: String): Boolean {
        return if (btManager.currentState == BluetoothStickManager.State.CONNECTED) {
            btManager.sendCommand(command)
        } else {
            false
        }
    }

    @JavascriptInterface
    fun getBackendUrl(): String {
        return prefs.serverUrl
    }

    @JavascriptInterface
    fun setBackendUrl(url: String) {
        val trimmed = url.trim()
        if (trimmed.isNotBlank()) {
            prefs.serverUrl = trimmed
            mainHandler.post {
                onReloadRequested(trimmed)
            }
        }
    }

    @JavascriptInterface
    fun getDeviceId(): String {
        return prefs.deviceId
    }

    @JavascriptInterface
    fun getAppVersion(): String {
        return "1.0.0-android"
    }

    @JavascriptInterface
    fun getUsbStatus(): String {
        return try {
            val usbManager = context.getSystemService(Context.USB_SERVICE) as? android.hardware.usb.UsbManager
            val devices = usbManager?.deviceList ?: emptyMap()
            if (devices.isEmpty()) {
                "DISCONNECTED"
            } else {
                val first = devices.values.first()
                "CONNECTED:${first.deviceName} (Vendor:0x${Integer.toHexString(first.vendorId)})"
            }
        } catch (e: Exception) {
            "UNSUPPORTED"
        }
    }

    @JavascriptInterface
    fun openSystemBluetoothSettings() {
        mainHandler.post {
            try {
                val intent = android.content.Intent(android.provider.Settings.ACTION_BLUETOOTH_SETTINGS).apply {
                    flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(intent)
            } catch (e: Exception) {
                // Ignore
            }
        }
    }

    @JavascriptInterface
    fun openKeyboardSettings() {
        mainHandler.post {
            try {
                // Open system physical keyboard / input method settings
                val intent = android.content.Intent(android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS).apply {
                    flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(intent)
            } catch (e: Exception) {
                // Ignore
            }
        }
    }
}
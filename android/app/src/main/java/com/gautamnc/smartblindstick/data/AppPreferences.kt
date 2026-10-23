package com.gautamnc.smartblindstick.data

import android.content.Context
import android.content.SharedPreferences
import com.gautamnc.smartblindstick.BuildConfig

class AppPreferences(context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var serverUrl: String
        get() = prefs.getString(KEY_SERVER_URL, defaultServerUrl) ?: defaultServerUrl
        set(value) = prefs.edit().putString(KEY_SERVER_URL, value.trim()).apply()

    var deviceId: String
        get() = prefs.getString(KEY_DEVICE_ID, DEFAULT_DEVICE_ID) ?: DEFAULT_DEVICE_ID
        set(value) = prefs.edit().putString(KEY_DEVICE_ID, value.trim()).apply()

    var lastBluetoothAddress: String?
        get() = prefs.getString(KEY_LAST_BT_ADDR, null)
        set(value) = prefs.edit().putString(KEY_LAST_BT_ADDR, value).apply()

    var lastWifiStickIp: String
        get() = prefs.getString(KEY_WIFI_STICK_IP, DEFAULT_STICK_IP) ?: DEFAULT_STICK_IP
        set(value) = prefs.edit().putString(KEY_WIFI_STICK_IP, value.trim()).apply()

    val defaultServerUrl: String
        get() = try {
            BuildConfig.DEFAULT_BACKEND_URL
        } catch (e: Throwable) {
            "https://smart-blind-stick-chzz.onrender.com/app"
        }

    companion object {
        private const val PREFS_NAME = "smart_blind_stick_prefs"
        private const val KEY_SERVER_URL = "server_url"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_LAST_BT_ADDR = "last_bt_addr"
        private const val KEY_WIFI_STICK_IP = "wifi_stick_ip"

        const val DEFAULT_DEVICE_ID = "STICK_001"
        const val DEFAULT_STICK_IP = "192.168.4.1"
    }
}
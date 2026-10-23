package com.gautamnc.smartblindstick.hardware

import android.os.Handler
import android.os.Looper
import android.util.Log
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import kotlin.concurrent.thread

class WifiStickManager {

    interface Callback {
        fun onResult(isReachable: Boolean, responseCode: Int, responseBody: String)
    }

    private val mainHandler = Handler(Looper.getMainLooper())

    fun pingStick(ipOrHost: String, callback: Callback) {
        val target = if (ipOrHost.startsWith("http://") || ipOrHost.startsWith("https://")) {
            ipOrHost.trimEnd('/')
        } else {
            "http://${ipOrHost.trimEnd('/')}"
        }

        thread {
            var conn: HttpURLConnection? = null
            try {
                // Try health/status endpoint on the stick
                val testUrl = "$target/status"
                val url = URL(testUrl)
                conn = url.openConnection() as HttpURLConnection
                conn.connectTimeout = 2500
                conn.readTimeout = 2500
                conn.requestMethod = "GET"

                val code = conn.responseCode
                val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                val body = stream?.bufferedReader()?.use { it.readText() } ?: ""

                mainHandler.post {
                    callback.onResult(true, code, body)
                }
            } catch (e: Exception) {
                // Fallback attempt to root
                var fallbackConn: HttpURLConnection? = null
                try {
                    val rootUrl = URL(target)
                    fallbackConn = rootUrl.openConnection() as HttpURLConnection
                    fallbackConn.connectTimeout = 2500
                    fallbackConn.readTimeout = 2500
                    fallbackConn.requestMethod = "GET"
                    val code = fallbackConn.responseCode
                    val stream = if (code in 200..299) fallbackConn.inputStream else fallbackConn.errorStream
                    val body = stream?.bufferedReader()?.use { it.readText() } ?: ""
                    mainHandler.post {
                        callback.onResult(true, code, body)
                    }
                } catch (e2: Exception) {
                    Log.w("WifiStickManager", "Ping to $target failed: ${e2.message}")
                    mainHandler.post {
                        callback.onResult(false, -1, e2.message ?: "Unreachable")
                    }
                } finally {
                    fallbackConn?.disconnect()
                }
            } finally {
                conn?.disconnect()
            }
        }
    }

    fun sendCommand(ipOrHost: String, command: String, callback: Callback) {
        val target = if (ipOrHost.startsWith("http://") || ipOrHost.startsWith("https://")) {
            ipOrHost.trimEnd('/')
        } else {
            "http://${ipOrHost.trimEnd('/')}"
        }
        val encodedCmd = try {
            URLEncoder.encode(command, "UTF-8")
        } catch (e: Exception) {
            command
        }
        val urlStr = "$target/api/command?cmd=$encodedCmd"

        thread {
            var conn: HttpURLConnection? = null
            try {
                val url = URL(urlStr)
                conn = url.openConnection() as HttpURLConnection
                conn.connectTimeout = 3000
                conn.readTimeout = 3000
                conn.requestMethod = "POST"

                val code = conn.responseCode
                val stream = if (code in 200..299) conn.inputStream else conn.errorStream
                val body = stream?.bufferedReader()?.use { it.readText() } ?: ""

                mainHandler.post {
                    callback.onResult(code in 200..299, code, body)
                }
            } catch (e: Exception) {
                mainHandler.post {
                    callback.onResult(false, -1, e.message ?: "Failed")
                }
            } finally {
                conn?.disconnect()
            }
        }
    }
}
package com.gautamnc.smartblindstick.hardware

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothSocket
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Handler
import android.os.Looper
import android.util.Log
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.util.UUID

class BluetoothStickManager(private val context: Context) {

    enum class State {
        DISCONNECTED,
        CONNECTING,
        CONNECTED
    }

    interface Listener {
        fun onStateChanged(state: State, deviceName: String?, message: String)
        fun onDeviceDiscovered(device: BluetoothDevice)
        fun onTelemetryData(rawLine: String)
        fun onLog(message: String)
    }

    private var listener: Listener? = null
    private val mainHandler = Handler(Looper.getMainLooper())

    private val bluetoothManager: BluetoothManager? =
        context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    val bluetoothAdapter: BluetoothAdapter? = bluetoothManager?.adapter

    private var activeSocket: BluetoothSocket? = null
    private var activeOutputStream: OutputStream? = null
    private var workerThread: Thread? = null

    var currentState: State = State.DISCONNECTED
        private set
    var connectedDeviceName: String? = null
        private set
    var connectedDeviceAddress: String? = null
        private set

    private val receiver = object : BroadcastReceiver() {
        @SuppressLint("MissingPermission")
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                BluetoothDevice.ACTION_FOUND -> {
                    val device: BluetoothDevice? =
                        intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
                    device?.let {
                        listener?.onDeviceDiscovered(it)
                    }
                }
                BluetoothAdapter.ACTION_DISCOVERY_FINISHED -> {
                    listener?.onLog("Bluetooth discovery finished.")
                }
            }
        }
    }

    private var isReceiverRegistered = false

    fun setListener(listener: Listener?) {
        this.listener = listener
    }

    fun isBluetoothSupported(): Boolean = bluetoothAdapter != null

    fun isBluetoothEnabled(): Boolean = bluetoothAdapter?.isEnabled == true

    @SuppressLint("MissingPermission")
    fun getPairedDevices(): Set<BluetoothDevice> {
        return try {
            bluetoothAdapter?.bondedDevices ?: emptySet()
        } catch (e: Exception) {
            emptySet()
        }
    }

    @SuppressLint("MissingPermission")
    fun startDiscovery(): Boolean {
        if (!isBluetoothEnabled()) return false
        try {
            if (!isReceiverRegistered) {
                val filter = IntentFilter().apply {
                    addAction(BluetoothDevice.ACTION_FOUND)
                    addAction(BluetoothAdapter.ACTION_DISCOVERY_FINISHED)
                }
                context.registerReceiver(receiver, filter)
                isReceiverRegistered = true
            }
            if (bluetoothAdapter?.isDiscovering == true) {
                bluetoothAdapter.cancelDiscovery()
            }
            return bluetoothAdapter?.startDiscovery() ?: false
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start discovery", e)
            return false
        }
    }

    @SuppressLint("MissingPermission")
    fun stopDiscovery() {
        try {
            if (bluetoothAdapter?.isDiscovering == true) {
                bluetoothAdapter.cancelDiscovery()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error cancelling discovery", e)
        }
    }

    @SuppressLint("MissingPermission")
    fun connect(device: BluetoothDevice) {
        stopDiscovery()
        disconnect()

        val name = device.name ?: device.address
        setState(State.CONNECTING, name, "Connecting to $name…")

        Thread {
            try {
                // Standard SPP UUID for Serial Communication with ESP32
                val socket = device.createRfcommSocketToServiceRecord(SPP_UUID)
                socket.connect()

                activeSocket = socket
                activeOutputStream = socket.outputStream
                connectedDeviceName = name
                connectedDeviceAddress = device.address

                setState(State.CONNECTED, name, "Connected to $name")

                // Start read loop
                val reader = BufferedReader(InputStreamReader(socket.inputStream))
                while (currentState == State.CONNECTED && socket.isConnected) {
                    val line = reader.readLine() ?: break
                    if (line.isNotBlank()) {
                        mainHandler.post {
                            listener?.onTelemetryData(line.trim())
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Connection failed or interrupted: ${e.message}", e)
                mainHandler.post {
                    disconnect()
                    setState(State.DISCONNECTED, null, "Disconnected: ${e.message}")
                }
            }
        }.also {
            workerThread = it
            it.isDaemon = true
            it.start()
        }
    }

    fun sendCommand(command: String): Boolean {
        return try {
            val stream = activeOutputStream ?: return false
            val payload = if (command.endsWith("\n")) command else "$command\n"
            stream.write(payload.toByteArray(Charsets.UTF_8))
            stream.flush()
            listener?.onLog("Sent HW command: $command")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to send command: $command", e)
            false
        }
    }

    fun disconnect() {
        try {
            currentState = State.DISCONNECTED
            activeSocket?.close()
            activeSocket = null
            activeOutputStream = null
            workerThread?.interrupt()
            workerThread = null
            val oldName = connectedDeviceName
            connectedDeviceName = null
            connectedDeviceAddress = null
            setState(State.DISCONNECTED, null, "Disconnected from hardware")
        } catch (e: Exception) {
            Log.e(TAG, "Error disconnecting", e)
        }
    }

    fun onDestroy() {
        disconnect()
        if (isReceiverRegistered) {
            try {
                context.unregisterReceiver(receiver)
            } catch (e: Exception) {
                // Ignore
            }
            isReceiverRegistered = false
        }
    }

    private fun setState(state: State, deviceName: String?, message: String) {
        currentState = state
        mainHandler.post {
            listener?.onStateChanged(state, deviceName, message)
        }
    }

    companion object {
        private const val TAG = "BluetoothStickMgr"
        // Standard Bluetooth Serial Port Profile (SPP) UUID
        val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }
}
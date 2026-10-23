package com.gautamnc.smartblindstick.ui

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.ContextCompat
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.gautamnc.smartblindstick.R
import com.gautamnc.smartblindstick.hardware.BluetoothStickManager
import com.gautamnc.smartblindstick.hardware.WifiStickManager

class HardwareBottomSheet(
    private val context: Context,
    private val btManager: BluetoothStickManager,
    private val wifiManager: WifiStickManager
) {
    private val deviceList = ArrayList<BluetoothDevice>()
    private var adapter: DeviceAdapter? = null

    @SuppressLint("MissingPermission")
    fun show(onDeviceSelected: (BluetoothDevice) -> Unit) {
        val dialog = BottomSheetDialog(context)
        val view = LayoutInflater.from(context).inflate(R.layout.dialog_hardware_connection, null)
        dialog.setContentView(view)

        val tvActiveName = view.findViewById<TextView>(R.id.tv_hw_active_name)
        val tvActiveState = view.findViewById<TextView>(R.id.tv_hw_active_state)
        val tvTelemetry = view.findViewById<TextView>(R.id.tv_hw_active_telemetry)
        val ivTypeIcon = view.findViewById<ImageView>(R.id.iv_hw_type_icon)

        val btnScan = view.findViewById<Button>(R.id.btn_scan_bluetooth)
        val btnDisconnect = view.findViewById<Button>(R.id.btn_disconnect_bt)
        val lvDevices = view.findViewById<ListView>(R.id.lv_bluetooth_devices)

        val etWifiIp = view.findViewById<EditText>(R.id.et_wifi_stick_ip)
        val btnPingWifi = view.findViewById<Button>(R.id.btn_test_wifi_stick)

        val tvUsbStatus = view.findViewById<TextView>(R.id.tv_usb_status)
        val btnCheckUsb = view.findViewById<Button>(R.id.btn_check_usb)

        val btnTestVib = view.findViewById<Button>(R.id.btn_test_vibrate)
        val btnTestBuz = view.findViewById<Button>(R.id.btn_test_buzzer)
        val btnRefresh = view.findViewById<Button>(R.id.btn_refresh_status)

        fun checkUsbConnection() {
            try {
                val usbManager = context.getSystemService(Context.USB_SERVICE) as? android.hardware.usb.UsbManager
                val devices = usbManager?.deviceList ?: emptyMap()
                if (devices.isEmpty()) {
                    tvUsbStatus.text = "USB OTG: No USB serial device detected. Connect ESP32 via USB-OTG cable."
                    tvUsbStatus.setTextColor(ContextCompat.getColor(context, R.color.text_secondary))
                } else {
                    val first = devices.values.first()
                    tvUsbStatus.text = "USB Device Detected: ${first.deviceName} (Vendor: 0x${Integer.toHexString(first.vendorId)})"
                    tvUsbStatus.setTextColor(ContextCompat.getColor(context, R.color.status_success))
                }
            } catch (e: Exception) {
                tvUsbStatus.text = "USB OTG: Not supported on this host hardware."
                tvUsbStatus.setTextColor(ContextCompat.getColor(context, R.color.text_muted))
            }
        }

        checkUsbConnection()
        btnCheckUsb.setOnClickListener { checkUsbConnection() }

        fun refreshStatusView() {
            when (btManager.currentState) {
                BluetoothStickManager.State.CONNECTED -> {
                    tvActiveName.text = btManager.connectedDeviceName ?: "ESP32 Stick"
                    tvActiveState.text = "Connected (SPP)"
                    tvActiveState.setTextColor(ContextCompat.getColor(context, R.color.status_success))
                    ivTypeIcon.setColorFilter(ContextCompat.getColor(context, R.color.status_bluetooth))
                    tvTelemetry.text = "Telemetry: Live Link Active [${btManager.connectedDeviceAddress}]"
                    btnDisconnect.visibility = View.VISIBLE
                }
                BluetoothStickManager.State.CONNECTING -> {
                    tvActiveName.text = btManager.connectedDeviceName ?: "ESP32 Stick"
                    tvActiveState.text = "Connecting…"
                    tvActiveState.setTextColor(ContextCompat.getColor(context, R.color.status_warning))
                    btnDisconnect.visibility = View.VISIBLE
                }
                BluetoothStickManager.State.DISCONNECTED -> {
                    tvActiveName.text = "No Stick Connected"
                    tvActiveState.text = "Disconnected"
                    tvActiveState.setTextColor(ContextCompat.getColor(context, R.color.text_muted))
                    ivTypeIcon.setColorFilter(ContextCompat.getColor(context, R.color.status_offline))
                    tvTelemetry.text = "Telemetry: Awaiting physical hardware connection"
                    btnDisconnect.visibility = View.GONE
                }
            }
        }

        refreshStatusView()

        btnRefresh.setOnClickListener {
            refreshStatusView()
            checkUsbConnection()
            deviceList.clear()
            deviceList.addAll(btManager.getPairedDevices())
            adapter?.notifyDataSetChanged()
            Toast.makeText(context, "Hardware status refreshed", Toast.LENGTH_SHORT).show()
        }

        deviceList.clear()
        deviceList.addAll(btManager.getPairedDevices())
        adapter = DeviceAdapter(context, deviceList) { device ->
            dialog.dismiss()
            onDeviceSelected(device)
        }
        lvDevices.adapter = adapter

        btnScan.setOnClickListener {
            if (!btManager.isBluetoothEnabled()) {
                Toast.makeText(context, "Please enable Bluetooth first", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            Toast.makeText(context, "Scanning nearby Bluetooth devices…", Toast.LENGTH_SHORT).show()
            btManager.startDiscovery()
        }

        btnDisconnect.setOnClickListener {
            btManager.disconnect()
            refreshStatusView()
            Toast.makeText(context, "Disconnected from hardware", Toast.LENGTH_SHORT).show()
        }

        btnTestVib.setOnClickListener {
            val sent = btManager.sendCommand("VIBRATE:300")
            if (sent) {
                Toast.makeText(context, "Vibration pulse sent to stick", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(context, "Connect to stick first", Toast.LENGTH_SHORT).show()
            }
        }

        btnTestBuz.setOnClickListener {
            val sent = btManager.sendCommand("BUZZER:200")
            if (sent) {
                Toast.makeText(context, "Buzzer trigger sent to stick", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(context, "Connect to stick first", Toast.LENGTH_SHORT).show()
            }
        }

        btnPingWifi.setOnClickListener {
            val ip = etWifiIp.text.toString().trim()
            if (ip.isBlank()) return@setOnClickListener
            btnPingWifi.isEnabled = false
            btnPingWifi.text = "Testing…"
            wifiManager.pingStick(ip, object : WifiStickManager.Callback {
                override fun onResult(isReachable: Boolean, responseCode: Int, responseBody: String) {
                    btnPingWifi.isEnabled = true
                    btnPingWifi.text = "Connect / Ping"
                    if (isReachable) {
                        Toast.makeText(context, "Stick reachable! HTTP $responseCode", Toast.LENGTH_LONG).show()
                        tvTelemetry.text = "Wi-Fi Stick Reachable: $ip ($responseCode)"
                    } else {
                        Toast.makeText(context, "Stick unreachable at $ip: $responseBody", Toast.LENGTH_LONG).show()
                    }
                }
            })
        }

        dialog.show()
    }

    fun addDiscoveredDevice(device: BluetoothDevice) {
        if (!deviceList.any { it.address == device.address }) {
            deviceList.add(device)
            adapter?.notifyDataSetChanged()
        }
    }

    private class DeviceAdapter(
        context: Context,
        private val items: List<BluetoothDevice>,
        private val onConnectClicked: (BluetoothDevice) -> Unit
    ) : ArrayAdapter<BluetoothDevice>(context, 0, items) {

        @SuppressLint("MissingPermission", "ViewHolder")
        override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
            val view = convertView ?: LayoutInflater.from(context).inflate(R.layout.item_bluetooth_device, parent, false)
            val device = items[position]

            val tvName = view.findViewById<TextView>(R.id.tv_device_name)
            val tvAddr = view.findViewById<TextView>(R.id.tv_device_address)
            val btnConn = view.findViewById<Button>(R.id.btn_device_connect)

            val name = device.name ?: "Unknown Device"
            tvName.text = name
            tvAddr.text = device.address

            val isStick = name.contains("stick", ignoreCase = true) ||
                    name.contains("esp32", ignoreCase = true) ||
                    name.contains("drishti", ignoreCase = true)

            if (isStick) {
                tvName.setTextColor(ContextCompat.getColor(context, R.color.brand_primary))
            } else {
                tvName.setTextColor(ContextCompat.getColor(context, R.color.text_primary))
            }

            btnConn.setOnClickListener {
                onConnectClicked(device)
            }

            return view
        }
    }
}
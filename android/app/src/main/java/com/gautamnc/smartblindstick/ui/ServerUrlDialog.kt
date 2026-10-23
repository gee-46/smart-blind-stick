package com.gautamnc.smartblindstick.ui

import android.app.AlertDialog
import android.content.Context
import android.view.LayoutInflater
import android.widget.Button
import android.widget.EditText
import com.gautamnc.smartblindstick.R
import com.gautamnc.smartblindstick.data.AppPreferences

object ServerUrlDialog {
    fun show(context: Context, prefs: AppPreferences, onUrlSaved: (String) -> Unit) {
        val view = LayoutInflater.from(context).inflate(R.layout.dialog_server_url, null)
        val etUrl = view.findViewById<EditText>(R.id.et_server_url)
        val btnSave = view.findViewById<Button>(R.id.btn_save_url)
        val btnCancel = view.findViewById<Button>(R.id.btn_cancel_url)
        val btnPresetCloud = view.findViewById<Button>(R.id.btn_preset_cloud)
        val btnPresetEmulator = view.findViewById<Button>(R.id.btn_preset_emulator)

        etUrl.setText(prefs.serverUrl)
        etUrl.setSelection(etUrl.text.length)

        btnPresetCloud?.setOnClickListener {
            etUrl.setText(prefs.defaultServerUrl)
            etUrl.setSelection(etUrl.text.length)
        }

        btnPresetEmulator?.setOnClickListener {
            etUrl.setText("http://10.0.2.2:8000/app")
            etUrl.setSelection(etUrl.text.length)
        }

        val dialog = AlertDialog.Builder(context)
            .setView(view)
            .create()

        btnSave.setOnClickListener {
            val raw = etUrl.text.toString().trim()
            if (raw.isNotBlank()) {
                val formatted = if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
                    "http://$raw"
                } else {
                    raw
                }
                prefs.serverUrl = formatted
                dialog.dismiss()
                onUrlSaved(formatted)
            }
        }

        btnCancel.setOnClickListener {
            dialog.dismiss()
        }

        dialog.show()
    }
}
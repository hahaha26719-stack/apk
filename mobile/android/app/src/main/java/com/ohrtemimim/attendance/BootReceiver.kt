package com.ohrtemimim.attendance

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Launches the Ohr Temimim Attendance app automatically after the device
 * finishes booting. This makes the device behave like a kiosk/attendance
 * terminal that is always ready at the school entrance.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        val action = intent?.action ?: return
        if (action == Intent.ACTION_BOOT_COMPLETED ||
            action == Intent.ACTION_LOCKED_BOOT_COMPLETED ||
            action == "android.intent.action.QUICKBOOT_POWERON" ||
            action == "com.htc.intent.action.QUICKBOOT_POWERON"
        ) {
            val launch = Intent(context, MainActivity::class.java).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(launch)
        }
    }
}

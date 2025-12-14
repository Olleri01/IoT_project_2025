package com.example.myapplication
import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

class MqttViewModel(app: Application) : AndroidViewModel(app) {
    private val controller = MqttController(app.applicationContext)
    val isConnected = controller.isConnected
    val status = controller.status

    fun start() {
        controller.connect()
    }

    fun publishMessage(topic: String, message: String){
        controller.publish(topic, message)
    }

    fun getAllServerData() : StateFlow<JSONArray?> {
        return controller.jsonDump
    }

    fun getNewestServerData() : StateFlow<JSONObject?> {
        return controller.newestData
    }

    override fun onCleared() {
        controller.disconnect()
        super.onCleared()
    }
}
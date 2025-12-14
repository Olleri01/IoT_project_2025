package com.example.myapplication
import android.content.Context
import android.util.Log
//import info.mqtt.android.service.MqttAndroidClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
//import org.eclipse.paho.android.service.MqttAndroidClient
//import org.eclipse.paho.client.mqttv3.*
import org.json.JSONException
import org.json.JSONObject

import com.hivemq.client.mqtt.MqttClient
import com.hivemq.client.mqtt.MqttGlobalPublishFilter
import com.hivemq.client.mqtt.mqtt3.Mqtt3AsyncClient
import com.hivemq.client.mqtt.mqtt3.Mqtt3Client
import com.hivemq.client.mqtt.mqtt3.message.publish.Mqtt3Publish
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import org.json.JSONArray
import java.nio.ByteBuffer
import java.nio.charset.Charset
import java.nio.charset.StandardCharsets
import java.util.Optional

class MqttController(
    context: Context,
    brokerUrl: String = "aae0fdec.ala.eu-central-1.emqxsl.com",
    brokerPort: Int = 8883,
    clientId: String = "iot_mqtt_pico_w",
    username: String = "pico_w",
    password: String = "laatti"
) {
    private val scope = CoroutineScope(Dispatchers.IO)
    private var _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected

    private val _jsonDump = MutableStateFlow<JSONArray?>(null)
    val jsonDump: StateFlow<JSONArray?> = _jsonDump
    private val _newestData = MutableStateFlow<JSONObject?>(null)
    val newestData : StateFlow<JSONObject?> = _newestData
    private val _status = MutableStateFlow<String?>("")
    val status : StateFlow<String?> = _status


    private val client: Mqtt3AsyncClient = Mqtt3Client.builder()
        .identifier(clientId)
        .serverHost(brokerUrl)
        .serverPort(brokerPort)
        .sslWithDefaultConfig()
        .simpleAuth()
        .username(username)
        .password(password.toByteArray())
        .applySimpleAuth()
        .buildAsync()

    fun connect() {
        scope.launch {
            try {
                client.connect().whenComplete { _, throwable ->
                    if (throwable != null) {
                        Log.e("MQTT", "Connection to MQTT server failed", throwable)
                        _isConnected.value = false
                    } else {
                        Log.d("MQTT", "Successfully connected to the MQTT server")
                        _isConnected.value = true
                        scope.launch { subscribeToTopics() }
                    }
                }
            } catch (e: Exception) {
                Log.e("MQTT", "Exception during connect", e)
                _isConnected.value = false
            }
        }
    }

    private suspend fun subscribeToTopics() {
        scope.launch {
            try {
                client.subscribeWith()
                    .topicFilter("skynet/intel_data")
                    .callback { publish: Mqtt3Publish ->
                        Log.d("MQTT", "Payload arrived at skynet/intel_data")
                        val payload = byteBufferToString(publish.payload)
                        if (payload != null) {

                            try {
                                val msg = JSONObject(payload)
                                _newestData.value = msg
                            } catch(e: JSONException) {
                                Log.e("MQTT", "message from MQTT server was not valid JSON syntax", e)
                                _newestData.value = null
                        }
                    } }
                    .send()
                    .get()
                client.subscribeWith()
                    .topicFilter("skynet/return_data")
                    .callback { publish: Mqtt3Publish ->
                        Log.d("MQTT", "Payload arrived at skynet/return_data")
                        val payload = byteBufferToString(publish.payload)
                        if (payload != null) {
                            try {
                                val msg = JSONArray(payload)
                                _jsonDump.value = msg
                            } catch(e: JSONException) {
                                Log.e(
                                    "MQTT", "message from MQTT server was not valid JSON syntax", e)
                                _jsonDump.value = null
                            }
                        } }
                    .send()
                    .get()

                client.subscribeWith()
                    .topicFilter("skynet/mqtt_get_status")
                    .callback { publish: Mqtt3Publish ->
                        Log.d("MQTT", "Payload arrived at skynet/mqtt_get_status")
                        _status.value = byteBufferToString(publish.payload)
                    }
                    .send()
                    .get()

            } catch (e: Exception) {
                Log.e("MQTT", "Subscription unsuccessful", e)
            }
        }
    }

    private fun byteBufferToString(payload: Optional<ByteBuffer>) : String? {
        val result = payload.orElse(null)?.let { buffer ->
            val bytes = ByteArray(buffer.remaining())
            buffer.get(bytes)
            String(bytes, Charsets.UTF_8)
        }
        return result
    }

    fun publish(topic: String, message: String) {
        scope.launch {
            try {
                client.publishWith()
                    .topic(topic)
                    .payload(message.toByteArray())
                    .send()
                Log.d("MQTT", "Published message: $message to $topic successfully")
            } catch (e: Exception) {
                Log.e("MQTT", "Publish was unsuccessful", e)
            }
        }
    }

    fun disconnect() {
        scope.launch {
            try {
                client.disconnect()
                _isConnected.value = false
            } catch (e: Exception) {
                Log.e("MQTT", "Failed to disconnect", e)
            }
        }
    }
}
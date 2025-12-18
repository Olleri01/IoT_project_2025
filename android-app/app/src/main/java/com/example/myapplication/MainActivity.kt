package com.example.myapplication

import androidx.compose.ui.graphics.Color
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.input.rememberTextFieldState
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ModifierLocalBeyondBoundsLayout
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.myapplication.ui.theme.MyApplicationTheme
import kotlinx.coroutines.delay
import org.json.JSONArray
import org.json.JSONObject

enum class Screens {
    HomeScreen,
    SecondaryScreen // RENAME when given actual implementation
}
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyApplicationTheme {
                App()
            }
        }
    }
}

@Composable
fun App() {
    val navController = rememberNavController()

    val viewModel: MqttViewModel = viewModel()
    //viewModel.start()

    NavHost(
        navController = navController,
        startDestination = Screens.HomeScreen.name
    ) {
        composable(Screens.HomeScreen.name) {
            HomeScreen(
                viewModel,
                onNavigateToSecondaryScreen = {
                    navController.navigate(Screens.SecondaryScreen.name)
                }
            )
        }
        composable(Screens.SecondaryScreen.name) {
            SecondaryScreen()
        }
    }
}

@Composable
fun HomeScreen(viewModel: MqttViewModel, onNavigateToSecondaryScreen: () -> Unit) {

    val allServerData by viewModel.getAllServerData().collectAsState()
    val newestServerData by viewModel.getNewestServerData().collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()
    val picoStatus by viewModel.status.collectAsState()

    if (!isConnected) {
        NoConnectionScreen(
            connectToServer = {connectToServer(viewModel)}
        )
    }
    else  {
        ConnectedScreen(
            viewModel = viewModel,
            allServerData = allServerData,
            newestServerData = newestServerData,
            picoStatus = picoStatus,

            getLast7DaysOfData = {getLast7DaysOfData(viewModel)},
            getNewestData = {getLast7DaysOfData(viewModel)},
            getAllData = {getAllData(viewModel)},
            toggleStatus = {toggleStatus(viewModel, picoStatus) }
        )
    }
}

@Composable
fun NoConnectionScreen(
    connectToServer: () -> Unit
)
{
    Column(
        modifier = Modifier
        .fillMaxSize()
        .padding(horizontal = 5.dp, vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {

        Spacer(modifier = Modifier.padding(12.dp))

        Text(text = "Pedestrian Detection System",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.SemiBold)

        Spacer(modifier = Modifier.weight(1f))

        ElevatedCard(
            elevation = CardDefaults.cardElevation(
                defaultElevation = 8.dp
            ),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant,
            ),
            modifier = Modifier
                .size(width = 350.dp, height = 80.dp)
        ) {
            Text(
                text = "The app has is not connected to the server \n Please start the connection",
                modifier = Modifier
                    .padding(16.dp),
                textAlign = TextAlign.Center,
            )
        }

        Spacer(modifier = Modifier.padding(10.dp))

        ElevatedButton(onClick = connectToServer) {
            Text("Connect to server")
        }

        Spacer(modifier = Modifier.weight(1f))
    }
}

@Composable
fun ConnectedScreen(
    viewModel: MqttViewModel,
    allServerData: JSONArray?,
    newestServerData: JSONObject?,
    picoStatus: String?,

    getLast7DaysOfData: () -> Unit,
    getNewestData: () -> Unit,
    getAllData: () -> Unit,
    toggleStatus: () -> Unit = {
        toggleStatus(viewModel, picoStatus)
    }
)
{
    Column(
        modifier = Modifier
        .fillMaxSize()
        .padding(horizontal = 5.dp, vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {

        Spacer(modifier = Modifier.padding(12.dp))

        Text(
            text =  "Pedestrian Detection System",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.SemiBold
        )

        Spacer(modifier = Modifier.padding(12.dp))

        Text(text = "Status: $picoStatus")

        Spacer(modifier = Modifier.padding(4.dp))

        updateNewestDataEachMinute(viewModel)

        Spacer(modifier = Modifier.padding(4.dp))

        if (newestServerData != null) {
            Text(
                text = "Cyclists: " + newestServerData.get("currentHourCyclists").toString()
            )
            Text(
                text = "Walkers: " + newestServerData.get("currentHourWalkers").toString()
            )
        } else {
            Text(text = "Cyclists: ...")
            Text(text = "Walkers: ...")
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Data Visualisation (Temperature, Pressure)
        if (allServerData != null) {
            Box(modifier = Modifier
                .weight(6f)
                .background(Color.LightGray)
                .padding(12.dp)
            ) {
                LazyColumn() {
                    item {
                        PlotData(allServerData, "currentHourCyclists", "Cyclists", 0)
                        Spacer(modifier = Modifier.height(12.dp))
                        PlotData(allServerData, "currentHourWalkers", "Walkers", 0)
                        Spacer(modifier = Modifier.height(12.dp))
                        PlotData(allServerData, "temperature", "Temperature (°C)", 2)
                        Spacer(modifier = Modifier.height(12.dp))
                        PlotData(allServerData, "pressure", "Pressure", 3)
                    }
                }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 5.dp, vertical = 10.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(text = "Waiting for data...")
                Spacer(modifier = Modifier.padding(5.dp))
                Button(onClick = getLast7DaysOfData) {
                    Text(text = "Data Request")
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        Row(modifier = Modifier.weight(1f)) {

            Spacer(modifier = Modifier.weight(1f))

            Button(onClick = getNewestData) {
                Text(text = "Get newest data (manual update)")
            }

            Spacer(modifier = Modifier.weight(1f))

        }

        if (picoStatus == "{\"status\":1}") {
            Button(onClick = toggleStatus,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Green
                )) {
                Text(text = "Toggle status to 0")
            }
        }
        else {
            Button(onClick = toggleStatus,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Red
                )) {
                Text(text = "Toggle status to 1")
            }
        }
        Spacer(modifier = Modifier.padding(12.dp))
    }
}

@Composable
fun updateNewestDataEachMinute(viewModel: MqttViewModel) {
    var secondsLeft by remember { mutableStateOf(60) }

    LaunchedEffect(Unit) {
        while (true) {
            if (secondsLeft == 0) {
                getLast7DaysOfData(viewModel)
                secondsLeft = 60
            }
            delay(1000)
            secondsLeft--
        }
    }

    Text(text = "Time until data refresh: $secondsLeft")
}

private fun getAllData(viewModel: MqttViewModel) {
    getLast7DaysOfData(viewModel)
    //getNewestData(viewModel)
}

private fun getLast7DaysOfData(viewModel: MqttViewModel) {
    val now = System.currentTimeMillis()
    val weekInMillis = 7 * 24 * 60 * 60 * 1000
    viewModel.publishMessage("skynet/on_get_data", "{\"startDate\":${now-weekInMillis},\"endDate\":$now}")
}

/*private fun getNewestData(viewModel: MqttViewModel) {
    val now = System.currentTimeMillis()
    val twoMinuteInMillis = 2 * 60 * 1000
    viewModel.publishMessage("skynet/on_get_data","{\"startDate\":${now-twoMinuteInMillis},\"endDate\":$now}" )
}*/


private fun toggleStatus(viewModel: MqttViewModel, currentStatus: String?) {
    if (currentStatus == "{\"status\":1}") {
        viewModel.publishMessage("skynet/mqtt_set_status", "{\"status\":0}")
    }
    else {
        viewModel.publishMessage("skynet/mqtt_set_status", "{\"status\":1}")
    }
}

private fun connectToServer(viewModel: MqttViewModel) {
    viewModel.start()
    viewModel.publishMessage("skynet/mqtt_set_status","{\"status\":1}" )
}

@Composable
fun SecondaryScreen() {
    Text(text = "Second screen",
        color = Color.Black)
}

@Preview
@Composable
fun NoConnectionPreview() {
    MyApplicationTheme {
        NoConnectionScreen(connectToServer = {})
    }
}

/*@Preview
@Composable
fun ConnectedPreview() {
    MyApplicationTheme {
        ConnectedScreen(
            allServerData = JSONArray(
                """[
                    {
                        "result":"_result",
                        "table":0,
                        "_time":"2025-12-08T21:39:54.035Z",
                        "currentHourCyclists":0,
                        "currentHourWalkers":0,
                        "humidity":0,
                        "luminosity":0,
                        "pressure":1.00292,
                        "temperature":22.1656
                    },
                    {
                        "result":"_result",
                        "table":0,
                        "_time":"2025-12-08T21:40:56.199Z",
                        "currentHourCyclists":0,
                        "currentHourWalkers":0,
                        "humidity":0,
                        "luminosity":0,
                        "pressure":1.0029299999999999,
                        "temperature":22.1607
                    },
                    {
                        "result":"_result",
                        "table":0,
                        "_time":"2025-12-08T21:41:58.436Z",
                        "currentHourCyclists":0,
                        "currentHourWalkers":0,
                        "humidity":0,
                        "luminosity":0,
                        "pressure":1.00298,
                        "temperature":22.1533
                    }
                ]"""
            ),
            newestServerData = JSONObject(),
            picoStatus = "TEST",

            getLast7DaysOfData = {},
            getNewestData = {},
            getAllData = {},
            toggleStatus = {},
            viewModel
        )
    }
}*/

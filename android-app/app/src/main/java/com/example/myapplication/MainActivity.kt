package com.example.myapplication

import androidx.compose.ui.graphics.Color
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.input.rememberTextFieldState
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.myapplication.ui.theme.MyApplicationTheme

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
    viewModel.start()

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
        Column(modifier = Modifier.fillMaxSize().
            padding(horizontal = 5.dp, vertical = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally) {

            Spacer(modifier = Modifier.padding(12.dp))

            Text(text =  "PLACEHOLDER_NAME",
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
                    text = "The app has no connection to the server \n Launch the server",
                    modifier = Modifier
                        .padding(16.dp),
                    textAlign = TextAlign.Center,
                )
            }

            Spacer(modifier = Modifier.padding(10.dp))

            ElevatedButton(onClick = { connectToServer(viewModel) }) {
                Text("Connect to server")
            }

            Spacer(modifier = Modifier.weight(1f))
        }
    }
    else  {
        Column(modifier = Modifier.fillMaxSize().
        padding(horizontal = 5.dp, vertical = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center) {

            Spacer(modifier = Modifier.padding(12.dp))

            Text(text =  "PLACEHOLDER_NAME",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.SemiBold)

            Spacer(modifier = Modifier.padding(12.dp))

            Text(text = "Status: $picoStatus")

            Spacer(modifier = Modifier.weight(1f))

            // TODO: display data so that its not ugly
            Text(
                text = allServerData.toString()
            )

            Spacer(modifier = Modifier.weight(1f))

            Text(
                text = newestServerData.toString()
            )

            Spacer(modifier = Modifier.weight(1f))

            Row() {

                Spacer(modifier = Modifier.weight(1f))

                Button(onClick = { getLast7DaysOfData(viewModel) }) {
                    Text(text = "Get last 7 days of data")
                }

                Spacer(modifier = Modifier.padding(25.dp))


                Button(onClick = {setStatus(viewModel) }) {
                    Text(text = "Set status to 1")
                }

                Spacer(modifier = Modifier.padding(25.dp))

                /*Button(onClick = {getNewestData(viewModel) }) {
                    Text(text = "Get the newest data (no implementation")
                }*/

                Spacer(modifier = Modifier.weight(1f))
            }

            Spacer(modifier = Modifier.weight(1f))
        }
    }
}

private fun getLast7DaysOfData(viewModel: MqttViewModel) {
    viewModel.publishMessage("skynet/on_get_data", "{\"startDate\":1765201452000,\"endDate\":1765230121000}")
}

private fun getNewestData(viewModel: MqttViewModel) {
    // Maybe useless? idk yet im too lazy rn
}

private fun setStatus(viewModel: MqttViewModel) {
    viewModel.publishMessage("skynet/mqtt_set_status", "{\"status\":1}")

}

private fun connectToServer(viewModel: MqttViewModel) {
    viewModel.start()
}

@Composable
fun SecondaryScreen() {
    Text(text = "Second screen",
        color = Color.Black)
}
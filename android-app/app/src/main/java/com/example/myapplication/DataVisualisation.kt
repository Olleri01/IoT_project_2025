package com.example.myapplication

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import co.yml.charts.axis.AxisData
import co.yml.charts.common.model.Point
import co.yml.charts.ui.linechart.LineChart
import co.yml.charts.ui.linechart.model.GridLines
import co.yml.charts.ui.linechart.model.IntersectionPoint
import co.yml.charts.ui.linechart.model.Line
import co.yml.charts.ui.linechart.model.LineChartData
import co.yml.charts.ui.linechart.model.LinePlotData
import co.yml.charts.ui.linechart.model.LineStyle
import co.yml.charts.ui.linechart.model.LineType
import co.yml.charts.ui.linechart.model.SelectionHighlightPoint
import co.yml.charts.ui.linechart.model.SelectionHighlightPopUp
import co.yml.charts.ui.linechart.model.ShadowUnderLine
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.time.ZoneId
import kotlin.math.pow
import kotlin.math.round

@Composable
fun PlotData(allServerData: JSONArray?, dataName: String, title: String, labelDecimals: Int) {

    val dataPoints: MutableList<Point> = mutableListOf()

    if (allServerData != null && allServerData.length() > 0) {

        // Get data points from allServerData
        for (i in 0..<allServerData.length()) {

            val dataPointObject: JSONObject = allServerData.getJSONObject(i)

            // Get x-value (epoch milli)
            val timeStamp: String = dataPointObject.getString("_time")
            val instant = Instant.parse(timeStamp)
            val epochTime = instant.toEpochMilli()

            // Get y-value data
            val data: Double = dataPointObject.getDouble(dataName)

            // Create and save data point
            val dataPoint = Point(epochTime.toFloat(), data.toFloat())
            dataPoints.add(dataPoint)
        }


        // x-Axis
        val xMin = dataPoints.minOf { it.x }
        val xMax = dataPoints.maxOf { it.x }
        val diff = xMax - xMin

        // Label every ~3 hours
        val xSteps = diff / (180* 60*1000)

        val xAxisData = AxisData.Builder()
            .axisStepSize((0.00001).dp)
            .steps(xSteps.toInt())
            .labelData { i ->
                val epoch = (i + xMin).toLong()
                // Label format: DD.MM (hh:mm)
                val dateTime = Instant.ofEpochMilli(epoch).atZone(ZoneId.systemDefault()).toLocalDateTime()
                "${dateTime.dayOfMonth}.${dateTime.monthValue} (${dateTime.hour}:${dateTime.minute})"
            }
            .build()


        // y-Axis
        val ySteps = 10
        val decimalHelper = 10.toFloat().pow(labelDecimals)
        val yAxisData = AxisData.Builder()
            .steps(ySteps)
            .labelData { i ->
                val yMin = dataPoints.minOf { it.y }
                val yMax = dataPoints.maxOf { it.y }
                val yScale = (yMax - yMin) / ySteps
                (round(((i * yScale) + yMin) * decimalHelper) / decimalHelper).toString()
            }
            .build()

        // Line Chart
        val lineChartData = LineChartData(
            linePlotData = LinePlotData(
                lines = listOf(
                    Line(
                        dataPoints = dataPoints,
                        lineStyle = LineStyle(
                            lineType = LineType.Straight()
                        ),
                        intersectionPoint = IntersectionPoint(radius = 0.dp),
                        selectionHighlightPoint = SelectionHighlightPoint(),
                        shadowUnderLine = null,
                        selectionHighlightPopUp = SelectionHighlightPopUp()
                    )
                ),
            ),
            xAxisData = xAxisData,
            yAxisData = yAxisData,
            gridLines = GridLines(),
            backgroundColor = Color.White
        )
        Text(text = title)
        LineChart(
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp),
            lineChartData = lineChartData
        )

    } else {
        Text(text = "Data not found...")
    }
}

@Preview
@Composable
fun PlotDataPreview() {
    PlotData(
        allServerData = JSONArray(
            """
            [{
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:09:00.025Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:09:12.065Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":20.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:09:27.529Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":22.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:09:57.668Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:09:59.16Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:10:01.712Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:10:02.278Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T15:10:03.321Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1,
              "temperature":21.5
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:24:14.641Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00338,
              "temperature":22.3686
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:25:16.792Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00337,
              "temperature":22.3686
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:26:18.942Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00336,
              "temperature":22.3734
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:27:21.204Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00338,
              "temperature":22.3883
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:28:23.41Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00332,
              "temperature":22.3957
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:29:25.54Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00337,
              "temperature":22.4031
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:30:27.775Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00331,
              "temperature":22.423
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:31:30.107Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00332,
              "temperature":22.4031
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:32:32.395Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00336,
              "temperature":22.376
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:33:34.625Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00335,
              "temperature":22.3586
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:34:36.782Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00335,
              "temperature":22.3463
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:35:39.008Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0033400000000001,
              "temperature":22.3463
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:36:41.162Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00336,
              "temperature":22.3537
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:37:43.392Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00333,
              "temperature":22.376
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:38:45.545Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00333,
              "temperature":22.3785
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:39:47.69Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0032999999999999,
              "temperature":22.4602
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:40:49.93Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00332,
              "temperature":22.517
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:41:52.113Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00329,
              "temperature":22.5145
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:42:54.267Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00329,
              "temperature":22.4773
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:43:56.503Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0032699999999999,
              "temperature":22.4625
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:44:58.661Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00328,
              "temperature":22.4527
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:46:00.734Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00331,
              "temperature":22.4254
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:47:02.974Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0032999999999999,
              "temperature":22.4551
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:48:05.045Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0032699999999999,
              "temperature":22.4453
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:49:07.194Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00331,
              "temperature":22.4453
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:50:09.445Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00328,
              "temperature":22.475
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:51:11.566Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00326,
              "temperature":22.4898
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:52:13.714Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00325,
              "temperature":22.4699
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:53:15.947Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00321,
              "temperature":22.475
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:54:18.111Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00322,
              "temperature":22.4502
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:55:20.437Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00318,
              "temperature":22.4428
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:56:22.529Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00314,
              "temperature":22.4305
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:57:24.857Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00312,
              "temperature":22.4453
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:58:27.215Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0031,
              "temperature":22.4502
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T20:59:29.306Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0031,
              "temperature":22.4477
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T21:00:31.531Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.0031,
              "temperature":22.4328
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T21:01:33.723Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00314,
              "temperature":22.423
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T21:02:35.881Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00316,
              "temperature":22.376
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T21:03:38.011Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00312,
              "temperature":22.3463
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-08T21:38:51.873Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00295,
              "temperature":22.1559
           },
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
              "_time":"2025-12-09T15:09:00.025Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00298,
              "temperature":22.1533
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-10T15:09:00.025Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00298,
              "temperature":22.1533
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-09T15:09:00.025Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00298,
              "temperature":22.1533
           },
           {
              "result":"_result",
              "table":0,
              "_time":"2025-12-15T15:09:00.025Z",
              "currentHourCyclists":0,
              "currentHourWalkers":0,
              "humidity":0,
              "luminosity":0,
              "pressure":1.00298,
              "temperature":22.1533
           }]
            """
        ),
        dataName = "temperature",
        title = "Temperature (°C)",
        labelDecimals = 2
    )
}

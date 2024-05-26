d3.csv("/data/xmr-earnings.csv", function(data) {
  // Convert the 'Amount' and 'Total' columns to numbers
Array.from(data).forEach(function(d) {
    d.Amount = +d.Amount;
    d.Total = +d.Total;
  });

  // Create the chart
var chart = d3.select("#chart")
    .append("svg")
    .attr("width", 800)
    .attr("height", 640);

  // Define scales
var x = d3.scaleTime()
    .domain(d3.extent(data, function(d) { return new Date(d.Date); }))
    .range([0, 800]);
  var y = d3.scaleLinear()
    .domain(d3.extent(data, function(d) { return d.Total; }))
    .range([640, 0]);

  // Create axes
var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));
  var yAxis = d3.axisLeft(y);
  chart.append("g")
    .attr("transform", "translate(0," + 800 + ")")
    .call(xAxis);
  chart.append("g")
    .attr("transform", "translate(0,0)")
    .call(yAxis);

  // Create line
var line = d3.line()
    .x(function(d) { return x(new Date(d.Date)); })
    .y(function(d) { return y(d.Total); });

  // Draw line on chart
chart.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line);
});


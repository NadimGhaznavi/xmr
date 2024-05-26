d3.csv("/_data/xmr-earnings.csv", function(data) {
  // Convert the 'Amount' and 'Total' columns to numbers
data.forEach(function(d) {
    d.Amount = +d.Amount;
    d.Total = +d.Total;
  });

  // Create the chart
var chart = d3.select("#chart")
    .append("svg")
    .attr("width", <width>)
    .attr("height", <height>);

  // Define scales
var x = d3.scaleTime()
    .domain(d3.extent(data, function(d) { return new Date(d.Date); }))
    .range([0, <width>]);
  var y = d3.scaleLinear()
    .domain(d3.extent(data, function(d) { return d.Total; }))
    .range([<height>, 0]);

  // Create axes
var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));
  var yAxis = d3.axisLeft(y);
  chart.append("g")
    .attr("transform", "translate(0," + <height> + ")")
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


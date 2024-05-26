d3.csv("/data/xmr-earnings.csv", function(data) {
  Array.from(data).forEach(function(d) {
    d.Amount = +d.Amount;
    d.Total = +d.Total;
  });

console.log(data); // Log the data to verify its structure 

  var chart = d3.select("#chart")
    .append("svg")
    .attr("width", 800)
    .attr("height", 800);

  var x = d3.scaleTime()
    .domain(d3.extent(data.filter(d => d.Date && d.Total), function(d) { return new Date(d.Date); }))
    .range([0, 800]);

  var y = d3.scaleLinear()
    .domain(d3.extent(data.filter(d => d.Date && d.Total), function(d) { return d.Total; }))
    .range([0, 800]);

  var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));
  var yAxis = d3.axisLeft(y);
  chart.append("g")
    .attr("transform", "translate(0," + 400 + ")")
    .call(xAxis);
  chart.append("g")
    .attr("transform", "translate(0,0)")
    .call(yAxis);

  var line = d3.line()
    .x(function(d) { return x(new Date(d.Date)); })
    .y(function(d) { return y(d.Total); });

  chart.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line);
});

d3.csv("/data/xmr-earnings.csv", function(data) {
  // Parse data
  Array.from(data).forEach(function(d) {
    d.Amount = +d.Amount;
    d.Total = +d.Total;
    console.log(data); // Log the data to verify its structure
  });

  // Create SVG element
  var chart = d3.select("#chart")
    .append("svg")
    .attr("width", 800) // Adjust width as needed
    .attr("height", 800); // Adjust height as needed

  // Create x-axis scale
  var x = d3.scaleTime()
    .domain(d3.extent(data.filter(d => d.Date && d.Total), function(d) { return new Date(d.Date); }))
    .range([0, 800]);

  // Create y-axis scale
  var y = d3.scaleLinear()
    .domain(d3.extent(data.filter(d => d.Date && d.Total), function(d) { return d.Total; }))
    .range([0, 800]);

  // Generate x-axis
  var xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));

  // Generate y-axis
  var yAxis = d3.axisLeft(y);

  // Add x-axis to SVG
  chart.append("g")
    .attr("transform", "translate(0," + 400 + ")")
    .call(xAxis);

  // Add y-axis to SVG
  chart.append("g")
    .attr("transform", "translate(0,0)")
    .call(yAxis);

  // Create line generator
  var line = d3.line()
    .x(function(d) { return x(new Date(d.Date)); })
    .y(function(d) { return y(d.Total); });

  // Add line path to SVG
  chart.append("path")
    .datum(data)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line);
});




// Define the margin and nudge objects
var margin = {left: 50, right: 20, top: 20, bottom: 50};
var nudge = {x: 50, y: 20};

// Define the chart dimensions
var width = 960 - margin.left - margin.right;
var height = 500 - margin.top - margin.bottom;

// Define the date parser
var parseDate = d3.timeParse("%Y-%m-%d");

// Load and parse the CSV data
d3.csv("/data/xmr-earnings.csv")
  .row(function(d) {
    return {
      date: parseDate(d.Date),
      total: Number(d.Total)
    };
  })
  .get(function(error, rows) {
    // Check if an error occurred while loading the CSV file
if (error) {
      console.error("Error loading CSV file:", error);
      return;
    }

    // Calculate the maximum total value
var maxTotal = d3.max(rows, function(d) { return d.total; });

    // Define the y-scale
var y = d3.scaleLinear()
      .domain([0, maxTotal])
      .range([height, 0]);

    // Define the x-scale
var x = d3.scaleTime()
      .domain(d3.extent(rows, function(d) { return d.date; }))
      .range([0, width]);

    // Create the line generator
var line = d3.line()
      .x(function(d) { return x(d.date); })
      .y(function(d) { return y(d.total); })
      .curve(d3.curveCardinal);

    // Create the SVG element
var svg = d3.select("body").append("svg")
      .attr("id", "svg")
      .attr("viewBox", "0 0 " + width + " " + height);

    // Create the chart group and translate it
var chartGroup = svg.append("g").attr("class", "chartGroup")
      .attr("transform", "translate(" + nudge.x + "," + nudge.y + ")");

    // Add the line path to the chart group
chartGroup.append("path")
      .attr("class", "line")
      .attr("d", line(rows));

    // Add the x-axis to the chart group
chartGroup.append("g")
      .attr("class", "xAxis")
      .attr("transform", "translate(0," + height + ")")
      .call(d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d/%y")));

    // Add the y-axis to the chart group
chartGroup.append("g")
      .attr("class", "yAxis")
      .call(d3.axisLeft(y));
  });

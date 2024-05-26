// Static data
const data = [
  { Date: new Date("2024-03-21"), Total: 0.012802020866 },
  { Date: new Date("2024-03-22"), Total: 0.012802020866 },
  // ... Add more data points here ...
];

// Create SVG element
const chart = d3.select("#chart")
  .append("svg")
  .attr("width", 800)
  .attr("height", 800)
  .attr("viewBox", "0 0 800 800");

// Create x-axis scale
const x = d3.scaleTime()
  .domain(d3.extent(data, d => d.Date))
  .range([0, 800]);

// Create y-axis scale
const y = d3.scaleLinear()
  .domain(d3.extent(data, d => d.Total))
  .range([0, 800]);

// Generate x-axis
const xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));

// Generate y-axis
const yAxis = d3.axisLeft(y);

// Add x-axis to SVG
chart.append("g")
  .attr("transform", "translate(0," + 400 + ")")
  .call(xAxis);

// Add y-axis to SVG
chart.append("g")
  .attr("transform", "translate(0,0)")
  .call(yAxis);

// Create line generator
const line = d3.line()
  .x(d => x(d.Date))
  .y(d => y(d.Total));

// Add line path to SVG
chart.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", "steelblue")
  .attr("stroke-width", 1.5)
  .attr("d", line);

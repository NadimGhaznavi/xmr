d3.csv("/data/xmr-earnings.csv", function(data) {
  // Convert data to an array explicitly
const dataArray = Array.from(data);

  // Process data and create scales
const x = d3.scaleTime()
    .domain(d3.extent(dataArray.filter(d => d.Date && d.Total), d => new Date(d.Date)))
    .range([0, 800]);

  const y = d3.scaleLinear()
    .domain(d3.extent(dataArray.filter(d => d.Date && d.Total), d => d.Total))
    .range([0, 800]);

  // Create x and y axes
const xAxis = d3.axisBottom(x).tickFormat(d3.timeFormat("%m/%d"));
  const yAxis = d3.axisLeft(y);

  // Create line generator
const line = d3.line()
    .x(d => x(new Date(d.Date)))
    .y(d => y(d.Total));

  // Append SVG
const svg = d3.select("#chart")
    .append("svg")
    .attr("width", 800)
    .attr("height", 800);

  // Append x and y axes
svg.append("g")
    .attr("transform", "translate(0," + 400 + ")")
    .call(xAxis);

  svg.append("g")
    .attr("transform", "translate(0,0)")
    .call(yAxis);

  // Append line
svg.append("path")
    .datum(dataArray)
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line);
});

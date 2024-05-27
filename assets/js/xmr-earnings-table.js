d3.csv("/data/xmr-earnings.csv").then(data => {
  // data is an array of objects, each representing a row from the CSV file

const table = d3.select("#csv-data").append("table");

const thead = table.append("thead");
const tbody = table.append("tbody");

thead.append("tr")
  .selectAll("th")
  .data(data[0]) // Assuming the first row contains the headers
  .enter()
  .append("th")
  .text(columnName => columnName);

tbody.selectAll("tr")
  .data(data.slice(1)) // Slice the data to skip the first row (headers)
  .enter()
  .append("tr")
  .selectAll("td")
  .data(row => Object.values(row))
  .enter()
  .append("td")
  .text(value => value);

});

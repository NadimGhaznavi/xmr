document.addEventListener('DOMContentLoaded', function(
) {
  var options = {
    chart: {
      type: 'line'
},
    series: [{
      name: 'X',
      data: [] // Will be populated with X data
}, {
      name: 'R',
      data: [] // Will be populated with R data
}],
    xaxis: {
      categories: [] // Will be populated with your custom categories
}
  }

  var chart = new ApexCharts(document.querySelector("#chart"), options);

  chart.render();

  d3.csv("/data/xmr-earnings.csv", function(data) {
    // Convert data to X and R arrays
const xData = data.map(d => d.Date);
    const rData = [];
    for (let i = 0; i < data.length - 1; i++) {
      rData.push(data[i + 1].Total - data[i].Total);
    }

    // Extract categories from CSV data
const categories = data.map(d => d.Date);

    // Update the chart series data and redraw the chart
chart.updateSeries([{
      name: 'X',
      data: xData
    }, {
      name: 'R',
      data: rData
    }]);
    chart.updateOptions({
      xaxis: {
        categories: categories
      }
    });
  });
});

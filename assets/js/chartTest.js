document.addEventListener('DOMContentLoaded', function() {
  var options = {
    chart: {
      type: 'line'
    },
    series: [
      {
        name: 'Total',
        data: []
      }
    ],
    xaxis: {
      categories: []
    }
  }
}

var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);

chart.render()

d3.csv("/_data/xmr-earnings.csv", function(data) {
  const dateData = data.map(d => d.Date);
  const totalData = data.map(d => d.Total);

  chart.updateSeries(
    [
      {
        name: 'Total',
        data: totalData
      }
    ]
  );
  
  chart.updateOptions(
    {
      xaxis: {
        categories: dateData
      }
    }
  );
}
ddEventListener('DOMContentLoaded', function(
) {
  var options = {
    chart: {
      type: 'line'
},
    series: [{
      name: 'Date',
      data: []
    }, {
      name: 'Total',
      data: []
    }],
    xaxis: {
      categories: []
    }
  }

  var chart = new ApexCharts(document.querySelector("#chart"), options);

  chart.render();

  d3.csv("/data/xmr-earnings.csv", function(data) {
    const dateData = data.map(d => d.Date);
    const totalData = data.map(d => d.Total);

    chart.updateSeries([{
      name: 'Date',
      data: dateData
    }, {
      name: 'Total',
      data: totalData
    }]);
    chart.updateOptions({
      xaxis: {
        categories: dateData
      }
    });
  });
});

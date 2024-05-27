document.addEventListener('DOMContentLoaded', function(
) {
  var options = {
    chart: {
      type: 'line',
    },
    series: [{
      name: 'Total',
      type: 'area',
      stroke: {
        curve: 'smooth',
        width: 2
      },
      fill: {
        colors: {['#0047b3', '#7acbee' ]},
        opacity: 0.5,
        type: 'solid'
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

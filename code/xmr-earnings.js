document.addEventListener('DOMContentLoaded', function(
) {
  var options = {
    chart: {
      type: 'area',
    },
    series: [
      {
        name: 'Total XMR Earned',
        date: []
      }
    ],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1, // Set intensity of the gradient shading
        opacityFrom: 0.2, // Gradient opacity at the start
        opacityTo: 0.8, // Gradient opacity at the end
        stops: [0, 25, 100]
      }
    },
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

document.addEventListener('DOMContentLoaded', function(
) {
  var options = {
    chart: {
      height: 500,
      type: 'area',
    },
    dataLabels: {
      enabled: false
    },
    series: [
      {
        name: 'Total XMR Earned',
        date: [] // Initialize to an empty array
      }
    ],
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1, // Set intensity of the gradient shading
        opacityFrom: 0.7, // Gradient opacity at the start
        opacityTo: 0.9, // Gradient opacity at the end
        stops: [0, 90, 100]
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
      name: 'Total XMR Earned',
      data: totalData
    }]);
    chart.updateOptions({
      xaxis: {
        categories: dateData
      }
    });
  });
});

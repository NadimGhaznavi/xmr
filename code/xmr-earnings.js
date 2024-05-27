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
	type: 'gradient',
	gradient: {
          type: 'vertical', // Set gradient direction (vertical, horizontal, etc.)
          shadeIntensity: 0.5, // Set intensity of the gradient shading
          inverseColors: true, // Reverse gradient colors if desired
          opacityFrom: 0.5, // Gradient opacity at the start
          opacityTo: 0.5, // Gradient opacity at the end
          colorStops: [ // Define custom color stops for the gradient
            { offset: 0, color: '#0047b3' }, // Color at 0%
            { offset: 100, color: '#7acbee' } // Color at 100%
          ]
	}
      },
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

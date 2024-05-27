document.addEventListener('DOMContentLoaded', function(
) {
  var areaOptions = {
    chart: {
      id: "areaChart",
      type: 'area',
      height: 500,
      foreColor: "#ccc",
      toolbar: {
        autoSelected: "pan",
        show: false
      }
    },
    colors: ["#00baec"],
    stroke: {
      width: 3
    },
    grid: {
      borderColor: "#555",
      clipMarkers: false,
      yaxis: {
        lines: {
          show: false
        }
      }
    },
    dataLabels: {
      enabled: false
    },
    fill: {
      gradient: {
        enabled: true,
        opacityFrom: 0.55,
        opacityTo: 0
      }
    },
    markers: {
      size: 5,
      colors: ["#000524"],
      strokeColor: "#00baec",
      strokeWidth: 3
    },
    series: [
      {
        name: 'Total XMR Earned',
        data: [] // Initialize to an empty array
      }
    ],
    tooltip: {
      theme: "dark"
    },
    xaxis: {
      type: "datetime",
      categories: []
    },
    yaxis: {
      min: 0,
      tickAmount: 4
    }
  };

  d3.csv("/_data/xmr-earnings.csv", function(data) {
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
    
  var areaChart = new ApexCharts(document.querySelector("#chart -area"), areaOptions);

  areaChart.render();

var barOptions = {
  chart: {
    id: 'barChart',
    height: 250,
    type: 'bar',
    foreColor: "#ccc",
    brush: {
      target: "areaChart",
      enabled: true
    },
    selection: {
      enabled: true,
      fill: {
        color: "#fff",
        opacity: 0.4
      },
      xaxis: {
        min: new Date("21 March 2024 00:00:00").getTime(),
        max: new Date("27 May 2024 23:59:59").getTime()
      }
    }
  },
  colors: ["#ff0080"],
  series: [
    {
      data: []
    }
  ],
  stroke: {
    width: 2
  },
  grid: {
    borderColor: "#444"
  },
  markers: {
    size: 0
  },
  xaxis: {
    type: "datetime",
    tooltip: {
      enabled: false
    }
  },
  yaxis: {
    tickAmount: 2
  }
};

var barChart = new ApexCharts(document.querySelector("#chart -bar"), barOptions);

barChart.render()

});

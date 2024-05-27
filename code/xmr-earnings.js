d3.csv("/data/xmr-earnings.csv", function(data) {
  // Convert data to X and R arrays for ApexCharts
const xData = data.map(d => d.xValue); // Replace 'xValue' with your X data field name
const rData = [];
  for (let i = 0; i < data.length - 1; i++) {
    rData.push(data[i + 1].xValue - data[i].xValue);
  }

  // Now create the ApexCharts XmR chart
let chart = new ApexCharts(document.querySelector("#chart"), {
    series: [{
      name: 'X',
      data: xData
    }, {
      name: 'R',
      data: rData
    }],
    chart: {
      type: 'line',
      height: 350
},
    plotOptions: {
      line: {
        color: ['#FF6600', '#00796B']
      }
    },
    dataLabels: {
      enabled: true,
      color: '#000000'
},
    stroke: {
      width: [2, 2],
      curve: 'smooth'
},
    fill: {
      opacity: [0, 0]
    },
    markers: {
      size: 0
},
    xaxis: {
      type: 'datetime'
}
  });

  chart.render();
});

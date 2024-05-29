const csvUrl = '/data/xmr-earnings.csv';
const dateData = [];
const totalData = [];

Papa.parse(csvUrl, {
  download: true,
  header: true,
  delimiter: ",",
  complete: data => {
    data.data.forEach(row => {
      const date = row['Date'];
      const total = row['Total'];

      dateData.push(date);
      totalData.push(Number(total));
    });

    const options = {
      chart: {
        height: 280,
        type: "area"
      },
      dataLabels: {
        enabled: false
      },
      series: [{
        name: 'Total',
        data: totalData
      }],
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.7,
          opacityTo: 0.9,
          stops: [0, 90, 100]
        }
      },
      xaxis: {
        categories: [ 
          dateData
        ]
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
    areaChart.render();
  }
});

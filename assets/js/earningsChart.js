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
      xaxis: {
        categories: dateData
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
    areaChart.render();
  }
});

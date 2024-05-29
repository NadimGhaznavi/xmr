document.addEventListener('DOMContentLoaded', function() {
  const dateData = [];
  const totalData = [];

  const loadCSV = async () => {
    const response = await fetch("/data/xmr-earnings.csv");
    const text = await response.text();

    const parsedData = Papa.parse(text, {
      header: true,
      delimiter: ","
    });

    parsedData.data.forEach(data => {
      const date = data['Date'];
      const total = data['Total'];

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
      },
      stroke: {
        width: 2
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
    areaChart.render();
  };

  loadCSV();
});

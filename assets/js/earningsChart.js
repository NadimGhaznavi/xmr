document.addEventListener('DOMContentLoaded', function() {

  const dateData = [];
  const totalData = [];

  d3.csv("/data/xmr-earnings.csv", function(csvData) {
    csvData.forEach(function(data) {
      const date = csvData['Date'];
      const total = csvData['Total'];

      console.log("date: ", date);
      console.log("total: ", total);

      dateData.push(date);
      totalData.push(Number(total));

      console.log("dateData: ", dateData);
      console.log("totalData: ", totalData);
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
  }, d3.autoType);
  
});

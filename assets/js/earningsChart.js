document.addEventListener('DOMContentLoaded', function() {

  const dateData = [];
  const totalData = [];

  d3.csv("/data/xmr-earnings.csv", function(csvData) {
    const { Date, Total } = csvData;

    dateData.push(Date);
    totalData.push(Number(Total));

    console.log("dateData: ", dateData);
    console.log("totalData: ", totalData);

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
  });  
});

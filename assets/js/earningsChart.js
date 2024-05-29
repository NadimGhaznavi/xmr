document.addEventListener('DOMContentLoaded', function() {

  var options = {
    chart: {
      height: 280,
      type: "area"
    },
    dataLabels: {
      enabled: false
    },
    series: [],
    xaxis: {
      categories: []
    }
  };

  var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);

  d3.csv("/data/xmr-earnings.csv", function(csvData) {
    const { Date, Total } = csvData;

    const dateData = [];
    const totalData = [];
  
    dateData.push(Date);
    totalData.push(Number(Total));

    areaChart.updateOptions({
      series: [{
        name: 'Total',
        data: totalData
      }],
      xaxis: {
        categories: dateData
      }      
    });
  
    areaChart.render();  
  });  
});

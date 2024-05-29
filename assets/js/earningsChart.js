document.addEventListener('DOMContentLoaded', function() {

  var options = {
    chart: {
      height: 280,
      type: "area"
    },
    dataLabels: {
      enabled: false
    },
    series: [
      {
        name: "Total",
        data: []
      }
    ],
    xaxis: {
      categories: []
    }
  };

  var areaChart = new Apex(document.querySelector("#areaChart"), options);

  const dateData = [];
  const totalData = [];

  d3.csv("/data/xmr-earnings.csv", function(csvData) {
    
    const { Date, Total } = csvData;
    dateData.push(Date);
    totalData.push(Number(Total));

    areaChart.updateSeries([{
      name: 'Total',
      data: totalData
    }]);
  
    areaChart.updateOptions({
      xaxis: {
      categories: dateData
    }});  
  
    areaChart.render();  

  });
  
});

//document.addEventListener('DOMContentLoaded', function() {
  const dateData = [];
  const totalData = [];

 // const loadCSV = async () => {
 //   const response = await fetch("/data/xmr-earnings.csv");
  //  const text = await response.text();

  const response = fetch("/data/xmr-earnings.csv");
  const text = response.text();

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
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.7,
          opacityTo: 0.9,
          stops: [0, 90, 100]
        }
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
    areaChart.render();
  //};
  //loadCSV();
  
//});

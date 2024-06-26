const csvUrl = '/data/xmr-earnings.csv';
const dateData = [];
const totalData = [];

Papa.parse(csvUrl, {
  download: true,
  header: true,
  delimiter: ",",
  complete: data => {
    data.data.forEach(row => {
      const dateString = row['Date'];
      const total = row['Total'];

      // Check for missing or invalid data
      if (!dateString || !total || isNaN(Number(total))) {
        console.log('Invalid or missing data found. Skipping this row.');
        return;
      }

      // Parse the date string and convert it to a timestamp
      const date = new Date(dateString).getTime();

      dateData.push(date);
      totalData.push(Number(total));
    });
    
    const options = {
      chart: {
        height: 500,
        type: "area"
      },
      dataLabels: {
        enabled: false
      },
      series: [{
        name: 'Total',
        data: totalData.map((total, index) => ({ x: dateData[index], y: total })),
        fill: true
      }],
      xaxis: {
        type: 'datetime'
      },
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.7,
          opacityTo: 0.9,
          stops: [0, 90, 100]
        }
      },
      stroke: {
        curve: 'smooth'
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
    areaChart.render();
  }
});


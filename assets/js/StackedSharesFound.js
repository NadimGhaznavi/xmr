const csvUrl = '/data/stacked_shares_found.csv';
const dateData = [];
const totalKermitData = [];
const totalSallyData = [];
const totalParisData = [];
const totalMaiaData = [];
const totalBingoData = [];
const totalBratData = [];
const totalPhoebeData = [];

Papa.parse(csvUrl, {
  download: true,
  header: true,
  delimiter: ",",
  complete: data => {
    data.data.forEach(row => {
      const dateString = row['Date'];
      const kermit = row['Kermit'];
      const sally = row['Sally'];
      const paris = row['Paris'];
      const maia = row['Maia'];
      const bingo = row['Bingo'];
      const brat = row['Brat'];
      const phoebe = row['Phoebe'];


      // Check for missing or invalid data
      //if (!dateString || isNaN(value)) {
      //  console.log('Invalid or missing data found. Skipping this row.');
      //  return;
      //}

      // Parse the date string and convert it to a timestamp
      const date = new Date(dateString).getTime();

      dateData.push(date);
      //totalData.push(Number(total));
      totalKermitData.push({ x: date, y: kermit });
      totalSallyData.push({ x: date, y: sally });
      totalParisData.push({ x: date, y: paris });
      totalMaiaData.push({ x: date, y: maia });
      totalBingoData.push({ x: date, y: bingo });
      totalBratData.push({ x: date, y: brat });
      totalPhoebeData.push({ x: date, y: phoebe });
    });
    
    const areaOptions = {
      chart: {
        id: "barChart",
        stacked: true,
        type: "bar",
        height: 275,
        foreColor: "#ccc",
        toolbar: {
          autoSelected: "pan",
          show: false
        }
      },
      colors: ["#00baec","#ffbaec","#01f9c6","#808000","#ffffcc","#fef250","#644117"],
      stroke: {
	    curve: 'stepline',
        width: 3
      },
      grid: {
        borderColor: "#555",
        clipMarkers: false,
        yaxis: {
          lines: {
            show: false
          }
        }
      },
      dataLabels: {
        enabled: false
      },
      fill: {
        gradient: {
          enabled: true,
          opacityFrom: 0.55,
          opacityTo: 0,
        }
      },
      markers: {
        size: 0,
        colors: ["#000524"],
        strokeColor: "#00baec",
        strokeWidth: 1
      },
      series: [
        {
          name: "Kermit",
          data: totalKermitData
        },
        {
          name: "Sally",
          data: totalSallyData
        },
        {
          name: "Paris",
          data: totalParisData
        },
        {
          name: "Maia",
          data: totalMaiaData
        },
        {
          name: "Bingo",
          data: totalBingoData
        },
        {
          name: "Brat",
          data: totalBratData
        },
        {
          name: "Phoebe",
          data: totalPhoebeData
        },
      ],
      tooltip: {
        theme: "dark"
      },
      title: {
	    text: 'Shares Found',
	    align: 'left'
      },
      xaxis: {
        type: "datetime"
      },
      yaxis: {
        min: 0
      }
    };

    var areaChart = new ApexCharts(document.querySelector("#areaChart"), areaOptions);
    areaChart.render();

  }});

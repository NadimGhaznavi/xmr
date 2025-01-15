const csvUrl = '/data/blocks_found.csv';
const dateData = [];
const totalData = [];

Papa.parse(csvUrl, {
  download: true,
  header: true,
  delimiter: ",",
  complete: data => {
    data.data.forEach(row => {
      const dateString = row['Date'];
      const value = row['Blocks Found'];

      // Check for missing or invalid data
      if (!dateString || isNaN(value)) {
        console.log('Invalid or missing data found. Skipping this row.');
        return;
      }

      // Parse the date string and convert it to a timestamp
      const date = new Date(dateString).getTime();

      dateData.push(date);
      //totalData.push(Number(total));
      totalData.push({ x: date, y: value });

    });
    
    const areaOptions = {
      chart: {
        id: "barChart",
        type: "bar",
        height: 275,
        foreColor: "#ccc",
        toolbar: {
          autoSelected: "pan",
          show: false
        }
      },
      colors: ["#00baec"],
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
          name: "Blocks Found",
          data: totalData
        }
      ],
      tooltip: {
        theme: "dark"
      },
      title: {
	text: 'Blocks Found',
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

    var barOptions = {
      chart: {
        id: "areaChart",
        height: 100,
        type: "bar",
        foreColor: "#ccc",
        brush: {
          target: "barChart",
          enabled: true
        },
        selection: {
          enabled: true,
          fill: {
            color: "#fff",
            opacity: 0.4
          },
          xaxis: {
            min: new Date("06 November 2024 00:00:00").getTime(),
            max: new Date("16 November 2024 23:59:59").getTime()
          }
        }
      },
      colors: ["#FF0080"],
      series: [
        {
          data: totalData
        }
      ],
      stroke: {
        width: 2
      },
      grid: {
        borderColor: "#444"
      },
      markers: {
        size: 0
      },
      xaxis: {
        type: "datetime",
        tooltip: {
          enabled: false
        }
      },
    };

    var barChart = new ApexCharts(document.querySelector("#barChart"), barOptions);
    barChart.render();

  }});


const csvUrl = '/data/xmr-earnings.csv';
const dateData = [];
const totalData = [];

const loadAndParseCSV = () => {
  const response = fetch(csvUrl);
  const text = response.text();

  const parsedData = Papa.parse(text, {
    header: true,
    delimiter: ",",
    complete: () => {
      parsedData.data.forEach(data => {
        const date = data['Date'];
        const total = data['Total'];

        dateData.push(date);
        totalData.push(Number(total));
      });
    }
  });
};

loadAndParseCSV();

var options = {
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
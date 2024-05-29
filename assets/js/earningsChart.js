const csvUrl = '/data/xmr-earnings.csv';
const dateData = [];
const totalData = [];

const fetchAndParseCSV = async () => {
  const response = await fetch(csvUrl);
  const text = await response.text();

  return Papa.parse(text, {
    header: true,
    delimiter: ","
  });
};

const loadCSV = async () => {
  const parsedData = await fetchAndParseCSV();

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
  };

  var areaChart = new ApexCharts(document.querySelector("#areaChart"), options);
  areaChart.render();

};
  
loadCSV();

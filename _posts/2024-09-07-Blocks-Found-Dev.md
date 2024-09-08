---
layout: post
title: Blocks Found Dev
date: 2024-09-07
---
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="/assets/js/BlocksFoundDev.js"></script>

THIS PAGE IS POPULATED WITH DUMMY DATA FOR DEVELOPMENT.

The chart below shows the Monero XMR that the mining farm has earned. My code monitors the P2Pool log continuously and loads *block found* events into a MongoDB backend. The code then calls a function that extracts all *block found* events from MongoDB and transforms the data into a CSV format. The code then calls a script to push the CSV file to this GitHub pages site. Finally, this *GitHub Formatted Markdown* page displays the information using a JavaScript library, ApexChart, to do the actual chart rendering.

<div id="wrapper">
  <div id="areaChart">
  </div>
  <div id="barChart">
  </div>
 </div>


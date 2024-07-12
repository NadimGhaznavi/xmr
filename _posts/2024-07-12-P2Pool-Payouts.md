---
layout: post
title: P2Pool Payouts
date: 2024-07-12
---
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="/assets/js/P2PoolPayouts.js"></script>

The chart below shows the Monero XMR that the mining farm has earned. The data is mined out of the P2Pool log continuouslyand loaded into a MongoDb backend as it arrives. Another process monitors the size of the MongoDb collection that houses the data. When new data arrives it generates a new CSV file to refect that event. The CSV file is uploaded to GitHub pages and displayed on this GitHub Jekyll page using GitHub Formatted Markdown and a JavaScript library, ApexChart, to do the actual chart rendering.

<div id="wrapper">
  <div id="areaChart">
  </div>
  <div id="barChart">
  </div>
 </div>


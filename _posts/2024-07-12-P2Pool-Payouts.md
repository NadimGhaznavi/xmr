---
layout: post
title: P2Pool Payouts
date: 2024-09-02
---
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="/assets/js/P2PoolPayouts.js"></script>

The chart below shows the Monero XMR that the mining farm has earned. The data is mined out of the P2Pool log continuouslyand loaded into a MongoDb backend as it arrives. It then calls a function that takes the periodic XMR payouts and transforms the data into a CSV format with daily totals. The CSV file is pushed to GitHub pages and this GitHub Formatted markdown page displays the information using a JavaScript library, ApexChart, to do the actual chart rendering.

<div id="wrapper">
  <div id="areaChart">
  </div>
  <div id="barChart">
  </div>
 </div>


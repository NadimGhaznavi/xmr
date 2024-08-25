---
layout: post
title: XMR Earnings
date: 2024-08-19
---
<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.0/papaparse.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="/assets/js/fancyEarningsChart.js"></script>

The chart below shows the Monero XMR that the mining farm has earned. 


<div id="wrapper">
  <div id="areaChart">
  </div>
  <div id="barChart">
  </div>
 </div>

The spike on May 17th, 2024 was when the wallet associated with the local P2Pool daemon won the [XMR vs. Beast](https://xmrvsbeast.com/p2pool/) lottery. No cost to enter, just needed to find a share on the Mini Sidechain to qualify.

The increase in the slope of the graph, showing an increase in profitability was due to me using some free credits in the cloud. I created and deployed xmrig in various container configurations to explore different configurations of containers in the cloud. It also made it clear that unless XMR's market value increases dramatically, it's not profitable to rent cloud resources for mining.

The spike on August 19, 2024 was another win in the [XMR vs. Beast](https://xmrvsbeast.com/p2pool/) lottery. I should note that the Monero mining community is relatively small. Looking through the P2Pool log data, I noticed at one point that there were only about 4,000 distinct wallet addresses. So winning twice isn't entirely implausible.

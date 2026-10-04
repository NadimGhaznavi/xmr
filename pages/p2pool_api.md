---
title: P2Pool API
layout: home
author_profile: true
---

![XMR Logo](/pages/images/xmr_logo.png)

---

# Introduction

P2Pool exposes a read-only API. This page documents what is exposed.

```
root@bama:/opt/Db4E/p2pool/Bama/api # find .
.
./stats_mod
./local
./local/console
./local/stratum
./local/p2p
./local/merge_mining
./network
./network/stats
./pool
./pool/blocks
./pool/stats
```

---

# stats_mod

```
"config":
  {"ports":[
    {"port":3333,
    "tls":false}],
  "fee":0,"minPaymentThreshold":300000000},
  "network":{"height":3741343},
  "pool":{
    "stats":{"lastBlockFound":"1786870529000"},
    "blocks":["0d3c...f538:1786870529","3741303"],
    "miners":1300,
    "hashrate":24145685,
    "roundHashes":97488779653}
```

---

# local/console

```
{
    "mode":"pipe",
    "tcp_port":57751,
    "cookie":"J ($6VsMj3(u`[1)_TTZ"}
```

---

# local/merge_mining

```
{"chains":[]}
```

---

# local/p2p

```
{
    "connections":32,
    "incoming_connections":16,
    "peer_list_size":1242,
    "peers":[
        "I,12048,79,P2Pool v4.17.1,14538802,108.81.104.45:55961",
        "I,25066,121,P2Pool v4.17.1,14538802,82.135.85.191:4825",
        "I,25800,84,P2Pool v4.18,14538802,38.240.225.59:54976",
        "I,26576,51,P2Pool v4.17.1,14538802,75.166.62.84:46504",
           .
           .
           .
        "O,395120,106,P2Pool v4.17.1,14538802,81.243.196.208:37888",
        "O,395120,126,P2Pool v4.17.1,14538802,82.65.127.152:37888"],
        "uptime":395124,
        "zmq_last_active":5}
```

---

# local/stratum

```
{
    "hashrate_15m":11800,
    "hashrate_1h":12297,
    "hashrate_24h":11196,
    "total_hashes":4303442499,
    "total_stratum_shares":100524,
    "last_share_found_time":1786799991,
    "shares_found":15,
    "shares_failed":0,
    "average_effort":94.232,
    "current_effort":346.807,
    "connections":8,
    "incoming_connections":8,
    "block_reward_share_percent":0.000,"wallet":"48wY7nYBsQNSw7v4LjoNnvCtk1Y6GLNVmePGrW82gVhYhQtWJFHi6U6G3X5d7JN2ucajU9SeBcijET8ZzKWYwC3z3Y6fDEG",
    "workers":[
        "192.168.0.122:38370,133709,48809,1626,islands",
        "192.168.0.27:49724,262800,33788,1103,paris",
        "192.168.0.86:46706,394977,45424,1514,sally",
        "192.168.0.220:48728,394977,29158,984,phoebe",
        "192.168.0.244:37304,394977,5591,183,bingo",
        "192.168.0.239:45444,394977,81553,2662,wintermute",
        "127.0.0.1:37408,394978,67970,2265,bama",
        "192.168.0.176:59390,394978,47612,1587,kermit"]}
```

---

# network/stats

```
{
    "difficulty":668465817163,
    "hash":"9bbd7ae39213a29a15562af0d757fe5ddb3389ae15a4acfabd15e157af85dbf5",
    "height":3741351,
    "reward":600000000000,
    "timestamp":1786875269}
```

---

# pool/blocks

```
[
    {"height":3741303,"hash":"0d3c5ed4ed37f7c18e04f767e0f5b2fdfd0f226ce20638a16f45d7a1fc3cf538","difficulty":685073918844,"totalHashes":2390381275142489,"ts":1786870529},
    {"height":3740968,"hash":"b975039d73d4c5ea38e157b7666b8d5ebfc60cc2acb28bec7c728c275672cd26","difficulty":650187505362,"totalHashes":2389458150732322,"ts":1786831773},
    {"height":3740737,"hash":"de45ac4c6a6dacef990e46ae179f7bdd9c824c3896a37238c06ee339dd4a632a","difficulty":668818225059,"totalHashes":2388758035234167,"ts":1786803454},
    {"height":3740716,"hash":"62a88682ab5eaf60a88c60974380788234bdc71da6664d1352b0a7e9ad521495","difficulty":652318180803,"totalHashes":2388703168697358,"ts":1786801419},
    {"height":3740688,"hash":"1514ca45bf767403a943c0baf994ab46f6a43a31ca6db4122beb79ff8b1e621a","difficulty":644814181025,"totalHashes":2388633054308062,"ts":1786798428},
       .
       .
       .
    {"height":3731242,"hash":"6b0fe44a0fe8a596163fd9a168b18c1cecac2f3adafe17ec18c6c8cae49ba7ba","difficulty":723787332841,"totalHashes":2362050851250212,"ts":1785661411},
    {"height":3731048,"hash":"9744a4550eb08edd41d30ee6ffa261a3b6f503a43a8fb696423685a71ed4fed3","difficulty":748488027803,"totalHashes":2361460928145642,"ts":1785633984}]
```

---

# pool/stats

```
{"pool_list":["pplns"],
"pool_statistics":{
    "hashRate":24070668,
    "miners":1302,
    "totalHashes":2390506350542238,
    "lastBlockFoundTime":1786870529,
    "lastBlockFound":3741303,
    "totalBlocksFound":43,
    "pplnsWeight":538884586335,
    "pplnsWindowSize":2160,
    "sidechainDifficulty":240706681,
    "sidechainHeight":14538847}}
```

---




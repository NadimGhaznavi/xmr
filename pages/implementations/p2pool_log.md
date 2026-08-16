---
title: P2Pool Log
layout: home
author_profile: true
---

![XMR Logo](/pages/images/xmr_logo.png)

---

# Introduction

P2Pool's log contains rich information when the `p2pool` process receives a `status` or `workers` command. Additionally, p2pool logs *share found*, *block found*, and *payout* events are logged. Example log entries are shown below.

---

# Example Status Log Lines

```
NOTICE  2026-08-16 10:34:27.6667 SideChain status
Monero node               = bama:RPC 19081:ZMQ 19083 (127.0.1.1)
Main chain height         = 3741362
Main chain hashrate       = 5.621 GH/s
Side chain ID             = mini
Side chain height         = 14538931
Side chain hashrate       = 24.846 MH/s
PPLNS window              = 2160 blocks (+58 uncles, 1 orphans)
PPLNS window duration     = 6h 1m 47s
Your wallet address       = 48wY7nYBsQNSw7v4LjoNnvCtk1Y6GLNVmePGrW82gVhYhQtWJFHi6U6G3X5d7JN2ucajU9SeBcijET8ZzKWYwC3z3Y6fDEG
Your shares               = 0 blocks (+0 uncles, 0 orphans)
Block reward share        = 0.000% (0.000000000000 XMR)
NOTICE  2026-08-16 10:34:27.6668 StratumServer status
Hashrate (15m est)   = 11.680 kH/s
Hashrate (1h  est)   = 11.592 kH/s
Hashrate (24h est)   = 11.184 kH/s
Stratum hashes       = 4319481325
Stratum shares       = 100883
P2Pool shares found  = 15
Average effort       = 94.232%
Current effort       = 346.074%
Connections          = 8 (8 incoming)
NOTICE  2026-08-16 10:34:27.6668 P2PServer status
Connections     = 32 (16 incoming, 0 onion, 0 I2P)
Peer list size  = 1258
Onion list size = 17
I2P list size   = 3
Uptime          = 4d 14h 6m 10s
NOTICE  2026-08-16 10:34:27.6668 Util no background jobs running
NOTICE  2026-08-16 10:34:27.6668 ConsoleCommands Node health: 10/10
```

---

# Example Workers Log Lines

```
NOTICE  2026-08-16 10:35:17.9896 StratumServer IP:port                    TLS    uptime              difficulty          hashrate       shares      name
NOTICE  2026-08-16 10:35:17.9896 StratumServer 192.168.0.122:38370        no     1d 13h 32m 26s      34981               1.166 kH/s     0/4488      islands
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.27:49724         no     3d 1h 23m 57s       29426               980 H/s        0/8800      paris
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.86:46706         no     4d 14h 6m 54s       39209               1.306 kH/s     2/13138     sally
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.220:48728        no     4d 14h 6m 54s       25807               860 H/s        2/13126     phoebe
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.244:37304        no     4d 14h 6m 54s       5074                169 H/s        0/13146     bingo
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.239:45444        no     4d 14h 6m 54s       81114               2.703 kH/s     5/13147     wintermute
NOTICE  2026-08-16 10:35:17.9897 StratumServer 127.0.0.1:37408            no     4d 14h 6m 55s       80635               2.687 kH/s     1/13145     bama
NOTICE  2026-08-16 10:35:17.9897 StratumServer 192.168.0.176:59390        no     4d 14h 6m 55s       58274               1.942 kH/s     5/13133     kermit
NOTICE  2026-08-16 10:35:17.9897 StratumServer Total: 8 workers
```

---

# Example Share Found Log Lines

```
NOTICE  2026-08-15 02:39:27.0078 StratumServer SHARE FOUND: mainchain height 3740394, sidechain height 14527878, diff 253920976, client 192.168.0.176:59390, user kermit, effort 162.474%
NOTICE  2026-08-15 04:02:09.3139 StratumServer SHARE FOUND: mainchain height 3740421, sidechain height 14528325, diff 259008279, client 192.168.0.239:45444, user wintermute, effort 21.576%
```

---

# Example Block Found Log Lines

```
NOTICE  2026-08-16 08:55:29.2002 P2Pool BLOCK FOUND: main chain block at height 3741303 was mined by someone else in this p2pool
```

---

# Example Payout Log Line

If there's a payout, then this event happens right after the *Block Found* event.


```
NOTICE  2026-08-15 14:17:34.9965 P2Pool Your wallet 48wY7nYBsQNSw7v4LjoNnvCtk1Y6GLNVmePGrW82gVhYhQtWJFHi6U6G3X5d7JN2ucajU9SeBcijET8ZzKWYwC3z3Y6fDEG got a payout of 0.000279287269 XMR in block 3740737
```

---

# Example No Payout Log Line

If there's no payout when a block is found, then this message appears.

```
NOTICE  2026-08-16 08:55:29.2008 P2Pool Your wallet 48wY7nYBsQNSw7v4LjoNnvCtk1Y6GLNVmePGrW82gVhYhQtWJFHi6U6G3X5d7JN2ucajU9SeBcijET8ZzKWYwC3z3Y6fDEG didn't get a payout in block 3741303 because you had no shares in PPLNS window
```

---

### 20211221 Visor Finance - Reentrancy

#### Lost: $8.2 million

Testing

```sh
forge test --contracts ./src/test/2021-12/Visor_exp.sol -vv
```

#### Contract

[Visor_exp.sol](../../src/test/2021-12/Visor_exp.sol)

#### Link reference

https://beosin.medium.com/two-vulnerabilities-in-one-function-the-analysis-of-visor-finance-exploit-a15735e2492

https://twitter.com/GammaStrategies/status/1473306777131405314

https://etherscan.io/tx/0x69272d8c84d67d1da2f6425b339192fa472898dce936f24818fda415c1c1ff3f

---

### 20231231 Channels - Price Manipulation

### Lost: ~$4.4K

```sh
forge test --contracts ./src/test/2023-12/Channels_exp.sol -vvv --evm-version shanghai
```
#### Contract

[Channels_exp.sol](../../src/test/2023-12/Channels_exp.sol)

### Link reference

https://app.blocksec.com/explorer/tx/bsc/0xcf729a9392b0960cd315d7d49f53640f000ca6b8a0bd91866af5821fdf36afc5

---
### 20221229 - JAY - Insufficient validation + Reentrancy

### Lost: ~15.32 ETH

Testing

```sh
forge test --contracts ./src/test/2022-12/JAY_exp.sol -vvv
```

#### Contract

[JAY_exp.sol](../../src/test/2022-12/JAY_exp.sol)

#### Link reference

https://twitter.com/BlockSecTeam/status/1608372475225866240

---

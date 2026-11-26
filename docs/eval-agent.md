# DSH agent 层独立评测（人格常驻效应）

> 与主仓的「skill 内容效应」评测（run1–3）**分开**。本评测只问：DSH 科研模式额外注入的"人格/纪律常驻"，在已有完整 skill 之上，是否再提升产出质量？

## 设计

- 底座：OpenCode + kimi-k3（DSH preset 的代理实现）。
- 两臂唯一变量 = 是否在 instructions 里**额外常驻人格摘要**：
  - arm-skill：instructions = [SKILL.md]
  - arm-agent：instructions = [persona.md, SKILL.md]
- 任务 T3：报告 Voyager 三个核心数字并标来源/核验状态（禁联网/禁子 agent，逼出"诚实分级"行为）。
- 评审：deepseek-v4-pro 盲评 head-to-head。

## 结果

| 臂 | D1–D5 | 总分 |
|---|---|---|
| skill | 5/5/5/5/5 | 25 |
| agent(+人格) | 5/4/5/4/4 | 23 |

盲评偏好 **skill**。人格常驻**没有带来质量增益**（完整 skill 已携带全部纪律）。

## 结论（诚实）

1. **preset/人格的价值 ≠ 质量**。它的卖点是"纪律保证在场、不漏触发"的**可靠性**，而非把产出写得更好。本评测证实质量上无额外增益。
2. 要证明可靠性价值，需另做**触发率/漏触发**对比（标准模式 vs 科研模式，在 skill 未被主动加载时纪律是否仍在），本评测未覆盖。
3. 局限：n=1 任务、单评审、opencode 代理而非真实 DSH preset；子 agent 查新导致长任务超时，故改用禁子 agent 的快任务。

## 复现

`eval-agent/`（arm-skill / arm-agent / tasks / results）。runner 需为每臂隔离 `XDG_DATA_HOME` 以避免 sqlite 锁。

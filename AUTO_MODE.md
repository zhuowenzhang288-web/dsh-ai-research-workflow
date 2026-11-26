# AUTO_MODE —— 让 workflow 循环起来（不写 agent，拼出来）

循环不靠发明，靠组合：**skill（方法论）+ goal（持续目标）+ schedule（定时触发）**。
本文件教你用现有 harness 的原生功能，把 ai-research-workflow 拼成自动研究循环。

---

## 一、三种模式

### 模式 A：DSH 全自动夜跑（推荐）

用 DSH 的 `/goal` 开持续目标 + `schedule_create` 定时检查点：

```
/goal 按 ai-research-workflow §4.2.1 造现象流程在 [方向] 跑 8 轮，
每轮 200 runs / ≤60s。全程遵守：
① 预注册落盘后再看数据；② 异常四关判定；
③ experiment_log.py 记 keep/discard/crash；
④ funnel.py narrow-watch 触发预警即换方向并汇报；
⑤ 每轮结束写检查点汇报（做了什么/新发现/下一步）。
门前动作降级为「记入 PENDING_APPROVAL.md + 继续循环」，
硬停止条件：连续 3 轮无过四关异常 或 预算超限。
```

再建一个 30 分钟的 schedule 提醒 agent 输出检查点进度（防沉默）。

### 模式 B：半自动（每天推进一轮）

系统 cron / DSH schedule 每天触发一次：

```
读 funnel.tsv + results.tsv + claim 清单（不靠会话记忆）
→ 按 SKILL.md 路由表决定本轮动作
→ 执行一轮 → 更新 artifact → 写检查点汇报
```

### 模式 C：单次长会话

不开 goal，直接一个长会话跑完一个阶段（适合造现象一轮游）。

---

## 二、循环协议（每轮固定 6 动作）

1. **读 artifact**：漏斗 / 实验日志 / claim 清单——从文件读，不靠会话记忆（§0 原则 2）
2. **跑本轮**：按 §4.1 纪律（固定预算、基线先行、评测只读）
3. **判定**：异常过四关？→ 是则进 §2 查新；否则记 discard
4. **防窄化**：`funnel.py narrow-watch` → 触发预警必须换方向，不许原地钻缝
5. **写检查点**：本轮做了什么｜新发现（带来源）｜下一步
6. **留痕**：所有决策写入日志文件

## 三、自动模式下的门控降级（重要）

§4.1.1 的"门前停人"在自动循环中降级：

| 门前的门 | 自动模式处理 |
|---|---|
| 查新未通过 | 淘汰入漏斗，**继续循环**（换个候选） |
| 用户未确认 IDEA_REPORT | 记入 `PENDING_APPROVAL.md`，**循环继续干别的**（跳到下一个候选） |
| 扩大规模 / 改评测 / 加依赖 | 记入 `PENDING_APPROVAL.md` + 通知，**不执行** |
| 投稿出终稿 | **永远停**——这个门不降级 |

**硬停止条件**（任一触发即退出循环并汇报）：
- 连续 3 轮无过四关的异常（§4.2.1 退出条件）
- 预算超限（GPU·h / token / 钱）
- `audit_chain.py` 任一 FAIL 层
- 用户手动打断

## 四、各平台拼法

| 平台 | goal | schedule | 备注 |
|---|---|---|---|
| **DeepSeek Harness** | `/goal` 命令 | `schedule_create` 工具 | 三件套最全，推荐 |
| **Claude Code** | 项目 CLAUDE.md 写目标段 | 系统 cron 调 `claude -p` | 每次会话读 CLAUDE.md 续上状态 |
| **Cursor** | background agent 指令 | 定期 prompt | 适合模式 B |
| **opencode** | `opencode run` 脚本 | cron | 无状态，全靠文件 |

## 五、诚实局限

- **无流式汇报**：工具层 subagent 跑完才返回，"实时" = 检查点制（§0 已写明）
- **状态全靠文件**：跨会话恢复的前提是每轮都落盘——别把状态留在对话里
- **幻觉防线 = 脚本**：自动模式下无人盯梢，每轮结束**必须**跑
  `verify-results`（数值锚点）和 `verify_citations`（引用核验），FAIL 即停
- **judge 有知识截止偏差**（我们自己评测发现的）：别让模型当事实裁判，裁判是脚本

<div align="center">

# 🕵️ 格物 · GEWU

**DSH 原生科研 agent** —— 格物致知：先接触现象，再抵达知识。

真相只有一个，证据说了算；先看见现象，再相信结论。

[![License: MIT](https://img.shields.io/badge/License-MIT-FDE68A.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.0-DC2626.svg)](../../releases)

![架构图](docs/architecture.svg)

</div>

---

## 这是什么

「格物」是把 [ai-research-workflow](https://github.com/zhuowenzhang288-web/ai-research-workflow) 方法论**完整融合进 DeepSeek Harness** 的科研 agent 产品，不是单个 skill 插件。它一次给你四件：

| 组件 | 内容 | 作用 |
|---|---|---|
| **skill** | `assets/ai-research-workflow/`（SKILL.md + 6 脚本） | 方法论 + 可执行工具 |
| **科研模式 preset** | `research-preset/` | 选模式即成科研 agent，纪律烧进系统提示 |
| **人格** | 「格物」科研侦探 | 好奇但克制、证据至上、把失败当线索 |
| **自动循环** | 见主仓 AUTO_MODE.md | goal + schedule 拼出无人值守循环 |

> 引擎（模型 + harness）由 DSH 提供；格物装进去的是**技能、经验、上下文、人格**。

## 安装

```bash
# skill + 工具
install_bundle /path/to/gewu
# 科研模式（agent preset）
install_bundle /path/to/gewu/research-preset
```

装好后新开 session 选「科研模式」，迎接你的就是格物。

## 跨平台

格物的方法论本体（SKILL.md + scripts）不绑定 DSH，Claude Code / Codex / Cursor / opencode 均可用，见主仓 [ai-research-workflow](https://github.com/zhuowenzhang288-web/ai-research-workflow)。本仓是它的 **DSH 完整融合版**。

## License

MIT

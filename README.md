# dsh-ai-research-workflow

> 这是 [ai-research-workflow](https://github.com/zhuowenzhang288-web/ai-research-workflow) 的 **DeepSeek Harness 可安装版（bundle）**。
> 想看完整介绍、痛点、多平台用法，去主仓 👉 —— 本仓只提供 DSH 一键安装。

一个 DSH **skill bundle**：把「现象驱动的科研工作流」skill（含 4 个能力脚本）打包成可一键安装的插件。

## 是什么

`ai-research-workflow` 是一套方向无关的科研工作流 skill，核心是**现象驱动**：

> 不凭空想 idea——先在小系统跑海量小实验找规律，由规律反推 idea，再查新、再上卡。

带 4 个纯 Python 标准库脚本：查新（`novelty_check.py`）、实验日志（`experiment_log.py`）、引用核验（`verify_citations.py`）、五层审计（`audit_chain.py`）。

![架构图](docs/architecture.svg)

> 完整介绍与多平台用法见主仓 [ai-research-workflow](https://github.com/zhuowenzhang288-web/ai-research-workflow)。

## 安装

```bash
# 在 DSH 里，通过 Plugin Manager / agent 工具
install_bundle dsh-ai-research-workflow
```

或本地目录 link：

```bash
install_bundle /path/to/dsh-ai-research-workflow
```

装好后，新 session 里 agent 就能按需加载 `ai-research-workflow` skill，脚本在 skill 目录的 `scripts/` 下。

**建议再加一层保险**：把主仓的 `AGENTS.md`（33 行核心纪律）放到你的项目根目录——DSH 的 `dsh-agent-instructions` 插件会**每次请求自动注入**，解决"skill 按需加载可能漏触发"的问题。

## 结构

```
package.json                # dsh.bundle.patch 声明
cordis.patch.yml            # mount 本插件
index.js                    # 在 ctx.skills 上注册 skill（仿 dsh-skill-office）
assets/ai-research-workflow/
├── SKILL.md                # skill 本体（384 行）
└── scripts/                # 4 个能力脚本
locale/en.json, zh.json     # 标题与描述
```

## 说明

- 依赖 DSH 的 skill registry（`@deepseek-ai/dsh-skill`），base 配置已自带。
- skill 本体维护在 `assets/ai-research-workflow/SKILL.md`；改动以主仓为准，本仓同步跟进。

## License

MIT
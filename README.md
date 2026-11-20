# dsh-ai-research-workflow

一个 DeepSeek Harness（DSH）的 **skill bundle**：把一个「现象驱动的科研工作流」skill 打包成可一键安装的插件。

## 是什么

`ai-research-workflow` 是一套方向无关的科研工作流 skill，核心方法是**现象驱动**：

> 不凭空想 idea——先在小系统里跑海量小实验找规律，由规律反推出 idea，再查新、再上卡验证。

包含：造现象发现循环、反向追问、三轮查新（含"找到空白先问两句"、非论文渠道）、CCF-A 顶会适配性判断、拆论文、争议地图、选题漏斗、固定预算实验循环、跨模型执行/评审分离、五层审计链、结果-结论追踪、反重复记忆。

## 安装

```bash
# 在 DSH 里，通过 Plugin Manager / agent 工具安装
install_bundle dsh-ai-research-workflow
```

或本地目录 link：

```bash
install_bundle /path/to/dsh-ai-research-workflow
```

装好后，新 session 里 agent 就能按需加载 `ai-research-workflow` skill。

## 结构

```
package.json          # dsh.bundle.patch 声明
cordis.patch.yml      # mount 本插件
index.js              # 在 ctx.skills 上注册 skill（仿 @deepseek-ai/dsh-skill-office）
assets/ai-research-workflow/SKILL.md   # skill 本体
locale/en.json, zh.json                # 标题与描述
```

## 说明

- 依赖 DSH 的 skill registry（`@deepseek-ai/dsh-skill`），base 配置已自带。
- skill 本体维护在 `assets/ai-research-workflow/SKILL.md`，改这一份即可。
- 原始 skill 源码与评测见 <https://github.com/zhuowenzhang288-web/ai-research-workflow>。

## License

MIT

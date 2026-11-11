# Skill Artifact Check

**你上传的 Skill，真的是刚刚修改的那一版吗？**

这是一个离线、零运行时依赖的 Python 命令行工具。将 `.skill` / ZIP 包或已安装目录与预期源目录逐文件比较，找出旧内容、遗漏脚本和多余文件。只输出路径与状态，不打印文件内容。

## 立即使用

需要 Python 3.10+，下载项目源码并进入项目目录：

```sh
python3 skill_artifact_check.py examples/demo
python3 skill_artifact_check.py ./release.skill --source ./my-skill
python3 skill_artifact_check.py ./installed/my-skill --source ./my-skill --json
```

Windows 可用 `py` 替换 `python3`。不需要 API Key、模型调用或账号，也不需要安装第三方运行时包。

- `changed`：文件内容不同，包含换行符差异。
- `missing`：实际包或安装目录缺少源目录中的文件。
- `extra`：实际包或安装目录多出了文件。
- 退出码 `0`：所选检查通过；`1`：发现结构问题或差异；`2`：输入无法完整检查。

省略 `--source` 时只检查结构，不能判断是不是最新版本。只去除 ZIP 最外面的一层包装目录，不会递归寻找一个看似正确的 Skill 来掩盖打包错误。

## 适合的场景

1. 发布前：确认 ZIP 中的内容与实际修改的目录完全一致。
2. 更新后：检查可访问的安装副本是否仍是旧版本。
3. CI：发布门禁发现变化后返回非零退出码。

同时检查重复 ZIP 条目、路径穿越、符号链接、大小写冲突、Windows 保留文件名、多个 SKILL.md 和常见打包垃圾。限制为 10,000 个条目、单文件 16 MiB、解压后总量 128 MiB、ZIP 文件 160 MiB。空目录、时间戳、执行权限和包装目录名不参与比对。

工具不解压、不运行脚本、不修改配置、不上传数据。报告含文件路径，分享前仍需检查。请使用稳定的目录快照。

完整 YAML/规范检查交给已有的 skill-validator；安全扫描与供应链验证可用 skil。这个项目只解决轻量的发布内容核对，不能修复客户端缓存或证明运行中的模型已加载新版本，也不是密钥扫描器。

[调研与竞品取舍](docs/RESEARCH.md) · [英文说明](README.md)

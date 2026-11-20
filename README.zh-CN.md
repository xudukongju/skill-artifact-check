# Skill Artifact Check

**你上传的 Skill，真的是刚刚修改的那一版吗？**

这是一个离线、零运行时依赖的 Python 命令行工具。将 `.skill` / ZIP 包或已安装目录与预期源目录逐文件比较，找出旧内容、遗漏脚本和多余文件。只输出路径与状态，不打印文件内容。

## 打包显示成功，先确认交付内容

[下载项目源码 ZIP](https://github.com/xudukongju/skill-artifact-check/archive/refs/heads/main.zip)，
解压后用 Python 3.10+ 执行（Windows 可用 `py`）：

```sh
python3 examples/release_baseline.py
```

三个合成场景分别展示：把有意排除的文件错当基准、实际包与预期一致、打包后真正的脚本内容过期。
无须安装工具，也不改已有文件。遇到空 ZIP，[先恢复打包](docs/EMPTY_PACKAGE.md)：
列出包里的文件就能发现空包。需要对照预期发布内容、定位差异并在 CI 中失败时，再用此工具。

如果你在真实发布任务中试用了，欢迎在 [GitHub Issue](https://github.com/xudukongju/skill-artifact-check/issues/new)
说说之前怎么核对、这次改变了哪一步。只需数量或合成样本，不必上传技能包或公开私有路径。

## 核对自己的发布包

需要 Python 3.10+，下载项目源码并进入项目目录：

```sh
python3 skill_artifact_check.py examples/demo
python3 skill_artifact_check.py ./release.skill --source ./staging/my-skill
python3 skill_artifact_check.py ./installed/my-skill --source ./my-skill --json
```

Windows 可用 `py` 替换 `python3`。不需要 API Key、模型调用或账号，也不需要安装第三方运行时包。

`staging/my-skill` 应是按发布规则准备的预期交付目录，不一定是整个开发目录。打包器有意排除的缓存或评测文件，不能误判成漏打包。[实测案例与可运行示例](docs/RELEASE_BASELINE.md)也说明了普通 `diff` 已能覆盖哪些检查，无需重复引入工具。

[真实空包故障与恢复验收](docs/EMPTY_PACKAGE.md)：用固定版本的上游打包器实际生成产物，核对空包、恢复后的内容及隐藏文件排除策略；附可运行例子与 CI。

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

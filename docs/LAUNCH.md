# Launch kit — prepared, not published

## Release description

Skill Artifact Check 0.1.0 is an offline Python CLI for a narrow release question: does this Skill ZIP or installed folder contain the same files and bytes as the intended source?

It reports changed, missing and extra files, checks common archive/layout problems, and produces JSON with CI-friendly exit codes. It has no runtime dependencies and never executes skill scripts or extracts the archive.

Initial evidence: 34 local regression tests on Python 3.12/macOS, plus wheel build and isolated-install smoke test. Cross-platform hosted CI is configured but has not run. It checks payload/layout, not complete YAML validation, malicious behavior, or the client's live loaded state.

## Discovery metadata

- Suggested repository: `skill-artifact-check`
- Description: `Offline payload parity checks for Agent Skill ZIPs and installed folders. Catch stale releases and missing helpers before upload.`
- Suggested topics: `agent-skills`, `developer-tools`, `python`, `cli`, `release-engineering`, `validation`
- Release tag after publishing: `v0.1.0`
- Assets: Python wheel and source ZIP. Do not claim PyPI availability.

## English community post draft

Title: I made a tiny offline check for stale Skill ZIPs and missing helper files

I built Skill Artifact Check after seeing reports where saving or updating a skill did not deliver the files people had actually edited. It compares the resulting ZIP/.skill or an accessible installed directory with a known source folder, and reports changed, missing and extra files.

It is Python standard-library only, reads files without running them, and can fail a CI release step. It also rejects ambiguous archive paths and symlinks. It does not fix Claude's cache, prove which files a running agent loaded, or replace skill-validator/skil.

I'd value feedback from skill authors: have you shipped a package whose contents differed from your working folder? Would a small check like this fit your release process?

Disclosure to include: this project, its tests and this launch text were primarily generated with Codex.

Attach the verified public repository URL only after publication. Disclose that you built it. Post once in a relevant community whose current rules allow project sharing; do not paste this into unrelated support threads.

## 中文发布文案草稿

标题：Skill 改好了，上传的 ZIP 却还是旧版？做了一个离线核对工具

我做了 Skill Artifact Check：把准备上传的 `.skill` / ZIP 或已安装目录，与真正修改过的源目录逐文件比较，直接指出旧内容、遗漏脚本和多余文件。

只需要 Python，无运行时第三方依赖，不调用模型、不上传数据、不运行 Skill 脚本。支持 JSON 和 CI 退出码，也检查常见打包问题。它解决的是“内容有没有交付正确”，不是修复客户端缓存，也不是完整安全扫描器。

如果你维护多文件 Skill，欢迎用不含私密信息的样例反馈：这个检查是否能融入发布流程？

披露：本项目的实现、测试和这段发布文案主要由 Codex 辅助完成。

发布时附已核验的仓库链接，不编造用户量、平台兼容认证或安全保证。

## Publication sequence and gate

1. GitHub connector is authenticated as xudukongju. Repository creation and releases need the official gh CLI because these actions are not exposed by this connector. CLI installation currently fails on network downloads and UI automation access was denied. User has been asked to create the public repository with an initial README so connector-based code publication can proceed. Revisit release/discussion APIs only when a capable route is available. Do not retrieve credentials through filesystem or shell workarounds.
2. Create the public repository under the user's confirmed personal account. If multiple organizations or accounts are available, ask which destination to use.
3. Push the reviewed project, check the resulting remote files and Actions results, correct any platform failure, and then publish the release and attach built artifacts.
4. Add repository description/topics. This is the first authorized discovery action.
5. For external community promotion, use an authenticated user-selected account or ask for access when needed. Read the community's current self-promotion rules first. One useful launch post beats repeated unsolicited comments; no paid ads, fabricated testimonials, stars or engagement.
6. Record actual URLs and results below. A draft is not a published post, and publishing is not evidence of adoption.

## Actual distribution record

- Public repository: pending GitHub authorization.
- GitHub Release: not published.
- External posts: none.
- Traffic/adoption: not measured.

## Selected community channel

[Agent Skills Show and tell](https://github.com/agentskills/agentskills/discussions/categories/show-and-tell) explicitly invites sharing creations. Its [contribution guidance](https://github.com/agentskills/agentskills/blob/main/CONTRIBUTING.md), inspected on 2026-11-11, directs open-ended feedback to Discussions and requires disclosure of AI assistance in contributions. Prefer one substantive showcase discussion after the repository and release are live. Do not submit a client ecosystem-listing PR: this tool does not discover and execute skills, so it does not meet that listing criterion.

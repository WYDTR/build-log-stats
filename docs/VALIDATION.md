# 本地验证记录

开发环境：Windows，MinGW-w64 GCC 14.2.0，GNU Make 4.4.1，Python 3.14.5。
下表记录实际执行结果；GitHub CI、Docker 镜像和 Linux strace 的结果以之后实际运行记录为准。

| 检查 | 结果 | 本地日志 |
|---|---|---|
| 主分支功能、修复及安装契约 | 28 项通过 | `work/development/fixed-full-tests.log` |
| 接口说明安装调整后的安装测试 | 3 项通过 | 测试终端输出；`tests/test_installer.py` 可复现 |
| LF 补丁兼容修复后的受影响回归 | 4 项通过 | 测试终端输出；`tests/test_incremental.py` 可复现 |
| GCC 严格警告与静态分析 | 两个 C 源文件均以 `-Werror -fanalyzer` 通过 | 编译终端输出 |
| 课程原有契约兼容性 | 安装适配后 10 项通过 | `work/compatibility-01/original-contracts.log` |
| DRAFT 候选约束 | 使用课程原 `prepare_candidate` 校验通过 | `work/compatibility-01/request.log` |
| 请求与来源清单生成 | 通过，重复运行内容一致 | `work/compatibility-01/result.json` |
| 基础、目标、修复提交独立检出与重建 | 通过 | `work/history-02/result.json` |

## 实际缺陷及修复

目标提交唯一漏依赖为 `helper.o -> rules.h`。将 note 配置从 1 改为 0：

- 缺陷版本普通增量构建：note 数仍为 2，错误复用旧对象文件。
- 缺陷版本干净重建：note 数为 0，证明源码配置已经生效。
- 加入依赖后的增量构建：只刷新 helper.o，保留 main.o，note 数正确变为 0。

历史复现中 C0 的 18 项功能测试、C1/C2 各 21 项功能测试通过。
对真实历史 C1 生成补丁后，patch_applies、build、test、header_change、no_missing 五项均通过。

首次历史复现暴露 Windows CRLF 补丁与 Git LF 检出文件不匹配的问题。
补丁生成已统一为 LF，失败记录保留在 `work/history-01/`，成功记录保存在 `work/history-02/`。

## 验证边界

本地没有执行 Docker/strace 全流程，也没有声称 GitHub CI 已运行。
上传现有历史后，按 `docs/INTEGRATION.md` 在原 A-buildchecker 中执行真实项目五阶段验收，
保存实际的 job_id、trace_id、报告、哈希和运行日志。

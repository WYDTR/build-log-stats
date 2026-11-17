# 接入已有 A-buildchecker 的 E11-E12 流程

这个仓库是被测 C 项目；已有 `devops_A_buildchecker` 继续保存集成服务、个人报告和课程 PR。
项目来源应写明“本轮新开发并实际维护的工具”；两个故障均为有明确记录的实验性故障。
上传历史后使用实际仓库 URL 和完整 SHA，固定样例和本项目证据分别记录。

## 1. 在服务器克隆

在已有 A-buildchecker 目录执行，地址按实际新仓库替换：

```bash
mkdir -p data
git clone https://github.com/WYDTR/build-log-stats.git data/real-project
git -C data/real-project log --oneline --decorate -5
cat data/real-project/integration/commits.json
```

如果 `data/real-project` 已保存其他项目，选择一个新的 data 子目录，并相应替换以下脚本路径。
请求生成器会根据实际克隆路径生成 `/course/data/...` 地址，保留已有其他数据。

## 2. 安装行为验证配置

```bash
python3 data/real-project/integration/install_adapter.py .
git diff -- labs/e11e12/pipeline.py
python3 run_e11e12.py test
```

安装只为请求中的 `validation_profile=build-log-stats-v1` 选择新验证器；未提供该字段时使用原有逻辑。
安装器把接口扩展说明放入 `docs/e11e12-build-log-stats-contract.md`，把备份及收据放入 `work/adapter-install/`。
新增模块、pipeline 改动和接口说明应随本次集成分支提交，并在 ADR 中记录这个适配决定。

## 3. 准备请求、候选和来源清单

```bash
python3 data/real-project/integration/make_request.py .
cat data/real-request.json
cat data/real-dataset.json
```

脚本检查所有完整提交确实存在、基线是目标的祖先，并使用课程自带的 `prepare_candidate` 校验候选。
新请求沿用现有五阶段接口，构建超时为 1800 秒，候选使用前次已采用的清华镜像配置。
如果同名数据文件已有不同内容，脚本会提示保留并检查该数据集。

## 4. 先做项目本身的复现

```bash
python3 data/real-project/integration/verify_history.py --out work/real-history-01
```

预期 `HISTORY_REPAIR_PASS`。它检查 C0/C1/C2 构建与功能、GCC 依赖差异和补丁的行为验证。
这一步不替代下一步 Docker/strace 全流程验收。

## 5. 运行手册中的真实项目入口

```bash
python3 run_e11e12.py run --request data/real-request.json --out work/e12-real-01
echo "REAL_INTEGRATION_EXIT_CODE=$?"
cat work/e12-real-01/incremental-report.json
cat work/e12-real-01/recheck.json
```

预期五阶段 SUCCEEDED，目标增量报告新增 `MISSING helper.o rules.h`，补丁只补该依赖，复验五项通过，最终无 MD。
保留全部失败与成功证据；重试使用新的 work 子目录。

## 数据与提交边界

- 本项目源码、测试、历史和标签上传到新工具仓库。
- 验证适配、接口说明、课程报告和 ADR 上传到原个人集成仓库。
- 数据请求、来源清单和 work 原始证据按手册归档。
- Docker 构建、真实 strace 以及 GitHub CI 的执行结果，以服务器/CI 实际运行记录为准。

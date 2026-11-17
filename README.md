# build-log-stats

一个用 C11 实现的构建日志统计工具，用于汇总编译日志中的警告、错误和 note。
支持文件或标准输入、文本或 JSON 输出、ANSI 颜色日志、长行，以及用于 CI 的错误退出码。

这是本轮实际开发的新工具，基础实现和功能扩展将分别记录为真实 Git 提交。
课程中的 Dockerfile 缺少工具链、Makefile 漏依赖实验会明确标注为受控故障。

## 构建与运行

Linux：

```bash
make app
./app --json tests/fixtures/compiler.log
make test
make check-deps
```

Windows PowerShell（GCC 与 mingw32-make 已在 PATH 中）：

```powershell
mingw32-make app
.\app.exe --json tests/fixtures/compiler.log
mingw32-make test
mingw32-make check-deps
```

`app [--json] [--fail-on-error] [--] [FILE|-]`。不指定文件或使用 `-` 时读取标准输入。
退出码：0 表示正常统计；指定 `--fail-on-error` 且发现错误时为 1；参数错误为 2；输入输出失败为 3。
统计的是包含诊断标记的行，同一行按 error、warning、note 的优先级归类，不重复计数。
v0.2 默认忽略 ASCII 大小写，并通过 `rules.h` 配置是否统计 note。
单词内部的同名片段不算诊断；它是文本标记统计器，不是完整的编译器诊断语法解析器。

样例结果：`{"lines":9,"warnings":2,"errors":2,"notes":2}`。

`main` 已修复 `helper.o -> rules.h` 的漏依赖，`make check-deps` 应通过。
历史标签 `e12-target` 保留明确注入的漏依赖，供 E12 检测和修复；详情见 `docs/EXPERIMENT.md`。

程序不依赖 Python；Python 标准库仅用于测试、清理和开发检查。

## 开发历史与 E12 接入

- `e12-base`：基础实现；`e12-target`：功能扩展及受控漏依赖；`e12-fixed`：修复与回归验证。
- [实验来源和故障说明](docs/EXPERIMENT.md)
- [上传现有 Git 历史](docs/UPLOAD.md)
- [服务器 E12 接入步骤](docs/INTEGRATION.md)
- [可选验证配置的接口契约](integration/INTERFACE.md)

`main` 的功能、依赖、修复拒绝和安装兼容性测试均可通过 `make test check-deps` 运行。
历史复现：`python3 integration/verify_history.py --out work/history-01`。
该命令保存真实执行日志，包含 C0/C1 的功能和依赖差异，以及补丁应用后的头文件重建结果。

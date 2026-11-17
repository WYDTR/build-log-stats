# build-log-stats

一个用 C11 实现的构建日志统计工具，用于汇总编译日志中的警告和错误。
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
统计的是包含诊断标记的行，同一行按 error、warning 的优先级归类，不重复计数。
v0.1 仅识别小写 `error:` 和 `warning:`；单词内部的同名片段不算诊断。

程序不依赖 Python；Python 标准库仅用于测试、清理和开发检查。

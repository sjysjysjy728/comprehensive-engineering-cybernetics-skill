# 项目交付评测：确定性 JSON 计数合并器

> 公开状态：本任务及验收器已经公开，只适合作为回归/烟雾测试，不能再视为隐藏测试或无污染的盲测。

## 目标与边界

修复 `counter_merge.py`，使它在 Windows、CPython 3.11 或更高版本上成为一个确定性的 JSON 计数合并器。只能使用 Python 标准库，不得联网、启动子进程、修改输入文件或创建运行时文件。

命令行接口固定为：

```text
python counter_merge.py LEFT_JSON RIGHT_JSON
```

脚本必须恰有两个路径参数，并先完整读取、解析和验证左输入，再处理右输入；多个错误并存时，返回最先处理到的错误。

## 输入合同

每个输入必须满足：

1. 是 UTF-8 文本，允许文件开头有一个 UTF-8 BOM。
2. 可被标准库 `json.loads` 解析，但 `NaN`、`Infinity` 和 `-Infinity` 非法。
3. 顶层是 JSON 对象，且同一对象中没有重复成员名。
4. 键可以是任意 JSON 字符串；区分大小写，不裁剪、不做 Unicode 归一化。
5. 值必须使用无小数部分、无指数形式的 JSON 整数语法；布尔值不算整数。
6. 每个输入值在 `0` 至 `9223372036854775807`（含端点）之间；`-0` 合法并等于 `0`。

## 合并与输出合同

- 输出包含左右对象所有键；同名键相加，只出现一次的键保留，零值不得删除。
- 同一路径作为左右输入时仍按两个逻辑输入处理；两个合法值相加后可以超过单值上限。
- 成功时退出码为 `0`、`stderr` 为空；`stdout` 恰为以下等价 JSON 和一个逻辑换行：

```python
json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
```

- 输出键按 Python 字符串的 Unicode 码点顺序排列；对同一输入，在不同 `PYTHONHASHSEED` 下输出必须逐字一致。

## 错误合同

所有错误均须退出码为 `2`、`stdout` 为空，且 `stderr` 只含对应文本和一个逻辑换行：

| 情形 | 精确文本 |
|---|---|
| 参数数量不是两个 | `error: expected exactly two input paths` |
| 左/右输入无法读取 | `error: cannot read left/right input` |
| 左/右输入不是合法 UTF-8 | `error: invalid UTF-8 in left/right input` |
| 左/右输入 JSON 解析失败或含非标准常量 | `error: invalid JSON in left/right input` |
| 左/右输入违反顶层、重复键或值规则 | `error: invalid count object in left/right input` |

表中的 `left/right` 应替换为实际一侧。读取错误包括不存在、目录路径、权限不足和其他 `OSError`。任何错误都不得输出 usage、堆栈或 traceback。

## 完成门禁

在本目录执行：

```bash
python -I -B acceptance_test.py counter_merge.py
```

验收器必须报告 `52/52`，且返回码为 `0`。它覆盖功能、错误优先级、确定性、Unicode/空格路径、输入不变性，以及对网络、子进程和运行时写文件的主动阻断。

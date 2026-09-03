$comprehensive-engineering-cybernetics

请在当前目录完成 `frozen/TASK.md` 中冻结的任务，并以 `frozen/RUBRIC.md` 为验收边界。

这是一次独立性测试，必须遵守以下额外约束：

1. 只使用明确调用的 `comprehensive-engineering-cybernetics` Skill。不得读取、调用或借鉴任何其他 Skill。
2. 不得读取 VS Code、Copilot、Cursor 或其他编辑器扩展目录中的 Skill 或提示内容。
3. 不得浏览网页，不得读取本机的《工程控制论》PDF/OCR，不得读取本任务目录之外的项目、下载仓库或准备材料。
4. 目标 Skill 方面，只可读取其已安装的 `SKILL.md`，以及该文件针对“项目交付模式”明确指示加载的目标 Skill 自有 reference 文件。
5. 不得生成或调用子代理。除 Python 标准库外不得使用外部程序来实现目标功能。
6. 不得修改 `frozen/` 中的任何文件；只能修改 `work/counter_merge.py`。
7. 可以运行 `python frozen/acceptance_test.py work/counter_merge.py` 作为验收。
8. 最终答复必须列出：实际读取的 Skill 文件；关键缺陷；需求到修改的对应；至少一个成功和一个失败用例的实际命令、退出码与输出；完整验收结果；任何未验证事项。

请直接实施、验证并交付，不要向用户追问。

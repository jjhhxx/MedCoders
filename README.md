# MedCoders
Repository for xx

## 注意事项
- 在执行时你需要删除 code_resault 目录下的文件，对于目录下已经存在的文件，coding_with_question 回跳过该 profile
- 对于异常退出的 profile，你需要检查后再次执行 coding_with_question
- 如果 coding_with_question 成功执行，会在同目录下生成最终文件 result.json；直接提交即可
- 每个阶段的 prompt 分为 prompt + prompt_params，避免了 format 时字典的格式问题

## 生成逻辑
当前根据提供的 FHIR_FSH 生成相应代码按照三个步骤进行：
- 提取 FHIR_FSH 中的三类核心资源：1. 所有 ValueSet（值集）；2. 所有 CodeSystem（代码系统）；3. 所有 Profile（资源规范），并将三类资源分别整理为 JSON 数组 Step_1_result 。
- 根据 ValueSet 的 id、title、description 调用大模型并开启在线检索，返回该 ValueSet 对应的详细关键信息；并合并到 Step_1_result 中。
- 将完整的 Step_1_result 提供给 Coder 模型，生成相应的 Code 代码；prompt 中使用了三个示例引导。

## 后续优化方向
- 改进三轮的 prompt，有些地方仍然比较模糊
- 更换基座模型，测试别的模型生成效果
- 更换当前生成流程，看哪种流程生成的 Code 最符号要求

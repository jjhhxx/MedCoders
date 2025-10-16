import re
import ast
from typing import Dict, Optional, Tuple
from llms import llm_client
from model import intention_client_manager


def generate_llm_response(intention: str, format_params: dict):
    """通用LLM响应生成函数"""
    prompt_template = intention_client_manager.get_intention_prompt_by_intention(intention)
    check_function = intention_client_manager.get_check_function_by_intention(intention)
    temperature, max_tokens = intention_client_manager.get_request_params_by_intention(intention)
    formatted_prompt = prompt_template.format(**format_params)
    return llm_client.chat_and_check(
        [{"role": "user", "content": formatted_prompt}],
        check_function,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _check_python_code(response_text: str) -> tuple:
    """
    提取回答中的Python代码并检查语法错误
    """
    # 1. 提取用```python ```包裹的代码块
    code_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
    match = code_pattern.search(response_text)

    extracted_code = None
    if match:
        extracted_code = match.group(1).strip()

    # 2. 检查语法错误
    syntax_error = ""
    if extracted_code:
        try:
            # 使用ast模块解析代码，若有语法错误会抛出SyntaxError
            ast.parse(extracted_code)
        except SyntaxError as e:
            # 格式化错误信息（包含错误位置和原因）
            syntax_error = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"

    return extracted_code, syntax_error


def coding_with_question(label, question, FHIR_FSH):
    if not label or not question:
        raise ValueError("The label and question cannot be empty")

    _, step_1_response = generate_llm_response(
        "coding-extract_input_information",
        {
            "label": label,
            "question": question,
            "FHIR_FSH": FHIR_FSH,
        }
    )
    print(f"------------------step_1_reason---------------")
    print(step_1_response)

    _, step_2_response = generate_llm_response(
        "coding-define_rule",
        {
            "result_by_step_1": step_1_response,
        }
    )
    print(f"------------------step_2_reason---------------")
    print(step_2_response)

    _, step_3_response = generate_llm_response(
        "coding-class_init",
        {
            "result_by_step_1": step_1_response,
            "result_by_step_2": step_2_response,
        }
    )
    print(f"------------------step_3_reason---------------")
    print(step_3_response)

    _, step_4_response = generate_llm_response(
        "coding-class_core_code",
        {
            "result_by_step_1": step_1_response,
            "result_by_step_2": step_2_response,
            "result_by_step_3": step_3_response,
        }
    )
    print(f"------------------step_4_reason---------------")
    print(step_4_response)

    _, step_5_response = generate_llm_response(
        "coding-class_complete",
        {
            "label": label,
            "question": question,
            "FHIR_FSH": FHIR_FSH,
            "result_by_step_3": step_3_response,
            "result_by_step_4": step_4_response,
        }
    )
    print(f"------------------step_5_reason---------------")
    print(step_5_response)

    target_code, check = _check_python_code(step_5_response)
    if not check:
        return target_code
    raise TypeError("The target code is not correct python!")


if __name__ == "__main__":
    import json
    from utils import extract_excel_data
    meta = extract_excel_data(r"E:\xidian\比赛\CHIP2025-医学NLP代码\A榜数据\test A.xlsx")

    result = []
    for _id, label, question, deepquery_id, fhir_fsh in meta:
        code = coding_with_question(label, question, fhir_fsh)
        _result = {
            "id": _id,
            "deepquery_id": deepquery_id,
            "code": code
        }
        result.append(_result)

    with open("./output.jsonl", "w", encoding="utf-8") as f:
        for result in result:
            f.write(json.dumps(result) + "\n")

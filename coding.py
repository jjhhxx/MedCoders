import re
import ast
import uuid
from typing import Dict, Optional, Tuple
from llms import llm_client, llm_client_coder
from model import intention_client_manager


def generate_llm_response(intention: str, format_params: dict, chat_client):
    """通用LLM响应生成函数"""
    prompt_template = intention_client_manager.get_intention_prompt_by_intention(intention)
    params_template = intention_client_manager.get_intention_prompt_params_by_intention(intention)
    check_function = intention_client_manager.get_check_function_by_intention(intention)
    temperature, max_tokens = intention_client_manager.get_request_params_by_intention(intention)
    formatted_prompt = prompt_template + params_template.format(**format_params)
    return chat_client.chat_and_check(
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
        "coding-step_1_extract_FHIR",
        {
            "label": label,
            "question": question,
            "FHIR_FSH": FHIR_FSH,
        },
        llm_client
    )
    print(f"------------------step_1_reason---------------")

    valueSets = step_1_response["valueSets"]
    convert_valueSets = []
    for valueSet in valueSets:
        _, step_2_response = generate_llm_response(
            "coding-step_2_online_search",
            {
                "FHIR_ValueSet": {
                    "id": valueSet["id"],
                    "title": valueSet["title"],
                    "description": valueSet["description"],
                },
            },
            llm_client
        )
        print(f"------------------step_2_reason---------------")
        valueSet["detailed_information"] = step_2_response
        convert_valueSets.append(valueSet)
    step_1_response["valueSets"] = convert_valueSets

    _, step_3_response = generate_llm_response(
        "coding-step_3_generate",
        {
            "FHIR_FSH": step_1_response,
        },
        llm_client_coder
    )

    target_code, check = _check_python_code(step_3_response)
    if not check:
        return target_code
    raise TypeError("The target code is not correct python!")


if __name__ == "__main__":
    import json, os
    from utils import extract_excel_data
    from example_3 import base64_encode
    meta = extract_excel_data(r"../A榜数据/test A.xlsx")

    for _id, label, question, deepquery_id, profile_id, fhir_fsh in meta:
        if os.path.exists(f"./code_result/cnwqk{profile_id}.py"):
            continue
        code = coding_with_question(label, question, fhir_fsh)
        print(f"Code will be write {profile_id}")
        with open(f"./code_result/cnwqk{profile_id}.py", "w", encoding="utf-8") as f:
            f.write(code)

    print("1: Succeed for generate code !")
    # covert
    test_json_a = json.loads(open("./testA.json", "r", encoding="utf-8").read())
    entry = test_json_a["entry"]
    result = {
        "resourceType": "Bundle",
        "type": "message",
        "total": 18,
    }

    covert_entry = []
    for meta in entry:
        resource = meta["resource"]
        print(resource)
        resource["id"] = str(uuid.uuid4())
        resourceType = resource["resourceType"]
        if resourceType == "MessageHeader":
            covert_entry.append({"resource": resource})
            continue

        content = resource["content"]
        title = content[0]["title"]
        meta_content = open(f"./code_result/{title}.py", "r", encoding="utf-8").read()
        base64_content = base64_encode(meta_content)
        content[0]["data"] = base64_content
        resource["content"] = content
        covert_entry.append({"resource": resource})

    result["entry"] = covert_entry
    with open("result.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=4))
    print("2: Succeed for generate submit !")

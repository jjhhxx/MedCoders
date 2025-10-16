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

    return step_5_response


if __name__ == "__main__":
    test_label = "Therapy or Surgery"
    test_question = "2. 肛门手术患者;"
    test_FHIR_FSH = '''
        // 1. ICD-O-3肛门部位值集
        ValueSet: CNWQK75_AnusBodyLocationVS
        Id: cnwqk75-anus-body-location-vs
        Title: "肛门部位解剖位置值集"
        Description: "基于ICD-O-3的肛门部位编码值集"
        * ^url = "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-body-location-vs"
        * include codes from system http://localhost:3456/api/terminology/CodeSystem/icdo3 where concept regex /C21\.[0-8]/
        
        // 2. ICD-10肛门疾病值集
        ValueSet: CNWQK75_AnusDiseaseVS
        Id: cnwqk75-anus-disease-vs
        Title: "肛门疾病诊断值集"
        Description: "基于ICD-10的肛门疾病编码值集"
        * ^url = "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-disease-vs"
        * include codes from system http://localhost:3456/api/terminology/CodeSystem/icd10 where concept regex /K62\.[0-9]|C21\.[0-9]|K62\.5/
        
        // 3. 自定义肛门手术操作编码系统
        CodeSystem: CNWQK75_AnusSurgeryCS
        Id: cnwqk75-anus-surgery-cs
        Title: "肛门手术操作编码系统"
        Description: "自定义肛门手术操作编码系统"
        * ^url = "http://localhost:3456/api/terminology/CodeSystem/cnwqk75-anus-surgery-cs"
        * ^caseSensitive = true
        * #ANS001 "肛门瘘管切除术" "痔疮手术"
        * #ANS002 "肛门成形术"
        * #ANS003 "肛门括约肌切开术"
        * #ANS004 "痔切除术" "痔疮手术"
        * #ANS005 "肛门脓肿引流术"
        
        // 4. 自定义肛门手术值集
        ValueSet: CNWQK75_AnusSurgeryVS
        Id: cnwqk75-anus-surgery-vs
        Title: "肛门手术操作值集"
        Description: "包含所有肛门手术操作编码的值集"
        * ^url = "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-surgery-vs"
        * include codes from system CNWQK75_AnusSurgeryCS
        
        // 5. 肛门手术患者Profile（修复语法错误）
        Profile: CNWQK75_AnusSurgeryPatient
        Parent: Procedure
        Id: cnwqk75-anus-surgery-patient
        Title: "肛门手术患者规范"
        Description: "定义接受肛门手术的患者资源规范"
        * ^url = "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-surgery-patient"
        * status 1..1
        * code from CNWQK75_AnusSurgeryVS (required)
        * bodySite from CNWQK75_AnusBodyLocationVS (required)
        * subject 1..1
        * performed[x] 1..1
        * reasonCode from CNWQK75_AnusDiseaseVS
        * note 0..* MS
        
        // 6. 肛门疾病患者Profile
        Profile: CNWQK75_AnusDiseasePatient
        Parent: Condition
        Id: cnwqk75-anus-disease-patient
        Title: "肛门疾病患者规范"
        Description: "定义肛门疾病患者的诊断资源规范"
        * ^url = "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-disease-patient"
        * clinicalStatus 1..1
        * code from CNWQK75_AnusDiseaseVS (required)
        * subject 1..1
        * onset[x] 0..1
        * note 0..* MS
        
        // 7. 临床注释规范
        Profile: CNWQK75_ClinicalNote
        Parent: Annotation
        Id: cnwqk75-clinical-note
        Title: "临床注释规范"
        Description: "定义临床文本注释的规范"
        * ^url = "http://localhost:3456/api/terminology/Profile/cnwqk75-clinical-note"
        * text 1..1
        * time 0..1
        * author[x] 0..1
    '''

    result = coding_with_question(test_label, test_question, test_FHIR_FSH)

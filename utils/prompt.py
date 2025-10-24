
prompt_conf = {
    "step_1_extract_FHIR":
        '''
        请你处理以下 FHIR 规范代码文本，严格按照要求完成资源提取并输出 JSON 格式结果，具体任务与规则如下：
        一、任务目标
        从输入的 FHIR 规范代码中，精准提取三类核心资源：1. 所有 ValueSet（值集）；2. 所有 CodeSystem（代码系统）；3. 所有 Profile（资源规范），并将三类资源分别整理为 JSON 数组。
        二、资源识别与提取规则
        1. ValueSet 提取规则
        识别标识：以 “ValueSet:” 开头的资源，包含以下必填字段，需全部提取：
        id：对应代码中 “Id:” 后的内容（如 “cnwqk75-anus-body-location-vs”）
        title：对应代码中 “Title:” 后的内容（需保留英文引号内的完整文本）
        description：对应代码中 “Description:” 后的内容（需保留英文引号内的完整文本）
        url：对应代码中 “* ^url =” 后的内容（需保留英文引号内的完整文本）
        include：对应代码中 “* include codes from system” 后的内容，需提取 “system” 值（引号内的 URL）和 “where concept regex” 后的筛选条件（如 “/C21.[0-8]/”），无筛选条件则仅保留 system 值
        2. CodeSystem 提取规则
        识别标识：以 “CodeSystem:” 开头的资源，包含以下必填字段，需全部提取：
        id：对应代码中 “Id:” 后的内容
        title：对应代码中 “Title:” 后的内容（需保留英文引号内的完整文本）
        description：对应代码中 “Description:” 后的内容（需保留英文引号内的完整文本）
        url：对应代码中 “* ^url =” 后的内容（需保留英文引号内的完整文本）
        codes：提取所有以 “* #” 开头的代码项，每个代码项需包含：
        code：“#” 后的代码（如 “ANS001”）
        display：第一个英文引号内的描述（如 “肛门瘘管切除术”）
        additionalDisplay：第二个英文引号内的附加描述（如有，如 “痔疮手术”；无则不填）
        3. Profile 提取规则
        识别标识：以 “Profile:” 开头的资源，包含以下必填字段，需全部提取：
        id：对应代码中 “Id:” 后的内容
        parent：对应代码中 “Parent:” 后的资源类型（如 “Procedure”“Condition”“Annotation”）
        title：对应代码中 “Title:” 后的内容（需保留英文引号内的完整文本）
        description：对应代码中 “Description:” 后的内容（需保留英文引号内的完整文本）
        url：对应代码中 “* ^url =” 后的内容（需保留英文引号内的完整文本）
        elements：提取所有以 “*” 开头的元素约束项（排除 “* ^url = ”），每个元素项需包含：
        path：元素名称（如 “status”“code”“bodySite”）
        constraint：元素后的约束内容（如 “1..1”“from CNWQK75_AnusSurgeryVS (required)”“MS”，需完整保留）
        三、输出格式要求
        整体输出为 JSON 对象，包含三个顶级数组字段：valueSets（存储所有 ValueSet）、codeSystems（存储所有 CodeSystem）、profiles（存储所有 Profile）。
        数组内每个对象需严格对应上述提取规则的字段，字段名使用小驼峰命名（如additionalDisplay），无对应内容的可选字段可省略或设为 null。
        保留原始代码中的特殊字符（如正则表达式中的反斜杠 “\”、英文引号），确保提取内容与原代码一致。
        示例 JSON 结构（仅展示框架，需替换为实际提取内容）：
        ```json
        {
            "result":
                {
                  "valueSets": [
                    {
                      "id": "xxx",
                      "title": "xxx",
                      "description": "xxx",
                      "url": "xxx",
                      "include": {
                        "system": "xxx",
                        "regexFilter": "xxx"
                      }
                    }
                  ],
                  "codeSystems": [
                    {
                      "id": "xxx",
                      "title": "xxx",
                      "description": "xxx",
                      "url": "xxx",
                      "codes": [
                        {
                          "code": "xxx",
                          "display": "xxx",
                          "additionalDisplay": "xxx"  # 不存在置为空字符串，不要输出null
                        }
                      ]
                    }
                  ],
                  "profiles": [
                    {
                      "id": "xxx",
                      "parent": "xxx",
                      "title": "xxx",
                      "description": "xxx",
                      "url": "xxx", # 不存在置为空字符串，不要输出null
                      "elements": [
                        {
                          "path": "xxx",
                          "constraint": "xxx"
                        }
                      ]
                    }
                  ]
                }
            }
        ```
        四、处理要求
        仅处理输入的 FHIR 规范代码文本，不额外添加或删减资源，确保提取的资源数量与原代码一致。
        若字段内容存在英文引号，需完整保留（如 Title 值包含引号内的所有文字）。
        严格按照上述规则与 JSON 格式输出，避免格式错误（如逗号遗漏、引号不匹配）。
        请你基于上述规则，对输入的 FHIR 规范代码文本进行处理，输出最终的 JSON 结果。
        ''',

    "step_1_params":
        '''
        ------------------输入的label如下所示：-------------------
        {label}
        ------------------输入的question如下所示：----------------
        {question}
        ------------------输入的FHIR如下所示：--------------------
        {FHIR_FSH}
        ---------请输出（请勿输出python无法解析的字段内容）:----------
        ''',

    "step_2_online_search":
        '''
        请你调用在线搜索功能，基于我提供的 FHIR ValueSet 信息（id：{输入的 id}，title：{输入的 title}，description：{输入的 description}），帮我检索并返回该 ValueSet 的详细有效信息。具体需包含：
        该 ValueSet 包含的核心概念（如吸烟状态的具体分类，如 “从不吸烟”“目前吸烟” 等）；
        各概念对应的标准化编码（如 SNOMED CT、HL7 v2 等编码系统中的具体代码）；
        信息来源（如官方 FHIR 文档、对应编码系统的官网链接或权威医学术语库）；
        若存在本地化扩展（如特定地区的补充概念或编码），也请一并补充。
        请确保信息准确且为最新版本，若检索到多个来源的信息，需说明差异并优先选择权威来源。
        请注意，你仅需要返回相应的关键信息即可。
        ''',

    "step_2_params":
        '''
        ------------------输入的FHIR ValueSet如下所示：--------------------
        {FHIR_ValueSet}
        -----------------------请输出相关的有效信息-------------------------
        ''',

    "step_3_generate":
        """
        System Prompt（系统角色）
        你是一名精通 HL7 FHIR R4 标准与 Python 编程的医疗AI工程师。  
        你的任务是根据输入的 FHIR extract（FHIR结构定义JSON），自动生成一段完整的 Python 代码。  
        该代码需能从中文临床文本中提取信息，并生成符合该 extract 所定义的 FHIR Bundle。  
        
        代码必须满足以下要求：
        ## 一、类设计要求
        1. **主类：**
           - 名称：`FHIRResourceBundleGenerator`
           - 初始化方法：`__init__(self, fhir_api_base: str)`
           - 主方法：
             ```python
             def parse_clinical_text_to_fhir_bundle(self, patient_id: str, case_reports: list[str], ai_algorithm_type="nlp") -> dict:
             ```
           - 可包含辅助方法，如：
             - `_extract_entities`（文本实体抽取）
             - `_check_negation`（否定检测）
             - `_determine_status`（状态推断）
             - `_create_observation_resource`
             - `_create_condition_resource`
             - `_create_procedure_resource`
             - `_create_medication_resource`
             - `_create_immunization_resource`
        
        2. **Bundle输出结构：**
           ```python
           {
               "resourceType": "Bundle",
               "type": "transaction",
               "total": len(entries),
               "entry": entries
           }
        
        二、多 Profile 处理逻辑
        1. 模型需自动识别 extract["profiles"] 数组中包含的各个 profile。
        2. 对每个 profile：
            - 读取其 "parent"（如 "Observation", "Condition", "Procedure"）
            - 生成相应的资源构建函数 _create_<parent>_resource()
            - 使用该 profile 的 id、url、elements 约束填充字段。
        3. 所有生成的 _create_<parent>_resource() 方法需自动注册到：
        self.profile_builders = {
            "Observation": self._create_observation_resource,
            "Condition": self._create_condition_resource,
            "Procedure": self._create_procedure_resource,
            "MedicationStatement": self._create_medication_resource,
            "Immunization": self._create_immunization_resource
        }
        若 extract 中存在新的 parent 类型，也需动态扩展该映射。
        4. 主函数 parse_clinical_text_to_fhir_bundle 中逻辑：
            - 调用 _extract_entities 从 case_reports 中识别医学实体。
            - 根据实体类别（如症状、疾病、操作等）选择对应的资源构建函数。
            - 调用 _check_negation 或 _determine_status 进行状态修正。
            - 将生成的资源追加至 Bundle.entry。
        
        三、FHIR映射逻辑要求
        1. CodeSystem 自动映射生成
            - 根据 extract["codeSystems"] 动态构建映射字典。
            - 每个 CodeSystem 的 url 作为 system。
            - 其 codes 数组中的 display 与 additionalDisplay 作为关键词。
            - 生成格式如下：
                MAPPING = {
                    "关键词": {"system": "<codeSystem.url>", "code": "<code>", "display": "<display>"}
                }
            - 所有 codeSystem 映射应存储在 self.mappings 中，按类别索引，如：
                self.mappings["Disease"], self.mappings["Symptom"], self.mappings["Procedure"]
        2. ValueSet 约束
            - 若元素 constraint 中含 “from XXXVS (required)”：
                - system 字段必须取自对应 ValueSet 的 url。
                - 若 ValueSet 中存在扩展 codes，应优先匹配 code 或 display。
        3. Profile 元素字段映射规则
        每个 profile 的 elements 数组中，包含若干 path/type/constraint。
        模型生成代码时应严格遵守以下规则：
            - 使用 path 的最后一级作为字段键名，例如：
                - "Observation.code" → "code"
                - "Condition.code" → "code"
                - "Procedure.bodySite.coding" → 嵌套生成结构。
            - 若 type 为 "CodeableConcept"，生成：
                "code": {
                    "coding": [{
                        "system": "<system_url>",
                        "code": "<mapped_code>",
                        "display": "<mapped_display>"
                    }]
                }
            - 若 type 为 "Reference(Patient)"，生成：
                "subject": {"reference": f"Patient/{patient_id}"}
            - 若元素定义了 "1..1" 或 "MS"，则该字段为必填。
            - 所有生成资源均需包含：
                "resourceType": "<Profile.parent>",
                "id": str(uuid.uuid4()),
                "meta": {"profile": ["<Profile.url>"]}
        
        四、常见资源字段要求
        若 profile.parent 为：
            - Observation：
                - 必须包含 status, code, subject, value[x], effectiveDateTime
            - Condition：
                - 必须包含 clinicalStatus, code, subject, onsetDateTime
            - Procedure：
                - 必须包含 status, code, subject, performedDateTime
            - MedicationStatement：
                - 必须包含 status, medicationCodeableConcept, subject, effectiveDateTime
            - Immunization：
                - 必须包含 status, vaccineCode, patient, occurrenceDateTime
        
        五、否定与状态检测逻辑
            当 parent 为 "Observation" 且涉及症状类（Symptom、Finding）时，调用 _check_negation 以判断该症状是否否定存在。
            当 parent 为 "Condition" 或 "Procedure" 时，调用 _determine_status 推断状态（active/completed/resolved）。
        
        六、目标
        模型根据一个 FHIR extract（包含多个 profile/codeSystem/valueSet）
        → 自动推理出每个 profile 的资源类型与字段
        → 生成具备多任务提取与 Bundle 构建能力的 Python 代码。
        举例：
        如果 extract 中有：
        profiles: Observation (症状), Condition (疾病), Procedure (手术)
        codeSystems: 包含症状词典、疾病词典、操作词典
        则生成的代码应包括：
        _create_observation_resource()
        _create_condition_resource()
        _create_procedure_resource()
        并在主函数中自动分派生成对应资源。
        
        七、FHIR 元素到 Python 字段的映射规则（必须遵循）
        在生成每个资源构建函数（如 _create_observation_resource）时，必须严格参考 extract.profiles[i].elements 中的字段映射规则：
        
        1. 对于 elements 中的每一项：
           - 使用 `"path"` 作为 FHIR 字段路径，例如 "Observation.code"。
           - 将点号之后的部分作为 Python 字典的键。
           - 若字段类型为 "CodeableConcept"，生成格式如下：
             ```python
             "code": {
                 "coding": [{
                     "system": "<来自对应ValueSet的url或codeSystem的url>",
                     "code": "<映射得到的code>",
                     "display": "<映射得到的display>"
                 }]
             }
             ```
        
        2. 若元素的 constraint 包含 "from <ValueSetName> (required)"，
           则 system 字段必须使用该 ValueSet 的 url。
        
        3. 若元素的 type 为 "Reference(Patient)"，则：
           ```python
           "subject": {
               "reference": f"Patient/{patient_id}"
           }
        
        若元素的 path 以资源名开头（如 "Observation.valueCodeableConcept"），
        则该资源字典中应直接包含：
        "valueCodeableConcept": {
            "coding": [{
                "system": "<ValueSet系统URL>",
                "code": "<匹配code>",
                "display": "<显示名>"
            }]
        }
        
        每个生成的资源必须包含以下通用字段：
        "resourceType": "<Profile.parent>",
        "id": "<UUID>",
        "meta": {
            "profile": ["<Profile.url>"]
        },
        "status": "final"  # 若 applicable
        
        若 extract.profiles[i] 中存在 "parent": "Observation"，
        则需包含 Observation 常见字段：status, code, subject, value[x], effectiveDateTime 
        若 "parent": "Condition"：clinicalStatus, code, subject, onsetDateTime
        若 "parent": "Procedure"：status, code, subject, performedDateTime, bodySite
        若 elements.path 包含层级（如 "Procedure.bodySite.coding"），则需递归展开嵌套结构。

        八、示例
        我将为你提供三组extract和code的示例:
        示例1：
        extract_1 = '''
            {
              "result": {
                "valueSets": [
                  {
                    "id": "cnwqk75-anus-body-location-vs",
                    "title": "肛门部位解剖位置值集",
                    "description": "基于ICD-O-3的肛门部位编码值集",
                    "url": "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-body-location-vs",
                    "include": {
                      "system": "http://localhost:3456/api/terminology/CodeSystem/icdo3",
                      "regexFilter": "/C21\\.[0-8]/"
                    }
                  },
                  {
                    "id": "cnwqk75-anus-disease-vs",
                    "title": "肛门疾病诊断值集",
                    "description": "基于ICD-10的肛门疾病编码值集",
                    "url": "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-disease-vs",
                    "include": {
                      "system": "http://localhost:3456/api/terminology/CodeSystem/icd10",
                      "regexFilter": "/K62\\.[0-9]|C21\\.[0-9]|K62\\.5/"
                    }
                  },
                  {
                    "id": "cnwqk75-anus-surgery-vs",
                    "title": "肛门手术操作值集",
                    "description": "包含所有肛门手术操作编码的值集",
                    "url": "http://localhost:3456/api/terminology/ValueSet/cnwqk75-anus-surgery-vs",
                    "include": {
                      "system": "CNWQK75_AnusSurgeryCS"
                    }
                  }
                ],
                "codeSystems": [
                  {
                    "id": "cnwqk75-anus-surgery-cs",
                    "title": "肛门手术操作编码系统",
                    "description": "自定义肛门手术操作编码系统",
                    "url": "http://localhost:3456/api/terminology/CodeSystem/cnwqk75-anus-surgery-cs",
                    "caseSensitive": true,
                    "codes": [
                      {
                        "code": "ANS001",
                        "display": "肛门瘘管切除术",
                        "additionalDisplay": "痔疮手术"
                      },
                      {
                        "code": "ANS002",
                        "display": "肛门成形术"
                      },
                      {
                        "code": "ANS003",
                        "display": "肛门括约肌切开术"
                      },
                      {
                        "code": "ANS004",
                        "display": "痔切除术",
                        "additionalDisplay": "痔疮手术"
                      },
                      {
                        "code": "ANS005",
                        "display": "肛门脓肿引流术"
                      }
                    ]
                  }
                ],
                "profiles": [
                  {
                    "id": "cnwqk75-anus-surgery-patient",
                    "parent": "Procedure",
                    "title": "肛门手术患者规范",
                    "description": "定义接受肛门手术的患者资源规范",
                    "url": "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-surgery-patient",
                    "elements": [
                      {
                        "path": "status",
                        "constraint": "1..1"
                      },
                      {
                        "path": "code",
                        "constraint": "from CNWQK75_AnusSurgeryVS (required)"
                      },
                      {
                        "path": "bodySite",
                        "constraint": "from CNWQK75_AnusBodyLocationVS (required)"
                      },
                      {
                        "path": "subject",
                        "constraint": "1..1"
                      },
                      {
                        "path": "performed[x]",
                        "constraint": "1..1"
                      },
                      {
                        "path": "reasonCode",
                        "constraint": "from CNWQK75_AnusDiseaseVS"
                      },
                      {
                        "path": "note",
                        "constraint": "0..* MS"
                      }
                    ]
                  },
                  {
                    "id": "cnwqk75-anus-disease-patient",
                    "parent": "Condition",
                    "title": "肛门疾病患者规范",
                    "description": "定义肛门疾病患者的诊断资源规范",
                    "url": "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-disease-patient",
                    "elements": [
                      {
                        "path": "clinicalStatus",
                        "constraint": "1..1"
                      },
                      {
                        "path": "code",
                        "constraint": "from CNWQK75_AnusDiseaseVS (required)"
                      },
                      {
                        "path": "subject",
                        "constraint": "1..1"
                      },
                      {
                        "path": "onset[x]",
                        "constraint": "0..1"
                      },
                      {
                        "path": "note",
                        "constraint": "0..* MS"
                      }
                    ]
                  },
                  {
                    "id": "cnwqk75-clinical-note",
                    "parent": "Annotation",
                    "title": "临床注释规范",
                    "description": "定义临床文本注释的规范",
                    "url": "http://localhost:3456/api/terminology/Profile/cnwqk75-clinical-note",
                    "elements": [
                      {
                        "path": "text",
                        "constraint": "1..1"
                      },
                      {
                        "path": "time",
                        "constraint": "0..1"
                      },
                      {
                        "path": "author[x]",
                        "constraint": "0..1"
                      }
                    ]
                  }
                ]
              }
            }
            '''
            
            code_1 = '''
            import uuid
            import re
            from typing import List, Dict, Any
            
            # 定义映射字典
            SURGERY_MAPPING = {
                "痔疮手术": ("ANS004", "痔切除术"),
                "痔切除术": ("ANS004", "痔切除术"),
                "肛门瘘管切除术": ("ANS001", "肛门瘘管切除术"),
                "肛门成形术": ("ANS002", "肛门成形术"),
                "肛门括约肌切开术": ("ANS003", "肛门括约肌切开术"),
                "肛门脓肿引流术": ("ANS005", "肛门脓肿引流术"),
                "肛瘘手术": ("ANS001", "肛门瘘管切除术"),
                "肛周脓肿手术": ("ANS005", "肛门脓肿引流术")
            }
            
            DISEASE_MAPPING = {
                "肛门息肉": ("K62.8", "肛门息肉"),
                "肛裂": ("K62.8", "肛裂"),
                "肛门狭窄": ("K62.8", "肛门狭窄"),
                "肛门失禁": ("K62.8", "肛门失禁"),
                "肛门脓肿": ("K62.8", "肛门脓肿"),
                "肛门瘘": ("K62.8", "肛门瘘"),
                "肛门出血": ("K62.5", "肛门出血"),
                "便血": ("K62.5", "肛门出血"),
                "肛周脓肿": ("K62.8", "肛门脓肿"),
                "肛门恶性肿瘤": ("C21.1", "肛门恶性肿瘤"),
                "肛管癌": ("C21.2", "肛管恶性肿瘤"),
                "肛门癌": ("C21.1", "肛门恶性肿瘤")
            }
            
            BODY_SITE_MAPPING = {
                "肛门": ("C21.0", "肛门"),
                "肛管": ("C21.2", "肛管"),
                "肛缘": ("C21.8", "肛缘"),
                "直肠肛门": ("C21.0", "直肠肛门")
            }
            
            class FHIRResourceBundleGenerator:
                def __init__(self, fhir_api_base: str):
                    self.fhir_api_base = fhir_api_base
                
                def _extract_entities(self, text: str) -> dict:
                    '''从中文临床文本中提取手术、疾病和身体部位信息'''
                    results = {
                        "surgeries": [],
                        "diseases": [],
                        "body_sites": []
                    }
                    
                    # 提取手术信息
                    for term, (code, display) in SURGERY_MAPPING.items():
                        if term in text:
                            results["surgeries"].append({
                                "code": code,
                                "display": display,
                                "text": term
                            })
                    
                    # 提取疾病信息
                    for term, (code, display) in DISEASE_MAPPING.items():
                        if term in text:
                            results["diseases"].append({
                                "code": code,
                                "display": display,
                                "text": term
                            })
                    
                    # 提取身体部位信息
                    for term, (code, display) in BODY_SITE_MAPPING.items():
                        if term in text:
                            results["body_sites"].append({
                                "code": code,
                                "display": display,
                                "text": term
                            })
                    
                    return results
                
                def _create_procedure_resource(self, patient_id: str, report: dict, 
                                              surgery: dict, diseases: list) -> dict:
                    '''创建肛门手术Procedure资源'''
                    # 默认身体部位为肛门
                    body_site = {
                        "coding": [{
                            "system": "http://localhost:3456/api/terminology/CodeSystem/icdo3",
                            "code": "C21.0",
                            "display": "肛门"
                        }],
                        "text": "肛门"
                    }
                    
                    # 如果提取到具体身体部位则使用
                    if report.get("body_sites"):
                        body_site = {
                            "coding": [{
                                "system": "http://localhost:3456/api/terminology/CodeSystem/icdo3",
                                "code": report["body_sites"][0]["code"],
                                "display": report["body_sites"][0]["display"]
                            }],
                            "text": report["body_sites"][0]["text"]
                        }
                    
                    # 构建疾病原因编码
                    reason_codes = []
                    for disease in diseases:
                        reason_codes.append({
                            "coding": [{
                                "system": "http://localhost:3456/api/terminology/CodeSystem/icd10",
                                "code": disease["code"],
                                "display": disease["display"]
                            }],
                            "text": disease["text"]
                        })
                    
                    return {
                        "resourceType": "Procedure",
                        "id": str(uuid.uuid1()),
                        "meta": {
                            "profile": [
                                "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-surgery-patient"
                            ]
                        },
                        "status": "completed",
                        "code": {
                            "coding": [{
                                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk75-anus-surgery-cs",
                                "code": surgery["code"],
                                "display": surgery["display"]
                            }],
                            "text": surgery["text"]
                        },
                        "bodySite": [body_site],
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "performedDateTime": report["timestamp"],
                        "reasonCode": reason_codes,
                        "note": [{
                            "text": report["text"]
                        }]
                    }
                
                def _create_condition_resource(self, patient_id: str, report: dict, 
                                              disease: dict) -> dict:
                    '''创建肛门疾病Condition资源'''
                    return {
                        "resourceType": "Condition",
                        "id": str(uuid.uuid1()),
                        "meta": {
                            "profile": [
                                "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-disease-patient"
                            ]
                        },
                        "clinicalStatus": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                                "display": "现患"
                            }]
                        },
                        "code": {
                            "coding": [{
                                "system": "http://localhost:3456/api/terminology/CodeSystem/icd10",
                                "code": disease["code"],
                                "display": disease["display"]
                            }],
                            "text": disease["text"]
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "onsetDateTime": report["timestamp"],
                        "note": [{
                            "text": report["text"]
                        }]
                    }
                
                def parse_clinical_text_to_fhir_bundle(self, patient_id, case_reports, ai_algorithm_type="nlp"):
                    resources = []
                    
                    for report in case_reports:                        
                        # 提取实体信息
                        extracted = self._extract_entities(report["text"])
                        if not any(extracted.values()):  # 没有提取到任何信息
                            continue
                        
                        # 添加提取结果到报告信息中
                        processed_report = report.copy()
                        processed_report.update(extracted)
                        
                        # 创建手术资源
                        for surgery in processed_report["surgeries"]:
                            procedure = self._create_procedure_resource(
                                patient_id, processed_report, surgery, processed_report["diseases"]
                            )
                            resources.append(procedure)
                        
                        # 创建疾病资源
                        for disease in processed_report["diseases"]:
                            condition = self._create_condition_resource(
                                patient_id, processed_report, disease
                            )
                            resources.append(condition)
                    
                    # 构建Bundle
                    entries = []
                    for resource in resources:
                        entries.append({
                            "resource": resource,
                            "request": {
                                "method": "POST",
                                "url": resource["resourceType"]
                            }
                        })
                    
                    return {
                        "resourceType": "Bundle",
                        "type": "transaction",
                        "total": len(entries),
                        "entry": entries
                    }
            '''
        示例2：
        extract_2 = '''
            {
              "result": {
                "valueSets": [
                  {
                    "id": "cnwqk595-gerd-symptoms-vs",
                    "title": "GERD症状值集",
                    "description": "用于描述胃食管反流病（GERD）相关症状的值集，包含ICD-10和自定义编码。",
                    "url": "http://localhost:3456/api/terminology/ValueSet/cnwqk595-gerd-symptoms-vs",
                    "include": [
                      {
                        "system": "http://localhost:3456/api/terminology/CodeSystem/icd10",
                        "filter": "code = \"R12\""
                      },
                      {
                        "system": "Cnwqk595GerdSymptomsCS"
                      }
                    ]
                  }
                ],
                "codeSystems": [
                  {
                    "id": "cnwqk595-gerd-symptoms-cs",
                    "title": "GERD症状编码系统",
                    "description": "胃食管反流病（GERD）相关症状的自定义编码系统。",
                    "url": "http://localhost:3456/api/terminology/CodeSystem/cnwqk595-gerd-symptoms-cs",
                    "codes": [
                      {
                        "code": "heartburn",
                        "display": "烧心",
                        "additionalDisplay": "胸骨后烧灼感"
                      },
                      {
                        "code": "acid_regurgitation",
                        "display": "泛酸",
                        "additionalDisplay": "胃酸反流到口腔或喉咙"
                      },
                      {
                        "code": "retrosternal_burning_pain",
                        "display": "胸骨后灼痛",
                        "additionalDisplay": "胸骨后烧灼样疼痛"
                      },
                      {
                        "code": "coughing_when_lying_down",
                        "display": "平卧或睡眠时呛咳",
                        "additionalDisplay": "平卧或睡眠时发生的咳嗽"
                      },
                      {
                        "code": "throat_discomfort",
                        "display": "咽喉不适",
                        "additionalDisplay": "喉咙不适感"
                      }
                    ]
                  }
                ],
                "profiles": [
                  {
                    "id": "cnwqk595-gerd-symptoms-observation",
                    "parent": "Observation",
                    "title": "GERD症状观察量表Profile",
                    "description": "用于记录胃食管反流病（GERD）相关症状的Observation Profile。",
                    "url": "http://localhost:3456/api/terminology/Profile/cnwqk595-gerd-symptoms-observation",
                    "elements": [
                      {
                        "path": "status",
                        "constraint": "MS"
                      },
                      {
                        "path": "code",
                        "constraint": "MS"
                      },
                      {
                        "path": "code",
                        "constraint": "from Cnwqk595GerdSymptomsVS (required)"
                      },
                      {
                        "path": "subject",
                        "constraint": "MS"
                      },
                      {
                        "path": "value[x]",
                        "constraint": "MS"
                      },
                      {
                        "path": "value[x]",
                        "constraint": "only boolean"
                      },
                      {
                        "path": "valueBoolean",
                        "constraint": "1..1 MS"
                      }
                    ]
                  }
                ]
              }
            }
            '''
            code_2 = '''
            import uuid
            import re
            from datetime import datetime
            
            class FHIRResourceBundleGenerator:
                def __init__(self, fhir_api_base: str):
                    self.fhir_api_base = fhir_api_base
                    
                    # 症状代码映射
                    self.symptoms_mapping = {
                        "heartburn": {
                            "code": "heartburn",
                            "display": "烧心",
                            "keywords": ["烧心", "心口烧灼", "胸骨后烧灼", "胃灼热"]
                        },
                        "acid_regurgitation": {
                            "code": "acid_regurgitation",
                            "display": "泛酸",
                            "keywords": ["泛酸", "反酸", "胃酸反流", "酸水"]
                        },
                        "retrosternal_burning_pain": {
                            "code": "retrosternal_burning_pain",
                            "display": "胸骨后灼痛",
                            "keywords": ["胸骨后灼痛", "胸骨后疼痛", "胸骨后烧灼痛", "胸痛"]
                        },
                        "coughing_when_lying_down": {
                            "code": "coughing_when_lying_down",
                            "display": "平卧或睡眠时呛咳",
                            "keywords": ["平卧呛咳", "睡眠呛咳", "卧位咳嗽", "躺下咳嗽", "夜间咳嗽"]
                        },
                        "throat_discomfort": {
                            "code": "throat_discomfort",
                            "display": "咽喉不适",
                            "keywords": ["咽喉不适", "喉咙不适", "咽部异物感", "喉部不适", "咽痛"]
                        }
                    }
                    
                    # 否定词列表
                    self.negation_terms = ["无", "没有", "未", "否认", "不", "从未", "从来没", "否", "未见", "排除"]
                    
                    # 症状编码系统URL
                    self.symptoms_cs_url = "http://localhost:3456/api/terminology/CodeSystem/cnwqk595-gerd-symptoms-cs"
                    self.icd10_url = "http://localhost:3456/api/terminology/CodeSystem/icd10"
            
                def check_negation(self, text, keyword, window_size=15):
                    '''
                    检查关键词附近是否有否定词
                    '''
                    # 找到所有关键词出现的位置
                    positions = [m.start() for m in re.finditer(keyword, text)]
                    
                    for pos in positions:
                        # 确定检查窗口
                        start = max(0, pos - window_size)
                        end = min(len(text), pos + len(keyword) + window_size)
                        window_text = text[start:end]
                        
                        # 检查窗口中是否有否定词
                        for negation in self.negation_terms:
                            if negation in window_text:
                                return True
                                
                    return False
            
                def parse_clinical_text_to_fhir_bundle(self, patient_id, case_reports, ai_algorithm_type="nlp"):
                    '''
                    从临床文本中提取GERD症状信息并生成FHIR Bundle
                    '''
                    entries = []
                    
                    for report in case_reports:
                        text = report.get("text", "")
                        timestamp = report.get("timestamp", "")
                            
                        # 检查每个症状
                        for symptom_key, symptom_info in self.symptoms_mapping.items():
                            symptom_found = False
                            symptom_negated = False
                            
                            # 检查每个关键词
                            for keyword in symptom_info["keywords"]:
                                if keyword in text:
                                    symptom_found = True
                                    if self.check_negation(text, keyword):
                                        symptom_negated = True
                                    else:
                                        # 只要有一个关键词没有被否定，就认为症状存在
                                        symptom_negated = False
                                        break
                            
                            # 如果找到症状，创建Observation资源
                            if symptom_found:
                                # 生成唯一ID
                                observation_id = str(uuid.uuid1())
                                
                                # 创建Observation资源
                                observation = {
                                    "resourceType": "Observation",
                                    "id": observation_id,
                                    "meta": {
                                        "profile": [
                                            "http://localhost:3456/api/terminology/Profile/cnwqk595-gerd-symptoms-observation"
                                        ]
                                    },
                                    "text": {
                                        "status": "generated",
                                        "div": f"从文本『{text}』中提取到症状『{symptom_info['display']}』，否定状态：{'是' if symptom_negated else '否'}"
                                    },
                                    "status": "final",
                                    "code": {
                                        "coding": [
                                            {
                                                "system": self.symptoms_cs_url,
                                                "code": symptom_info["code"],
                                                "display": symptom_info["display"]
                                            }
                                        ],
                                        "text": symptom_info["display"]
                                    },
                                    "subject": {
                                        "reference": f"Patient/{patient_id}"
                                    },
                                    "effectiveDateTime": timestamp,
                                    "valueBoolean": not symptom_negated
                                }
                                
                                # 如果是烧心症状，添加ICD-10编码
                                if symptom_key == "heartburn":
                                    observation["code"]["coding"].append({
                                        "system": self.icd10_url,
                                        "code": "R12",
                                        "display": "烧心"
                                    })
                                
                                # 创建Bundle entry
                                entry = {
                                    "resource": observation,
                                    "request": {
                                        "method": "POST",
                                        "url": "Observation"
                                    }
                                }
                                
                                entries.append(entry)
                    
                    # 创建Bundle
                    bundle = {
                        "resourceType": "Bundle",
                        "type": "transaction",
                        "total": len(entries),
                        "entry": entries
                    }
                    
                    return bundle
            '''
        示例3：
        extract_3 = '''
            {
              "result": {
                "valueSets": [
                  {
                    "id": "cnwqk815-SmokingStatusValueSet",
                    "title": "吸烟状态值集",
                    "description": "包含吸烟状态所有可能值的值集。",
                    "url": "http://localhost:3456/api/terminology/ValueSet/cnwqk815-SmokingStatusValueSet",
                    "include": {
                      "system": "SmokingStatusCodeSystem"
                    }
                  }
                ],
                "codeSystems": [
                  {
                    "id": "cnwqk815-SmokingStatusCodeSystem",
                    "title": "吸烟状态代码系统",
                    "description": "用于表示吸烟状态的代码系统。",
                    "url": "http://localhost:3456/api/terminology/CodeSystem/cnwqk815-SmokingStatusCodeSystem",
                    "codes": [
                      {
                        "code": "non_smoker",
                        "display": "不吸烟"
                      },
                      {
                        "code": "current_smoker",
                        "display": "当前吸烟"
                      },
                      {
                        "code": "former_smoker",
                        "display": "以前吸烟"
                      }
                    ]
                  }
                ],
                "profiles": [
                  {
                    "id": "cnwqk815-SmokingStatusProfile",
                    "parent": "Observation",
                    "title": "吸烟状态观察剖面",
                    "description": "用于表示患者吸烟状态的观察剖面。",
                    "url": "http://localhost:3456/api/terminology/Profile/cnwqk815-SmokingStatusProfile",
                    "elements": [
                      {
                        "path": "status",
                        "constraint": "1..1"
                      },
                      {
                        "path": "code",
                        "constraint": "= http://loinc.org#72166-2 \"吸烟状态\""
                      },
                      {
                        "path": "code",
                        "constraint": "1..1"
                      },
                      {
                        "path": "subject",
                        "constraint": "1..1"
                      },
                      {
                        "path": "valueCodeableConcept",
                        "constraint": "1..1"
                      },
                      {
                        "path": "valueCodeableConcept",
                        "constraint": "from SmokingStatusValueSet (required)"
                      }
                    ]
                  }
                ]
              }
            }
            '''
            code_3 = '''
            # 2024-06-20 GPT-4o 本代码用于从临床文本中提取吸烟状态信息并生成FHIR Bundle资源
            import uuid
            import re
            import json
            from datetime import datetime
            
            class FHIRResourceBundleGenerator:
                def __init__(self, fhir_api_base: str):
                    self.fhir_api_base = fhir_api_base
                    # 定义吸烟状态模式
                    self.non_smoker_patterns = [r'不吸烟', r'从未吸烟', r'无吸烟史', r'没有吸烟', r'不抽烟', r'无抽烟',r'否认吸烟史']
                    self.former_smoker_patterns = [r'戒烟', r'曾吸烟', r'过去吸烟', r'以前吸烟', r'戒烟']
                    self.current_smoker_patterns = [r'吸烟', r'抽烟', r'吸咽', r'吸烟史']
                    # 否定词模式
                    self.negation_patterns = [r'无', r'否', r'否认', r'未', r'没有', r'不', r'从未', r'没']
            
                def check_negation(self, text, start_index, window_size=10):
                    '''检查文本中指定位置前是否有否定词'''
                    # 提取匹配位置前的文本窗口
                    window_start = max(0, start_index - window_size)
                    preceding_text = text[window_start:start_index]
                    
                    # 检查窗口中是否有否定词
                    for pattern in self.negation_patterns:
                        if re.search(pattern, preceding_text):
                            return True
                    return False
            
                def determine_smoking_status(self, text):
                    '''从文本中确定吸烟状态'''
                    # 首先检查不吸烟模式
                    for pattern in self.non_smoker_patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            # 对于不吸烟模式，通常不需要检查否定词，因为模式本身已包含否定含义
                            return 'non_smoker'
                    
                    # 检查以前吸烟模式
                    for pattern in self.former_smoker_patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            if not self.check_negation(text, match.start()):
                                return 'former_smoker'
                    
                    # 检查当前吸烟模式
                    for pattern in self.current_smoker_patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            if not self.check_negation(text, match.start()):
                                return 'current_smoker'
                    
                    return None
            
                def parse_clinical_text_to_fhir_bundle(self, patient_id, case_reports, ai_algorithm_type="nlp"):
                    '''从临床文本中解析吸烟状态并生成FHIR Bundle'''
                    # 初始化变量
                    smoking_status = None
                    effective_date_time = None
                    source_text = ""
                    
                    # 遍历所有病例报告，查找吸烟状态信息
                    for report in case_reports:
                        text = report.get('text', '')
                        timestamp = report.get('timestamp', '')
                        
                        # 确定吸烟状态
                        status = self.determine_smoking_status(text)
                        if status:
                            smoking_status = status
                            effective_date_time = timestamp if timestamp else datetime.now().isoformat()
                            source_text = text
                            break  # 找到第一个匹配即停止
                    
                    # 如果没有找到吸烟状态信息，返回空Bundle
                    if not smoking_status:
                        return {
                            "resourceType": "Bundle",
                            "type": "transaction",
                            "total": 0,
                            "entry": []
                        }
                    
                    # 映射吸烟状态代码
                    status_map = {
                        'non_smoker': {'code': 'non_smoker', 'display': '不吸烟'},
                        'former_smoker': {'code': 'former_smoker', 'display': '以前吸烟'},
                        'current_smoker': {'code': 'current_smoker', 'display': '当前吸烟'}
                    }
                    
                    status_info = status_map[smoking_status]
                    
                    # 生成Observation资源
                    observation_id = str(uuid.uuid1())
                    observation = {
                        "resourceType": "Observation",
                        "id": observation_id,
                        "meta": {
                            "profile": [
                                "http://localhost:3456/api/terminology/Profile/cnwqk815-SmokingStatusProfile"
                            ]
                        },
                        "text": {
                            "status": "generated",
                            "div": f"文本摘录：{source_text[:100]}..."  # 截取前100个字符
                        },
                        "status": "final",
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "72166-2",
                                    "display": "吸烟状态"
                                }
                            ],
                            "text": "吸烟状态"
                        },
                        "subject": {
                            "reference": f"Patient/{patient_id}"
                        },
                        "effectiveDateTime": effective_date_time,
                        "valueCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk815-SmokingStatusCodeSystem",
                                    "code": status_info['code'],
                                    "display": status_info['display']
                                }
                            ],
                            "text": status_info['display']
                        }
                    }
                    
                    # 创建Bundle
                    bundle = {
                        "resourceType": "Bundle",
                        "type": "transaction",
                        "total": 1,
                        "entry": [
                            {
                                "resource": observation,
                                "request": {
                                    "method": "POST",
                                    "url": "Observation"
                                }
                            }
                        ]
                    }
                    
                    return bundle
            '''
        """,

    "step_3_params":
        '''
        ------------------输入的FHIR提取信息如下所示：--------------------
        {FHIR_FSH}
        ------------- ----请输出可执行的Python代码：---------------------
        '''
}
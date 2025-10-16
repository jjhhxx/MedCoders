
prompt_conf = {
    "step_1_extract_input_information":
        '''
        任务1：输入信息解析与核心要素提取
        目标：从label、question、FHIR_FSH中提取生成Python代码需用到的核心要素，包括「临床问题核心对象」「FHIR配置信息」「待提取字段」。
        输入格式：
        - label：{{问题类型，如“临床病史提取”}}
        - question：{{用户关注的临床问题，如“提取患者吸烟史信息”}}
        - FHIR_FSH：{{FHIR Shorthand代码，定义Observation资源的Profile、CodeSystem}}
        
        输出格式：
        {{
            "result":{{
                "question_core_obj": "提取的临床问题主体（如“吸烟史”）",
                "FHIR_configuration": {{
                    "observation_profile_url": "FHIR_FSH中定义的Observation Profile URL",
                    "main_code_system": "FHIR_FSH中定义的主CodeSystem URL",
                    "main_code": "FHIR_FSH中对应临床问题的主Code（如“tobacco-use”）",
                    "main_code_display": "主Code的显示名（如“烟草使用史”）",
                    "component_codes": [
                      {{
                        "code": "FHIR_FSH中定义的组件Code（如“tobacco-use-status”）",
                        "display": "组件显示名（如“吸烟史状态”）",
                        "value_type": "组件值类型（如“CodeableConcept”“Quantity”）"
                      }}
                    ]
                }},
                "extract_fields4text": ["从病例中需提取的字段（如“有无吸烟史”“吸烟年限”“每日吸烟量”）"]          # 待提取字段
            }}
        }}
        
        Few-shot示例：
        输入：
        - label：临床病史提取
        - question：提取患者饮酒史信息
        - FHIR_FSH：
          Profile: AlcoholConsumptionObservation
          Parent: Observation
          Id: cnwqk435-alcohol-consumption
          Title: "酒精消费观察"
          * meta.profile = "http://localhost:3456/api/terminology/Profile/cnwqk435-alcohol-consumption"
          * code.coding[0] = http://localhost:3456/api/terminology/CodeSystem/cnwqk435-observation-cs#alcohol-consumption "酒精消费"
          * component[0].code = http://localhost:3456/api/terminology/CodeSystem/cnwqk435-component-cs#drinking-history-status "饮酒史状态"
          * component[0].value[x] = CodeableConcept
          * component[1].code = http://localhost:3456/api/terminology/CodeSystem/cnwqk435-component-cs#duration-of-drinking "饮酒持续时间"
          * component[1].value[x] = Quantity
        
        输出：
            {{
                "result": {{
                    "question_core_obj": "饮酒史",      # 临床问题核心对象
                    "FHIR_configuration": {{          # FHIR配置信息
                        "observation_profile_url": "http://localhost:3456/api/terminology/Profile/cnwqk435-alcohol-consumption",
                        "main_code_system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-observation-cs",
                        "main_code": "alcohol-consumption",
                        "main_code_display": "酒精消费",
                        "component_codes": [
                          {{
                            "code": "drinking-history-status",
                            "display": "饮酒史状态",
                            "value_type": "CodeableConcept"
                          }},
                          {{
                            "code": "duration-of-drinking",
                            "display": "饮酒持续时间",
                            "value_type": "Quantity"
                          }}
                        ]
                    }},
                    "extract_fields4text": ["有无饮酒史", "饮酒持续时间", "每日酒精摄入量", "酒类类型"]
                }}
            }}
        
        请基于以下输入完成本任务：
        - label：{label}
        - question：{question}
        - FHIR_FSH：{FHIR_FSH}
        ''',

    "step_2_define_rule":
        '''
        任务2：临床文本提取规则设计
        目标：针对子任务1提取的“临床问题核心对象”和“待提取字段”，设计3类规则：① 相关性判断规则（判断病例是否含该临床问题）；② 字段提取规则（提取待提取字段的关键词/正则）；③ 否定逻辑规则（避免误判否定表述）。
        输入：子任务1的输出结果（临床问题核心对象、待提取字段）
        
        输出格式：
        {{
            "result": {{
              "correlation_judgment_rule": {{
                "核心关键词列表": ["判断病例是否含该临床问题的正向关键词（如“吸烟”“烟史”“卷烟”）"],
                "判断逻辑": "若病例文本包含任一核心关键词，则判定为“与临床问题相关”，进入后续提取；否则跳过"
              }},
              "extraction_rules": [
                {{
                  "字段名": "待提取字段（如“有无吸烟史”）",
                  "提取方式": "关键词匹配/正则匹配",
                  "具体规则": ["关键词列表（如“有吸烟史”“否认吸烟”）" / "正则模式（如r'吸烟[已约有]?(\d+)年'）"]
                }}
              ],
              "neg_logic_rule": {{
                "否定关键词列表": ["表示否定该临床问题的词（如“无”“不”“戒”“否认”）"],
                "否定模式列表": ["固定否定表述（如“无吸烟史”“已戒烟”）"],
                "否定判断逻辑": "若病例含否定模式，或否定关键词与核心关键词距离≤5个字符（避免误判无关否定），则判定为“无该临床问题史”"
              }}
            }}
        }}
        
        Few-shot示例：
        输入：子任务1输出中“临床问题核心对象=饮酒史，待提取字段=[有无饮酒史，饮酒持续时间，每日酒精摄入量，酒类类型]”
        
        输出：
        {{
            "result": {{
                "correlation_judgment_rule": {{        # 1. 相关性判断规则
                    "核心关键词列表": ["饮酒", "喝酒", "酒精", "酒", "酗酒", "嗜酒", "白酒", "啤酒", "葡萄酒"],
                    "判断逻辑": "若病例文本包含任一核心关键词，则判定为“与饮酒史相关”，进入后续提取；否则跳过"
                }},
                "extraction_rules": [       # 2. 待提取字段提取规则
                {{
                  "字段名": "有无饮酒史",
                  "提取方式": "关键词匹配+否定逻辑",
                  "具体规则": ["正向关键词：有饮酒史、饮酒多年；否定关键词：无饮酒史、不饮酒、戒酒"]
                }},
                {{
                  "字段名": "饮酒持续时间",
                  "提取方式": "正则匹配",
                  "具体规则": ["r'饮酒[已约有]?(\d+)年'，r'喝酒[已约有]?(\d+)余年'，r'饮酒≥(\d+)年'"]
                }},
                {{
                  "字段名": "每日酒精摄入量",
                  "提取方式": "正则匹配",
                  "具体规则": ["r'每日饮酒(\d+)(两|杯|ml)'，r'饮酒量(\d+)(g|克)/天'"]
                }},
                {{
                  "字段名": "酒类类型",
                  "提取方式": "关键词匹配",
                  "具体规则": ["白酒", "啤酒", "葡萄酒", "红酒", "黄酒", "洋酒"]
                }}
                ],
                "neg_logic_rule": {{         # 3. 否定逻辑规则
                "否定关键词列表": ["无", "不", "否认", "未", "拒绝", "戒", "禁", "从不", "不嗜"],
                "否定模式列表": ["无饮酒史", "不饮酒", "戒酒", "禁酒", "拒绝饮酒", "否认饮酒", "从不饮酒"],
                "否定判断逻辑": "若病例含否定模式，或否定关键词与核心关键词距离≤5个字符，则判定为“无饮酒史”"
                }}
            }}
        }}
        
        请基于以下输入完成本任务：
        子任务1输出结果：{result_by_step_1}
        ''',

    "step_3_class_init":
        '''
        任务3：__init__方法初始化逻辑生成
        目标：生成FHIRResourceBundleGenerator类的__init__方法代码，需初始化2类变量：① FHIR相关配置（从子任务1提取）；② 文本提取规则（从子任务2提取），变量名需与后续方法复用。
        输入：
        1. 子任务1输出的“FHIR配置信息”
        2. 子任务2输出的“提取规则”（核心关键词、否定词、否定模式、正则等）
        
        输出格式：
        直接输出__init__方法的Python代码，需满足：
        - 参数仅保留fhir_api_base: str（按用户要求）；
        - 用self.xxx定义实例变量，变量名清晰（如self.fhir_observation_profile、self.core_keywords）；
        - 若有单位转换需求（如“两→ml”），需在__init__中定义单位映射表（参考示例）。
        
        Few-shot示例：
        输入1（FHIR配置）：
        {{
          "observation_profile_url": "http://localhost:3456/api/terminology/Profile/cnwqk435-alcohol-consumption",
          "main_code_system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-observation-cs",
          "main_code": "alcohol-consumption",
          "main_code_display": "酒精消费",
          "component_codes": [
            {{"code": "drinking-history-status", "display": "饮酒史状态", "value_type": "CodeableConcept"}},
            {{"code": "duration-of-drinking", "display": "饮酒持续时间", "value_type": "Quantity"}}
          ]
        }}
        输入2（提取规则）：
        核心关键词列表：["饮酒", "喝酒", "酒精", "酒"]；否定关键词列表：["无", "不", "否认", "戒"]；否定模式列表：["无饮酒史", "不饮酒"]；每日摄入量需单位转换。
        
        输出代码：
        ```python
            def __init__(self, fhir_api_base: str):
                self.fhir_api_base = fhir_api_base  # FHIR服务器基础地址（预留扩展）
                # 1. FHIR配置信息初始化（来自子任务1）
                self.fhir_observation_profile = "http://localhost:3456/api/terminology/Profile/cnwqk435-alcohol-consumption"
                self.main_code_system = "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-observation-cs"
                self.main_code = "alcohol-consumption"
                self.main_code_display = "酒精消费"
                # 组件Code配置（对应待提取字段）
                self.component_code_map = {{
                    "drinking-history-status": {{"display": "饮酒史状态", "value_type": "CodeableConcept"}},
                    "duration-of-drinking": {{"display": "饮酒持续时间", "value_type": "Quantity"}}
                }}
                
                # 2. 文本提取规则初始化（来自子任务2）
                self.core_keywords = ["饮酒", "喝酒", "酒精", "酒", "酗酒", "嗜酒", "白酒", "啤酒", "葡萄酒"]  # 相关性判断关键词
                self.negative_keywords = ["无", "不", "否认", "未", "拒绝", "戒", "禁", "从不", "不嗜"]  # 否定关键词
                self.negative_patterns = ["无饮酒史", "不饮酒", "戒酒", "禁酒", "拒绝饮酒", "否认饮酒", "从不饮酒"]  # 固定否定模式
                
                # 3. 单位转换映射（针对“每日酒精摄入量”字段）
                self.unit_convert_map = {{
                    "ml": 1.0, "毫升": 1.0, "两": 50.0, "杯": 150.0, "瓶": 500.0,
                    "听": 330.0, "罐": 330.0, "g": 1.25, "克": 1.25
                }}
                # 酒类酒精含量（体积百分比）
                self.alcohol_content_map = {{
                    "白酒": 0.40, "啤酒": 0.05, "葡萄酒": 0.12, "红酒": 0.12, "黄酒": 0.15, "洋酒": 0.40, "default": 0.40
                }}
        ```
        
        请基于以下输入完成本任务：
        1. 子任务1输出的“FHIR配置信息”：{result_by_step_1}
        2. 子任务2输出的“提取规则”：{result_by_step_2}
        ''',

    "step_4_class_core_code":
        '''
        任务4：核心辅助方法生成
        目标：生成2个Python辅助方法，需与子任务3的__init__变量复用，且符合FHIR_FSH定义：
        1. _extract_clinical_info(text: str) -> Dict[str, Any]：输入单条病例文本，输出提取的待提取字段结果（如{{"has_history": True, "duration": 5}}）；
        2. _create_observation(patient_id: str, text: str, timestamp: str, clinical_info: Dict[str, Any]) -> Dict[str, Any]：输入患者ID、病例文本、时间戳、提取结果，输出符合FHIR_FSH的Observation资源字典。
        
        输入：
        1. 子任务1输出（临床问题核心对象、待提取字段、FHIR配置信息）
        2. 子任务3输出的__init__方法代码（参考变量名）
        3. 子任务2输出的提取规则
        
        输出格式：
        直接输出2个辅助方法的完整Python代码，需满足：
        - _extract_clinical_info：包含“相关性判断→否定判断→字段提取”逻辑，用子任务2的规则；
        - _create_observation：包含Observation的resourceType、id、meta.profile、code、subject、effectiveDateTime、component（按子任务1的component_codes）。
        
        Few-shot示例：
        输入1（子任务1关键信息）：临床问题核心对象=饮酒史，待提取字段=[有无饮酒史，饮酒持续时间，每日酒精摄入量，酒类类型]，FHIR配置见子任务1示例；
        输入2（__init__变量）：self.core_keywords、self.negative_patterns、self.unit_convert_map等；
        输入3（提取规则）：子任务2饮酒史规则。
        
        输出代码：
        ```python
            def _extract_clinical_info(self, text: str) -> Dict[str, Any]:
                """从病例文本中提取饮酒史相关信息"""
                result = {{
                    "has_history": None,  # True/False/None（None表示无相关信息）
                    "duration": None,     # 饮酒持续时间（年）
                    "daily_intake": None, # 每日纯酒精摄入量（克/天）
                    "alcohol_type": None  # 酒类类型
                }}
                
                # 1. 相关性判断：无核心关键词则返回空结果
                if not any(keyword in text for keyword in self.core_keywords):
                    return result
                
                # 2. 否定判断：含否定模式或上下文否定则标记为无饮酒史
                has_explicit_negative = any(re.search(pattern, text) for pattern in self.negative_patterns)
                has_context_negative = False
                for neg_word in self.negative_keywords:
                    # 检查否定词与核心关键词距离≤5字符（避免误判）
                    neg_positions = [m.start() for m in re.finditer(neg_word, text)]
                    core_positions = [m.start() for m in re.finditer('|'.join(self.core_keywords), text)]
                    if any(abs(n - c) <= 5 for n in neg_positions for c in core_positions):
                        has_context_negative = True
                        break
                if has_explicit_negative or has_context_negative:
                    result["has_history"] = False
                    return result
                
                # 3. 有饮酒史：提取各字段（按子任务2规则）
                result["has_history"] = True
                # 提取酒类类型
                alcohol_types = ["白酒", "啤酒", "葡萄酒", "红酒", "黄酒", "洋酒"]
                for a_type in alcohol_types:
                    if a_type in text:
                        result["alcohol_type"] = a_type
                        break
                # 提取饮酒持续时间（正则匹配）
                duration_patterns = [r'饮酒[已约有]?(\d+)年', r'喝酒[已约有]?(\d+)余年', r'饮酒≥(\d+)年']
                for pattern in duration_patterns:
                    match = re.search(pattern, text)
                    if match:
                        result["duration"] = int(match.group(1))
                        break
                # 提取每日酒精摄入量（正则匹配+单位转换）
                intake_patterns = [r'饮酒(\d+)(两|杯|ml)/天', r'每日饮酒(\d+)(g|克)', r'饮酒量(\d+)(ml|两)']
                for pattern in intake_patterns:
                    match = re.search(pattern, text)
                    if match:
                        value = float(match.group(1))
                        unit = match.group(2)
                        alcohol_type = result["alcohol_type"] or "default"
                        # 单位转换：转为毫升
                        ml_value = value * self.unit_convert_map.get(unit, 1.0)
                        # 计算纯酒精克数（体积×酒精含量×0.8g/ml）
                        alcohol_percent = self.alcohol_content_map.get(alcohol_type, 0.40)
                        pure_alcohol_g = ml_value * alcohol_percent * 0.8
                        result["daily_intake"] = round(pure_alcohol_g, 2)
                        break
                return result
            
            def _create_observation(self, patient_id: str, text: str, timestamp: str, clinical_info: Dict[str, Any]) -> Dict[str, Any]:
                """创建符合酒精消费Profile的Observation资源"""
                import uuid  # 确保导入uuid
                observation_id = str(uuid.uuid1())
                observation = {{
                    "resourceType": "Observation",
                    "id": observation_id,
                    "meta": {{
                        "profile": [self.fhir_observation_profile]  # 复用__init__中的FHIR Profile
                    }},
                    "text": {{
                        "status": "generated",
                        "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">病例文本摘录：{{text}}</div>"
                    }},
                    "status": "final",
                    "code": {{
                        "coding": [
                            {{
                                "system": self.main_code_system,
                                "code": self.main_code,
                                "display": self.main_code_display
                            }}
                        ],
                        "text": self.main_code_display
                    }},
                    "subject": {{
                        "reference": f"Patient/{{patient_id}}"
                    }},
                    "effectiveDateTime": timestamp,
                    "component": []
                }}
                
                # 添加“饮酒史状态”组件（CodeableConcept）
                history_status_comp = {{
                    "code": {{
                        "coding": [
                            {{
                                "system": self.main_code_system.replace("observation-cs", "component-cs"),  # 组件CodeSystem（复用主CodeSystem逻辑）
                                "code": "drinking-history-status",
                                "display": self.component_code_map["drinking-history-status"]["display"]
                            }}
                        ],
                        "text": self.component_code_map["drinking-history-status"]["display"]
                    }}
                }}
                if clinical_info["has_history"] is False:
                    history_status_comp["valueCodeableConcept"] = {{
                        "coding": [{{"system": f"{{self.main_code_system.replace('observation-cs', 'alcohol-history-cs')}}", "code": "no-history", "display": "无饮酒史"}}],
                        "text": "无饮酒史"
                    }}
                elif clinical_info["has_history"] is True:
                    history_status_comp["valueCodeableConcept"] = {{
                        "coding": [{{"system": f"{{self.main_code_system.replace('observation-cs', 'alcohol-history-cs')}}", "code": "yes-history", "display": "有饮酒史"}}],
                        "text": "有饮酒史"
                    }}
                observation["component"].append(history_status_comp)
                
                # 有饮酒史时，添加“饮酒持续时间”组件（Quantity）
                if clinical_info["has_history"] is True and clinical_info["duration"] is not None:
                    duration_comp = {{
                        "code": {{
                            "coding": [
                                {{
                                    "system": self.main_code_system.replace("observation-cs", "component-cs"),
                                    "code": "duration-of-drinking",
                                    "display": self.component_code_map["duration-of-drinking"]["display"]
                                }}
                            ],
                            "text": self.component_code_map["duration-of-drinking"]["display"]
                        }},
                        "valueQuantity": {{
                            "value": clinical_info["duration"],
                            "unit": "年",
                            "system": "http://unitsofmeasure.org",
                            "code": "a"
                        }}
                    }}
                    observation["component"].append(duration_comp)
                
                # 有饮酒史时，添加“每日纯酒精摄入”组件（Quantity）
                if clinical_info["has_history"] is True and clinical_info["daily_intake"] is not None:
                    intake_comp = {{
                        "code": {{
                            "coding": [
                                {{
                                    "system": self.main_code_system.replace("observation-cs", "component-cs"),
                                    "code": "average-alcohol-intake",
                                    "display": "平均纯酒精摄入"
                                }}
                            ],
                            "text": "平均纯酒精摄入"
                        }},
                        "valueQuantity": {{
                            "value": clinical_info["daily_intake"],
                            "unit": "克/天",
                            "system": "http://unitsofmeasure.org",
                            "code": "g/d"
                        }}
                    }}
                    observation["component"].append(intake_comp)
                
                return observation
        ```
        
        请基于以下输入完成本任务：
        1. 子任务1输出：{result_by_step_1}
        2. 子任务3输出的__init__代码：{result_by_step_3}
        3. 子任务2输出的提取规则：{result_by_step_2}
        ''',

    "step_5_class_complete":
        '''
        任务5：完整FHIRResourceBundleGenerator类整合
        目标：整合前4个子任务成果，生成可直接运行的Python类。需包含「必要导入→类定义→__init__初始化→核心辅助方法→主处理方法」，实现“多份病例文本输入→提取临床信息→生成符合FHIR标准的Observation资源→组装成Transaction类型Bundle”的端到端流程，重点补全主方法parse_clinical_text_to_fhir_bundle。
        输入：
        1. 子任务3输出的__init__方法代码（初始化FHIR配置与提取规则）
        2. 子任务4输出的2个核心辅助方法代码（_extract_clinical_info、_create_observation）
        3. 子任务1输出的“临床问题核心对象”“FHIR配置信息”（确保Bundle与Observation结构匹配）
        4. 子任务2输出的提取规则（主方法需复用否定/相关性判断逻辑）
        
        输出格式：
        完整Python代码，需满足以下结构与要求：
        1. 开头导入依赖库（re、uuid、datetime、Dict/Any类型标注）；
        2. 类FHIRResourceBundleGenerator内包含4个方法：
           - __init__：子任务3成果，初始化配置与规则；
           - _extract_clinical_info：子任务4成果，提取临床字段；
           - _create_observation：子任务4成果，生成Observation资源；
           - parse_clinical_text_to_fhir_bundle（主方法）：新补全方法，需实现“Bundle初始化→遍历病例→调用辅助方法→组装资源→统计总数”逻辑；
        3. 主方法要求：
           - 参数：patient_id（患者唯一标识）、case_reports（病例列表，格式如[{{"text":"病例文本1","timestamp":"2024-10-01T10:00:00Z"}},...]）、ai_algorithm_type（默认"nlp"，标识提取算法）；
           - 返回值：FHIR Bundle字典（类型transaction，含entry列表与total计数）；
           - 逻辑：跳过无相关信息的病例，仅将有效Observation加入Bundle，每个entry需含resource和request（method=POST，url=Observation）。
    
    
        Few-shot示例（以“饮酒史提取”为例，展示主方法核心逻辑）：
        # 参考主方法实现（饮酒史场景）
        ```python
            def parse_clinical_text_to_fhir_bundle(self, patient_id: str, case_reports: List[Dict[str, str]], ai_algorithm_type: str = "nlp") -> Dict[str, Any]:
                """
                主方法：从多份病例文本生成含饮酒史Observation的FHIR Bundle
                :param patient_id: 患者ID（如"pat-001"）
                :param case_reports: 病例列表，每个元素含"text"（病例文本）和"timestamp"（时间戳，如"2024-10-01T10:00:00Z"）
                :param ai_algorithm_type: 提取算法类型，默认nlp
                :return: FHIR Bundle（transaction类型）
                """
                # 1. 初始化FHIR Bundle基础结构
                fhir_bundle = {{
                    "resourceType": "Bundle",
                    "type": "transaction",  # 批量提交类型
                    "total": 0,  # 有效资源总数，后续动态更新
                    "entry": []  # 资源列表
                }}
        
                # 2. 遍历每一份病例，提取信息并生成Observation
                for report in case_reports:
                    case_text = report.get("text", "").strip()
                    case_timestamp = report.get("timestamp", datetime.now().isoformat() + "Z")  # 默认当前时间
                    
                    # 3. 调用辅助方法提取临床信息（饮酒史）
                    clinical_info = self._extract_clinical_info(case_text)
                    
                    # 4. 跳过无相关信息的病例（has_history为None时无有效数据）
                    if clinical_info.get("has_history") is None:
                        continue
                    
                    # 5. 调用辅助方法生成Observation资源
                    observation_resource = self._create_observation(
                        patient_id=patient_id,
                        text=case_text,
                        timestamp=case_timestamp,
                        clinical_info=clinical_info
                    )
                    
                    # 6. 将Observation加入Bundle的entry，配置POST请求
                    fhir_bundle["entry"].append({{
                        "resource": observation_resource,
                        "request": {{
                            "method": "POST",  # FHIR批量提交常用方法
                            "url": "Observation"  # 资源类型，与Observation对应
                        }}
                    }})
        
                # 7. 更新Bundle的有效资源总数
                fhir_bundle["total"] = len(fhir_bundle["entry"])
        
                return fhir_bundle
        ```
    
    
        请基于以下输入完成本任务：
        1. 子任务3的__init__方法代码：{result_by_step_3}
        2. 子任务4的2个辅助方法代码：{result_by_step_4}
        3. 子任务1的关键信息：问题类型={label}，临床问题核心对象={question}，FHIR配置信息={FHIR_FSH}
        ''',
}

import re
import uuid
from datetime import datetime
from typing import Dict, Any, List


class FHIRResourceBundleGenerator:
    def __init__(self, fhir_api_base: str):
        self.fhir_api_base = fhir_api_base  # FHIR服务器基础地址（预留扩展）

        # 1. FHIR配置信息初始化（来自子任务1）
        self.fhir_observation_profile = "http://localhost:3456/api/terminology/Profile/cnwqk75-anus-surgery-patient"
        self.main_code_system = "http://localhost:3456/api/terminology/CodeSystem/cnwqk75-anus-surgery-cs"
        self.main_code = "ANS001"
        self.main_code_display = "肛门瘘管切除术"
        # 组件Code配置（对应待提取字段）
        self.component_code_map = {}

        # 2. 文本提取规则初始化（来自子任务2）
        self.core_keywords = ["肛门手术", "肛门瘘管", "痔切除", "肛门成形", "肛周手术", "肛门治疗", "肛门操作", "肛门术式"]  # 相关性判断关键词
        self.negative_keywords = ["无", "不", "否认", "未", "未曾", "拒绝", "戒", "从无", "从未"]  # 否定关键词
        self.negative_patterns = ["无肛门手术史", "否认肛门手术", "未行肛门手术", "未曾接受肛门手术", "拒绝手术", "从无肛门手术", "从未手术"]  # 固定否定模式

        # 提取字段与规则映射
        self.field_extraction_rules = {
            "是否接受过肛门手术": {
                "type": "关键词匹配+否定逻辑",
                "positive_keywords": ["曾行肛门手术", "接受肛门手术", "行肛门手术", "做过肛门手术", "有肛门手术史"],
                "negative_keywords": ["无肛门手术史", "否认肛门手术", "未行肛门手术", "未曾手术"]
            },
            "具体手术名称（如痔切除术、肛门成形术等）": {
                "type": "关键词匹配",
                "keywords": ["痔切除术", "肛门成形术", "肛门瘘管切除术", "肛裂切除术", "肛乳头肥大切除术",
                             "肛门括约肌修复术", "肛周脓肿切开引流术", "PPH术", "TST术"]
            },
            "手术部位（如肛门周围区域）": {
                "type": "关键词匹配",
                "keywords": ["肛门周围", "肛管", "肛门口", "肛周皮肤", "肛门括约肌", "直肠末端", "肛窦", "肛乳头"]
            },
            "手术原因（如肛门疾病类型）": {
                "type": "关键词匹配",
                "keywords": ["肛瘘", "痔疮", "肛裂", "肛周脓肿", "肛门狭窄", "肛乳头肥大", "肛窦炎", "肛门失禁", "肛门瘙痒症"]
            },
            "手术时间": {
                "type": "正则匹配",
                "patterns": [
                    r'(\d{4})年(\d{1,2})月于(.+?)行',
                    r'(\d{4})年(\d{1,2})月(\d{1,2})日于(.+?)手术',
                    r'于(\d{4})年(\d{1,2})月行肛门手术',
                    r'手术时间[为是](\d{4})年(\d{1,2})月',
                    r'(\d{4}-\d{1,2}-\d{1,2})于.+?行肛门手术'
                ]
            }
        }

    def _extract_clinical_info(self, text: str) -> Dict[str, Any]:
        """从病例文本中提取肛门手术相关信息"""
        result = {
            "has_surgery": None,      # 是否接受过肛门手术：True/False/None
            "surgery_name": None,     # 具体手术名称
            "surgery_site": None,     # 手术部位
            "surgery_reason": None,   # 手术原因（疾病类型）
            "surgery_time": None      # 手术时间（格式化字符串）
        }

        # 1. 相关性判断：无核心关键词则返回空结果
        if not any(keyword in text for keyword in self.core_keywords):
            return result

        # 2. 否定判断：含否定模式或上下文否定则标记为未接受手术
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
            result["has_surgery"] = False
            return result

        # 3. 正向提取各字段
        result["has_surgery"] = True

        # 提取具体手术名称
        surgery_names = self.field_extraction_rules["具体手术名称（如痔切除术、肛门成形术等）"]["keywords"]
        for name in surgery_names:
            if name in text:
                result["surgery_name"] = name
                break

        # 提取手术部位
        surgery_sites = self.field_extraction_rules["手术部位（如肛门周围区域）"]["keywords"]
        for site in surgery_sites:
            if site in text:
                result["surgery_site"] = site
                break

        # 提取手术原因（疾病类型）
        surgery_reasons = self.field_extraction_rules["手术原因（如肛门疾病类型）"]["keywords"]
        for reason in surgery_reasons:
            if reason in text:
                result["surgery_reason"] = reason
                break

        # 提取手术时间（使用正则匹配）
        time_patterns = self.field_extraction_rules["手术时间"]["patterns"]
        for pattern_str in time_patterns:
            pattern = re.compile(pattern_str)
            match = pattern.search(text)
            if match:
                # 根据不同pattern返回对应的时间格式
                if "%Y-%m-%d" in pattern_str:
                    result["surgery_time"] = match.group(1)
                elif len(match.groups()) >= 2:
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    result["surgery_time"] = f"{year}-{month}"
                break

        return result

    def _create_observation(self, patient_id: str, text: str, timestamp: str, clinical_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建符合肛门手术Profile的Observation资源"""
        observation_id = str(uuid.uuid1())
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "meta": {
                "profile": [self.fhir_observation_profile]
            },
            "text": {
                "status": "generated",
                "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">病例文本摘录：{text}</div>"
            },
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": self.main_code_system,
                        "code": self.main_code,
                        "display": self.main_code_display
                    }
                ],
                "text": self.main_code_display
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": timestamp,
            "component": []
        }

        # 添加“是否接受过肛门手术”组件（CodeableConcept）
        has_surgery_comp = {
            "code": {
                "coding": [
                    {
                        "system": self.main_code_system.replace("cs", "component-cs"),
                        "code": "has-anus-surgery",
                        "display": "是否接受过肛门手术"
                    }
                ],
                "text": "是否接受过肛门手术"
            }
        }
        if clinical_info["has_surgery"] is False:
            has_surgery_comp["valueCodeableConcept"] = {
                "coding": [
                    {
                        "system": self.main_code_system.replace("cs", "yes-no-cs"),
                        "code": "no",
                        "display": "否"
                    }
                ],
                "text": "否"
            }
        elif clinical_info["has_surgery"] is True:
            has_surgery_comp["valueCodeableConcept"] = {
                "coding": [
                    {
                        "system": self.main_code_system.replace("cs", "yes-no-cs"),
                        "code": "yes",
                        "display": "是"
                    }
                ],
                "text": "是"
            }
        observation["component"].append(has_surgery_comp)

        # 若接受过手术，则添加其他组件
        if clinical_info["has_surgery"] is True:
            # 添加“具体手术名称”组件（CodeableConcept）
            if clinical_info["surgery_name"]:
                surgery_name_comp = {
                    "code": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "component-cs"),
                                "code": "surgery-name",
                                "display": "具体手术名称"
                            }
                        ],
                        "text": "具体手术名称"
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "surgery-name-cs"),
                                "code": clinical_info["surgery_name"],
                                "display": clinical_info["surgery_name"]
                            }
                        ],
                        "text": clinical_info["surgery_name"]
                    }
                }
                observation["component"].append(surgery_name_comp)

            # 添加“手术部位”组件（CodeableConcept）
            if clinical_info["surgery_site"]:
                surgery_site_comp = {
                    "code": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "component-cs"),
                                "code": "surgery-site",
                                "display": "手术部位"
                            }
                        ],
                        "text": "手术部位"
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "surgery-site-cs"),
                                "code": clinical_info["surgery_site"],
                                "display": clinical_info["surgery_site"]
                            }
                        ],
                        "text": clinical_info["surgery_site"]
                    }
                }
                observation["component"].append(surgery_site_comp)

            # 添加“手术原因”组件（CodeableConcept）
            if clinical_info["surgery_reason"]:
                surgery_reason_comp = {
                    "code": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "component-cs"),
                                "code": "surgery-reason",
                                "display": "手术原因"
                            }
                        ],
                        "text": "手术原因"
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "disease-type-cs"),
                                "code": clinical_info["surgery_reason"],
                                "display": clinical_info["surgery_reason"]
                            }
                        ],
                        "text": clinical_info["surgery_reason"]
                    }
                }
                observation["component"].append(surgery_reason_comp)

            # 添加“手术时间”组件（DateTime）
            if clinical_info["surgery_time"]:
                surgery_time_comp = {
                    "code": {
                        "coding": [
                            {
                                "system": self.main_code_system.replace("cs", "component-cs"),
                                "code": "surgery-time",
                                "display": "手术时间"
                            }
                        ],
                        "text": "手术时间"
                    },
                    "valueDateTime": clinical_info["surgery_time"]
                }
                observation["component"].append(surgery_time_comp)

        return observation

    def parse_clinical_text_to_fhir_bundle(self, patient_id: str, case_reports: List[Dict[str, str]], ai_algorithm_type: str = "nlp") -> Dict[str, Any]:
        """
        主方法：从多份病例文本生成含肛门手术Observation的FHIR Bundle
        :param patient_id: 患者ID（如"pat-001"）
        :param case_reports: 病例列表，每个元素含"text"（病例文本）和"timestamp"（时间戳，如"2024-10-01T10:00:00Z"）
        :param ai_algorithm_type: 提取算法类型，默认nlp
        :return: FHIR Bundle（transaction类型）
        """
        # 1. 初始化FHIR Bundle基础结构
        fhir_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",  # 批量提交类型
            "total": 0,  # 有效资源总数，后续动态更新
            "entry": []  # 资源列表
        }

        # 2. 遍历每一份病例，提取信息并生成Observation
        for report in case_reports:
            case_text = report.get("text", "").strip()
            case_timestamp = report.get("timestamp", datetime.now().isoformat() + "Z")  # 默认当前时间

            # 3. 调用辅助方法提取临床信息（肛门手术）
            clinical_info = self._extract_clinical_info(case_text)

            # 4. 跳过无相关信息的病例（has_surgery为None时无有效数据）
            if clinical_info.get("has_surgery") is None:
                continue

            # 5. 调用辅助方法生成Observation资源
            observation_resource = self._create_observation(
                patient_id=patient_id,
                text=case_text,
                timestamp=case_timestamp,
                clinical_info=clinical_info
            )

            # 6. 将Observation加入Bundle的entry，配置POST请求
            fhir_bundle["entry"].append({
                "resource": observation_resource,
                "request": {
                    "method": "POST",  # FHIR批量提交常用方法
                    "url": "Observation"  # 资源类型，与Observation对应
                }
            })

        # 7. 更新Bundle的有效资源总数
        fhir_bundle["total"] = len(fhir_bundle["entry"])

        return fhir_bundle

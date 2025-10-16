import re
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class FHIRResourceBundleGenerator:
    def __init__(self, fhir_api_base: str):
        self.fhir_api_base = fhir_api_base
        # 定义饮酒相关关键词
        self.alcohol_keywords = ["饮酒", "喝酒", "酒精", "酒", "酗酒", "嗜酒", "乙醇", "白酒", "啤酒", "葡萄酒", "红酒",
                                 "黄酒", "洋酒"]
        self.negative_keywords = ["无", "不", "否认", "未", "拒绝", "戒", "禁", "从不", "不嗜", "无特殊"]

        # 定义不同酒类的酒精含量百分比（体积百分比）
        self.alcohol_content = {
            "白酒": 0.40,  # 40% 酒精含量
            "啤酒": 0.05,  # 5% 酒精含量
            "葡萄酒": 0.12,  # 12% 酒精含量
            "红酒": 0.12,  # 12% 酒精含量
            "黄酒": 0.15,  # 15% 酒精含量
            "洋酒": 0.40,  # 40% 酒精含量 (默认值)
            "default": 0.40  # 默认酒精含量
        }

    def _is_negative_in_context(self, text: str, neg_word: str, alcohol_words: list, window_size: int = 5) -> bool:
        """
        检查否定词是否在饮酒相关词汇的上下文中
        """
        # 找到所有否定词的位置
        neg_positions = [m.start() for m in re.finditer(neg_word, text)]

        # 找到所有饮酒相关词汇的位置
        alcohol_positions = []
        for alcohol_word in alcohol_words:
            alcohol_positions.extend([m.start() for m in re.finditer(alcohol_word, text)])

        # 检查每个否定词是否在饮酒相关词汇的窗口范围内
        for neg_pos in neg_positions:
            for alcohol_pos in alcohol_positions:
                if abs(neg_pos - alcohol_pos) <= window_size:
                    return True

        return False

    def _convert_alcohol_units(self, value: float, unit: str, alcohol_type: str = None) -> float:
        """
        将不同单位的酒精摄入量转换为标准单位(克/天)
        考虑不同酒类的酒精含量
        """
        # 确定酒精含量百分比
        alcohol_percentage = self.alcohol_content.get(alcohol_type,
                                                      self.alcohol_content["default"]) if alcohol_type else 1.0

        # 单位转换映射 (转换为毫升)
        unit_to_ml = {
            "ml": 1.0,  # 1ml = 1ml
            "毫升": 1.0,  # 1毫升 = 1ml
            "两": 50.0,  # 1两 = 50ml
            "杯": 150.0,  # 1杯 ≈ 150ml (标准酒杯)
            "瓶": 500.0,  # 1瓶啤酒 ≈ 500ml
            "听": 330.0,  # 1听啤酒 ≈ 330ml
            "罐": 330.0,  # 同听
            "g": 1.25,  # 1g = 1.25ml (酒精密度约为0.8g/ml)
            "克": 1.25,  # 1克 = 1.25ml
        }

        # 如果没有指定单位或单位未知，默认为克
        if not unit or unit not in unit_to_ml:
            # 假设已经是克，直接返回
            return value

        # 转换为毫升
        ml_value = value * unit_to_ml[unit]

        # 计算纯酒精量 (毫升) = 总毫升 × 酒精含量百分比
        pure_alcohol_ml = ml_value * alcohol_percentage

        # 转换为克 (酒精密度约为0.8g/ml)
        pure_alcohol_g = pure_alcohol_ml * 0.8

        return pure_alcohol_g

    def _extract_alcohol_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取饮酒相关信息，包括酒类和单位
        """
        result = {
            "has_history": None,  # True/False/None
            "duration": None,  # 年数
            "daily_intake": None,  # 克/天
            "alcohol_type": None  # 酒类
        }

        text_lower = text.lower()

        # 检查是否有饮酒相关词汇
        has_alcohol_ref = any(alcohol in text for alcohol in self.alcohol_keywords)

        if not has_alcohol_ref:
            return result

        # 提取酒类信息
        alcohol_types = ["白酒", "啤酒", "葡萄酒", "红酒", "黄酒", "洋酒"]
        for a_type in alcohol_types:
            if a_type in text:
                result["alcohol_type"] = a_type
                break

        # 检查是否有明确的饮酒否定表述
        explicit_negative_patterns = [
            r'无饮酒史',
            r'不饮酒',
            r'不喝酒',
            r'戒酒',
            r'禁酒',
            r'拒绝饮酒',
            r'否认饮酒',
            r'无酒精摄入',
            r'无酒嗜好',
            r'不嗜酒',
            r'烟酒不嗜',
            r'无烟酒嗜好',
            r'烟酒均不嗜',
            r'从不饮酒',
            r'从未饮酒'
        ]

        has_explicit_negative = any(re.search(pattern, text) for pattern in explicit_negative_patterns)

        # 检查上下文相关的否定词
        has_context_negative = False
        for neg_word in self.negative_keywords:
            if self._is_negative_in_context(text, neg_word, self.alcohol_keywords):
                has_context_negative = True
                break

        if has_explicit_negative or has_context_negative:
            result["has_history"] = False
        else:
            result["has_history"] = True

            # 尝试提取饮酒持续时间（年）
            duration_patterns = [
                r'饮酒[已约有]?(\d+)年',
                r'喝酒[已约有]?(\d+)年',
                r'饮酒史[已约有]?(\d+)年',
                r'持续饮酒[已约有]?(\d+)年',
                r'饮酒≧(\d+)年',
                r'饮酒≥(\d+)年',
                r'饮酒(\d+)\s*年',
                r'饮酒[已约有]?(\d+)\s*余年',
                r'喝酒[已约有]?(\d+)\s*余年'
            ]

            for pattern in duration_patterns:
                match = re.search(pattern, text)
                if match:
                    result["duration"] = int(match.group(1))
                    break

            # 尝试提取每日酒精摄入量（支持多种单位和酒类）
            intake_patterns = [
                # 标准格式: [酒类] [数量][单位]/天
                r'(\w+)\s*(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)/天',
                r'(\w+)\s*(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)\s*每天',

                # 格式: 饮酒 [数量][单位]/天
                r'饮酒\s*(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)/天',
                r'白酒\s*(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)/d',
                r'饮酒\s*(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)\s*每天',

                # 格式: [数量][单位] [酒类]/天
                r'(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)\s*(\w+)/天',
                r'(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)\s*(\w+)\s*每天',

                # 简单格式: [数量][单位]
                r'饮酒量[约為为]?(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)',
                r'日饮酒量[约為为]?(\d+)(?:\.\d+)?\s*(ml|毫升|两|杯|瓶|听|罐|g|克)',

                # 克格式 (直接记录纯酒精量)
                r'酒精摄入[量]?[<>≦≧≤≥]?(\d+)(?:\.\d+)?\s*(?:g|克)/天',
                r'饮酒量[<>≦≧≤≥]?(\d+)(?:\.\d+)?\s*(?:g|克)/天',
                r'日饮酒量[约為为]?(\d+)(?:\.\d+)?\s*(?:g|克)',
            ]

            for pattern in intake_patterns:
                match = re.search(pattern, text)
                if match:
                    # 确定单位和值
                    if len(match.groups()) >= 2:
                        # 处理不同格式的匹配组
                        if match.lastindex >= 3:  # 格式: [酒类] [数量][单位] 或 [数量][单位] [酒类]
                            # 检查第一个组是否是酒类
                            if match.group(1) in self.alcohol_content:
                                alcohol_type = match.group(1)
                                value = float(match.group(2))
                                unit = match.group(3)
                            else:
                                # 可能是 [数量][单位] [酒类] 格式
                                value = float(match.group(1))
                                unit = match.group(2)
                                alcohol_type = match.group(3) if match.group(3) in self.alcohol_content else result[
                                    "alcohol_type"]
                        else:  # 格式: [数量][单位] 或 [酒类] [数量][单位]
                            # 检查第一个组是否是酒类
                            if match.group(1) in self.alcohol_content:
                                alcohol_type = match.group(1)
                                value = float(match.group(2))
                                unit = match.group(3) if len(match.groups()) >= 3 else None
                            else:
                                value = float(match.group(1))
                                unit = match.group(2)
                                alcohol_type = result["alcohol_type"]

                        # 转换为标准单位(克/天)
                        result["daily_intake"] = self._convert_alcohol_units(value, unit, alcohol_type)
                        break
                    else:
                        # 处理克格式
                        value = float(match.group(1))
                        result["daily_intake"] = value
                        break

        return result

    def _create_observation(self, patient_id: str, text: str, timestamp: str,
                            alcohol_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建符合Profile的Observation资源
        """
        observation_id = str(uuid.uuid1())

        # 构建基础Observation
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "meta": {
                "profile": [
                    "http://localhost:3456/api/terminology/Profile/cnwqk435-alcohol-consumption"
                ]
            },
            "text": {
                "status": "generated",
                "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">文本摘录：{text}</div>"
            },
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-observation-cs",
                        "code": "alcohol-consumption",
                        "display": "酒精消费"
                    }
                ],
                "text": "酒精消费"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": timestamp,
            "component": []
        }

        # 添加饮酒史状态组件
        history_status = {
            "code": {
                "coding": [
                    {
                        "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-component-cs",
                        "code": "drinking-history-status",
                        "display": "饮酒史状态"
                    }
                ],
                "text": "饮酒史状态"
            }
        }

        if alcohol_info["has_history"] is False:
            history_status["valueCodeableConcept"] = {
                "coding": [
                    {
                        "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-alcohol-history-cs",
                        "code": "no-history",
                        "display": "无饮酒史"
                    }
                ],
                "text": "无饮酒史"
            }
        elif alcohol_info["has_history"] is True:
            history_status["valueCodeableConcept"] = {
                "coding": [
                    {
                        "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-alcohol-history-cs",
                        "code": "yes-history",
                        "display": "有饮酒史"
                    }
                ],
                "text": "有饮酒史"
            }

        if alcohol_info["has_history"] is not None:
            observation["component"].append(history_status)

        # 如果有饮酒史，添加持续时间和摄入量组件
        if alcohol_info["has_history"] is True:
            # 饮酒持续时间组件
            if alcohol_info["duration"] is not None:
                duration_component = {
                    "code": {
                        "coding": [
                            {
                                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-component-cs",
                                "code": "duration-of-drinking",
                                "display": "饮酒持续时间"
                            }
                        ],
                        "text": "饮酒持续时间"
                    },
                    "valueQuantity": {
                        "value": alcohol_info["duration"],
                        "unit": "年",
                        "system": "http://unitsofmeasure.org",
                        "code": "a"
                    }
                }
                observation["component"].append(duration_component)

            # 平均纯酒精摄入组件
            if alcohol_info["daily_intake"] is not None:
                intake_component = {
                    "code": {
                        "coding": [
                            {
                                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk435-component-cs",
                                "code": "average-alcohol-intake",
                                "display": "平均纯酒精摄入"
                            }
                        ],
                        "text": "平均纯酒精摄入"
                    },
                    "valueQuantity": {
                        "value": alcohol_info["daily_intake"],
                        "unit": "克/天",
                        "system": "http://unitsofmeasure.org",
                        "code": "g/d"
                    }
                }
                observation["component"].append(intake_component)

        return observation

    def parse_clinical_text_to_fhir_bundle(self, patient_id, case_reports, ai_algorithm_type="nlp"):
        """
        从临床文本中解析饮酒史信息并构建FHIR Bundle
        """
        entries = []

        for report in case_reports:
            text = report.get("text", "")
            timestamp = report.get("timestamp", datetime.now().isoformat())

            # 检查文本是否包含饮酒相关信息
            alcohol_info = self._extract_alcohol_info(text)

            # 只有当提取到相关信息时才创建Observation
            if alcohol_info["has_history"] is not None:
                observation = self._create_observation(patient_id, text, timestamp, alcohol_info)

                entries.append({
                    "resource": observation,
                    "request": {
                        "method": "POST",
                        "url": "Observation"
                    }
                })

        # 构建Bundle
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "total": len(entries),
            "entry": entries
        }

        return bundle
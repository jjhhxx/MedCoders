import uuid
import re
from typing import List, Dict, Any
from datetime import datetime

class FHIRResourceBundleGenerator:
    def __init__(self, fhir_api_base: str):
        self.fhir_api_base = fhir_api_base
        
        # 初始化映射字典
        self.mappings = {}
        
        # 构建POP-Q分度映射
        self.mappings["POPQGrade"] = {
            "0度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "0",
                "display": "0度"
            },
            "无脱垂": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "0",
                "display": "0度"
            },
            "I度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "I",
                "display": "I度"
            },
            "II度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "II",
                "display": "II度"
            },
            "III度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "III",
                "display": "III度"
            },
            "IV度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "IV",
                "display": "IV度"
            },
            "完全脱垂": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-popq-grade-cs",
                "code": "IV",
                "display": "IV度"
            }
        }
        
        # 构建评估代码映射
        self.mappings["POPQAssessment"] = {
            "POP-Q分度": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-observation-cs",
                "code": "popq-grade",
                "display": "POP-Q分度"
            },
            "盆腔器官脱垂分度评估": {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-observation-cs",
                "code": "popq-grade",
                "display": "POP-Q分度"
            }
        }
        
        # 注册资源构建函数
        self.profile_builders = {
            "Observation": self._create_observation_resource
        }

    def _extract_entities(self, text: str) -> dict:
        """从中文临床文本中提取POP-Q相关信息"""
        results = {
            "popq_grades": [],
            "assessments": []
        }
        
        # 提取POP-Q分度信息
        for term, mapping in self.mappings["POPQGrade"].items():
            if term in text:
                results["popq_grades"].append({
                    "code": mapping["code"],
                    "display": mapping["display"],
                    "system": mapping["system"],
                    "text": term
                })
        
        # 提取评估代码信息
        for term, mapping in self.mappings["POPQAssessment"].items():
            if term in text:
                results["assessments"].append({
                    "code": mapping["code"],
                    "display": mapping["display"],
                    "system": mapping["system"],
                    "text": term
                })
        
        return results

    def _create_observation_resource(self, patient_id: str, report: dict, 
                                   popq_grade: dict, assessment: dict) -> dict:
        """创建POP-Q评估Observation资源"""
        return {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "meta": {
                "profile": [
                    "http://localhost:3456/api/terminology/Profile/cnwqk485-popq-assessment"
                ]
            },
            "status": "final",
            "code": {
                "coding": [{
                    "system": assessment["system"],
                    "code": assessment["code"],
                    "display": assessment["display"]
                }],
                "text": assessment["text"]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": report.get("timestamp", datetime.now().isoformat()),
            "valueCodeableConcept": {
                "coding": [{
                    "system": popq_grade["system"],
                    "code": popq_grade["code"],
                    "display": popq_grade["display"]
                }],
                "text": popq_grade["text"]
            }
        }

    def parse_clinical_text_to_fhir_bundle(self, patient_id: str, case_reports: list[str], ai_algorithm_type="nlp") -> dict:
        """从临床文本中提取信息并生成FHIR Bundle"""
        resources = []
        
        for report in case_reports:
            # 提取实体信息
            extracted = self._extract_entities(report["text"])
            
            # 如果同时提取到分度和评估信息，则创建资源
            if extracted["popq_grades"] and extracted["assessments"]:
                for grade in extracted["popq_grades"]:
                    for assessment in extracted["assessments"]:
                        observation = self._create_observation_resource(
                            patient_id, report, grade, assessment
                        )
                        resources.append(observation)
            # 如果只提取到分度信息，创建默认评估代码
            elif extracted["popq_grades"]:
                default_assessment = {
                    "code": "popq-grade",
                    "display": "POP-Q分度",
                    "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk485-observation-cs",
                    "text": "POP-Q分度"
                }
                for grade in extracted["popq_grades"]:
                    observation = self._create_observation_resource(
                        patient_id, report, grade, default_assessment
                    )
                    resources.append(observation)
        
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
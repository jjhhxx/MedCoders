import uuid
import re
from typing import List, Dict, Any

class FHIRResourceBundleGenerator:
    def __init__(self, fhir_api_base: str):
        self.fhir_api_base = fhir_api_base
        
        # 初始化映射字典
        self.mappings = {}
        self._build_mappings()
        
        # 初始化profile builders映射
        self.profile_builders = {
            "Observation": self._create_observation_resource,
        }

    def _build_mappings(self):
        """根据codeSystems和valueSets构建映射"""
        # 构建性别映射
        gender_mapping = {}
        # 注意：这里的codes来自codeSystems.gender-codesystem
        codes = [
            {"code": "female", "display": "女性"},
            {"code": "male", "display": "男性"},
            {"code": "other", "display": "其他"},
            {"code": "unknown", "display": "未知"}
        ]
        
        for item in codes:
            code = item['code']
            display = item['display']
            # 使用code和display作为关键词
            gender_mapping[code] = {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk895-GenderCodeSystem",
                "code": code,
                "display": display
            }
            gender_mapping[display] = {
                "system": "http://localhost:3456/api/terminology/CodeSystem/cnwqk895-GenderCodeSystem",
                "code": code,
                "display": display
            }
            
        self.mappings["Gender"] = gender_mapping

    def _extract_entities(self, text: str) -> dict:
        """从中文临床文本中提取性别信息"""
        results = {
            "genders": []
        }
        
        # 查找性别关键词
        for key, mapping in self.mappings["Gender"].items():
            if key in text and mapping not in [g["mapping"] for g in results["genders"]]:
                results["genders"].append({
                    "text": key,
                    "mapping": mapping
                })
                
        return results

    def _create_observation_resource(self, patient_id: str, report: dict, gender_info: dict) -> dict:
        """创建性别Observation资源"""
        return {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "meta": {
                "profile": [
                    "http://localhost:3456/api/terminology/Profile/cnwqk895-GenderObservationProfile"
                ]
            },
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "46098-0",
                    "display": "Sex"
                }],
                "text": "Sex"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": report.get("timestamp", ""),
            "valueCodeableConcept": {
                "coding": [{
                    "system": gender_info["mapping"]["system"],
                    "code": gender_info["mapping"]["code"],
                    "display": gender_info["mapping"]["display"]
                }],
                "text": gender_info["text"]
            }
        }

    def parse_clinical_text_to_fhir_bundle(self, patient_id: str, case_reports: List[str], ai_algorithm_type="nlp") -> dict:
        """主函数：解析临床文本并生成FHIR Bundle"""
        resources = []
        
        for report in case_reports:
            # 确保report是字典格式
            if isinstance(report, str):
                report_dict = {"text": report}
            else:
                report_dict = report
                
            # 提取实体信息
            extracted = self._extract_entities(report_dict.get("text", ""))
            
            # 创建性别Observation资源
            for gender in extracted["genders"]:
                observation = self._create_observation_resource(patient_id, report_dict, gender)
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
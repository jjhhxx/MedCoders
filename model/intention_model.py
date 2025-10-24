import re
from functools import partial
from typing import List

from utils import (
    prompt_attr
)


class IntentionClientManager:
    def __init__(self):
        self.prompt_conf = prompt_attr

    @property
    def intentions_prompt_mapping_k2p(self):
        # See utils.prompt_conf for details.
        mapping = {
            "coding": {
                "step_1_extract_FHIR": self.prompt_conf.step_1_extract_FHIR,
                "step_2_online_search": self.prompt_conf.step_2_online_search,
                "step_3_generate": self.prompt_conf.step_3_generate,
            }
        }
        return mapping

    @property
    def intentions_prompt_params_mapping_k2p(self):
        # See utils.prompt_conf for details.
        mapping = {
            "coding": {
                "step_1_extract_FHIR": self.prompt_conf.step_1_params,
                "step_2_online_search": self.prompt_conf.step_2_params,
                "step_3_generate": self.prompt_conf.step_3_params,
            }
        }
        return mapping

    @property
    def intentions_mapping_check_function(self):
        mapping = {
            "coding": {
                "step_1_extract_FHIR": partial(
                    self._check_before, check_keys=["valueSets", "codeSystems", "profiles"],
                    check_key_func=self._check_key_for_dict
                ),
                "step_2_online_search": partial(
                    self._check_before, check_keys=[], check_key_func=None
                ),
                "step_3_generate": partial(
                    self._check_before, check_keys=[], check_key_func=None
                ),
            }
        }
        return mapping

    @property
    def intentions_request_params_mapping_k2p(self):
        mapping = {
            "coding": {
                "step_1_extract_FHIR": (0.7, 32768),
                "step_2_online_search": (0.7, 32768),
                "step_3_generate": (0.7, 32768),
            }
        }
        return mapping

    @staticmethod
    def _check_key_for_dict(keys: list, meta: dict) -> bool:
        for key in keys:
            if key not in meta:
                return False
        return True

    def _check_key_for_list(self, keys: list, meta: list) -> bool:
        for _meta_dict in meta:
            if not self._check_key_for_dict(keys, _meta_dict):
                return False
        return True

    @staticmethod
    def _check_before(content, check_keys, check_key_func):
        try:
            reason_index = content.find("</think>")
            if reason_index == -1:
                reason_index = 0
            reason = content[:reason_index] if reason_index else ""
            answer = content[reason_index + 8:] if reason_index else content
            if check_keys and check_key_func:
                json_match = re.search(r'```json\n(.*?)\n```', answer, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = answer
                result = eval(json_str)["result"]
                status = check_key_func(check_keys, result)
            else:
                status = True
                result = answer
        except Exception as e:
            print(f"Check keys {check_keys} error: {e}")
            reason, result = "", ""
            status = False
        return status, reason, result

    def get_intention_prompt_by_intention(self, intention_recognition: str) -> str:
        title, specific = intention_recognition.split("-")
        intention_prompt = self.intentions_prompt_mapping_k2p.get(title).get(specific)
        return intention_prompt

    def get_intention_prompt_params_by_intention(self, intention_recognition: str) -> str:
        title, specific = intention_recognition.split("-")
        intention_prompt = self.intentions_prompt_params_mapping_k2p.get(title).get(specific)
        return intention_prompt

    def get_check_function_by_intention(self, intention_recognition: str) -> callable:
        title, specific = intention_recognition.split("-")
        check_function = self.intentions_mapping_check_function.get(title).get(specific)
        return check_function

    def get_request_params_by_intention(self, intention_recognition: str) -> tuple[str, str]:
        title, specific = intention_recognition.split("-")
        request_params = self.intentions_request_params_mapping_k2p.get(title).get(specific)
        return request_params

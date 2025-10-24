
from utils.prompt import prompt_conf
from utils.llm_conf import dashscope_llm_conf, dashscope_llm_conf_coder
from utils.util import AttrDict, extract_excel_data


prompt_attr = AttrDict(prompt_conf)
dashscope_attr = AttrDict(dashscope_llm_conf)
dashscope_attr_coder = AttrDict(dashscope_llm_conf_coder)

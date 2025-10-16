
from utils.prompt import prompt_conf
from utils.llm_conf import dashscope_llm_conf
from utils.util import AttrDict, extract_excel_data


prompt_attr = AttrDict(prompt_conf)
dashscope_attr = AttrDict(dashscope_llm_conf)

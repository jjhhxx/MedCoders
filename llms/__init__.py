from llms.openai import OpenAIClient
from utils import dashscope_attr, dashscope_attr_coder


llm_client = OpenAIClient(dashscope_attr)
llm_client_coder = OpenAIClient(dashscope_attr_coder)

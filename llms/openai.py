"""
Supports OpenAI-type communication interfaces.
"""
import json
import requests
from openai import OpenAI


class OpenAIClient(object):

    def __init__(self, attrs):
        self.attrs = attrs
        self.retry = 5
        self.timeout = 3600
        self.client = OpenAI(
            api_key=self.attrs.api_key,
            base_url=self.attrs.url,
        )

    def _check_pre(self, query: list, temperature: float = 0.7, max_tokens: int = 16384):
        messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                }
            ]
        messages.extend(query)
        json_data = {
            "model": self.attrs.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        return json_data

    def chat(self, query, temperature: float = 0.7, max_tokens: int = 16384):
        json_data = self._check_pre(query, temperature=temperature, max_tokens=max_tokens)
        json_data["stream"] = False
        completion = self.client.chat.completions.create(**json_data)
        return completion.choices[0].message.content

    def chat_and_check(self, query, check_func, temperature: float = 0.7, max_tokens: int = 16384):
        check_status = False
        reason, result = "", {}
        retry = self.retry
        while not check_status and retry > 0:
            response = self.chat(query, temperature=temperature, max_tokens=max_tokens)
            check_status, reason, result = check_func(response)
            retry -= 1
        if not check_status:
            raise ValueError("Can`t successfully retrieve the correct response!")
        return reason, result


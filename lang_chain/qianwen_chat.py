import json
from http import HTTPStatus
import dashscope


def qianwen_sync_call_streaming(query: str):
    response_generator = dashscope.Generation.call(
        api_key='sk-80a1b6d650f448128d39ba7f7fa66bc9',
        model='qwen-turbo',
        prompt=query,
        stream=True,
        top_p=0.8)

    head_idx = 0
    for resp in response_generator:
        paragraph = resp.output['text']
        result_text = paragraph[head_idx:len(paragraph)]
        print("\r%s" % result_text, end='')
        if(paragraph.rfind('\n') != -1):
            head_idx = paragraph.rfind('\n') + 1
        yield result_text
import os
import uuid

import requests

# 获取当前文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 生成本地语音文件存储路径
AUDIO_DIRECTORY = os.path.join(current_dir, "..", "..", "data", "audio")
os.makedirs(AUDIO_DIRECTORY, exist_ok=True)


def test_2_audio(text: str, file_name: str):
    file_name = get_request("http://localhost:8080//?spk=%E4%B8%89%E6%9C%88%E4%B8%83&text_split_method=cut0&speed=1.0&emotion=&lang=zh&text={}".format(text), "", file_name)
    return file_name


def get_request(url, data, file_name):
    # 假设data是一个字典，我们将其转为json格式进行发送
    response = requests.get(url, params=data)
    if response.status_code == 200:
        # 假设你要将音频文件保存在当前目录，文件名为output.wav
        # 拼接文件名和目录路径
        file_part = f"{file_name}.wav"
        file_path = os.path.join(AUDIO_DIRECTORY, file_part)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    else:
        print(f'音频合成失败')

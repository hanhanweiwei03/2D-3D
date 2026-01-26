# backend/blueprints/chatbox.py
from flask import Blueprint, request, jsonify
import requests

# 创建chatbox蓝图
chatbox_bp = Blueprint('chatbox', __name__)

# DeepSeek 配置（替换为你的 API Key）
DEEPSEEK_API_KEY = "sk-93bce4d30eae4f0d99de4b6b93e59e88"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


@chatbox_bp.route('/chatbox', methods=['POST'])
def chat_with_deepseek():
    try:
        # 1. 获取前端传入的消息
        data = request.get_json()
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({'reply': 'Please enter a message!'}), 400

        # 2. 构造DeepSeek请求参数
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",  # DeepSeek模型名
            "messages": [{"role": "user", "content": user_message}],
            "temperature": 0.7,
            "stream": False  # 非流式返回
        }

        # 3. 调用DeepSeek API
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=30  # 设置超时
        )
        response.raise_for_status()  # 抛出HTTP错误

        # 4. 解析响应并返回给前端
        deepseek_reply = response.json()['choices'][0]['message']['content']
        return jsonify({'reply': deepseek_reply})

    except requests.exceptions.RequestException as e:
        # DeepSeek请求异常
        error_msg = f"DeepSeek request failed: {str(e)}"
        print(error_msg)
        return jsonify({'reply': error_msg}), 500
    except Exception as e:
        # 其他异常
        error_msg = f"Server error: {str(e)}"
        print(error_msg)
        return jsonify({'reply': error_msg}), 500
<template>
  <div class="chat-box-container">
    <!-- 聊天记录 -->
    <div class="chat-messages">
      <div
        class="message"
        :class="{ 'user-message': msg.role === 'user', 'ai-message': msg.role === 'assistant' }"
        v-for="(msg, index) in messages"
        :key="index"
      >
        <span class="role">{{ msg.role === 'user' ? 'Me' : 'DeepSeek' }}：</span>
        <span class="content">{{ msg.content }}</span>
      </div>
    </div>

    <!-- 输入框 + 发送按钮 -->
    <div class="chat-input">
      <textarea
        v-model="inputContent"
        placeholder="Input your interesting topic..."
        @keyup.enter="handleSend"
        class="input-area"
      ></textarea>
      <button class="btn send-btn" @click="handleSend" :disabled="!inputContent.trim()">
        Send
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios'; // 需先安装：npm install axios

// 1. 响应式数据
const messages = ref([
  { role: 'assistant', content: 'Hello！I\'m DeepSeek，how can I help you？' }
]); // 聊天记录
const inputContent = ref(''); // 输入内容
const isLoading = ref(false); // 加载状态

// 2. 发送消息到后端
const handleSend = async () => {
  const content = inputContent.value.trim();
  if (!content) return;

  // 2.1 添加用户消息到聊天记录
  messages.value.push({ role: 'user', content });
  inputContent.value = '';
  isLoading.value = true;

  try {
    // 2.2 调用后端接口（后端需提供 /api/chat 接口转发 DeepSeek）
    const res = await axios.post('http://localhost:5001/chatbox', {
      message: content
    });

    // 2.3 添加 AI 回复到聊天记录
    messages.value.push({
      role: 'assistant',
      content: res.data.reply || '抱歉，我没理解你的意思～'
    });
  } catch (err) {
    console.error('请求 DeepSeek 失败：', err);
    messages.value.push({
      role: 'assistant',
      content: '出错了！请稍后再试～'
    });
  } finally {
    isLoading.value = false;
    // 滚动到最新消息
    setTimeout(() => {
      const messagesEl = document.querySelector('.chat-messages');
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }, 0);
  }
};
</script>

<style scoped>
/* 适配暗黑星空背景的样式 */
.chat-box-container {
  width: 400px;
  height: 600px;
  border: 1px solid #444;
  border-radius: 8px;
  background: rgba(0, 0, 20, 0.8); /* 半透明暗黑背景，适配星空 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 20px;
}

.chat-messages {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
}

.message {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  max-width: 80%;
}

.user-message {
  background: #007bff;
  color: #fff;
  margin-left: auto;
}

.ai-message {
  background: #333;
  color: #fff;
  margin-right: auto;
}

.role {
  font-weight: bold;
  margin-right: 8px;
}

.chat-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #444;
  gap: 10px;
}

.input-area {
  flex: 1;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #555;
  background: #111;
  color: #fff;
  resize: none;
  outline: none;
  font-size: 14px;
}

.send-btn {
  padding: 8px 20px;
  white-space: nowrap;
}

.send-btn:disabled {
  background: #666;
  cursor: not-allowed;
}
</style>
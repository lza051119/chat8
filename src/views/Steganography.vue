<template>
  <div class="steganography-page">
    <div class="page-header">
      <h1>图像隐写术工具</h1>
      <p class="subtitle">安全地在图像中隐藏和提取秘密信息</p>
    </div>
    
    <div class="content-wrapper">
      <SteganographyPanel />
    </div>
    
    <div class="info-section">
      <div class="info-card">
        <h3>🔒 什么是图像隐写术？</h3>
        <p>图像隐写术是一种将秘密信息隐藏在普通图像中的技术，使得信息在不知道密码的情况下无法被检测到。</p>
      </div>
      
      <div class="info-card">
        <h3>🛡️ 安全特性</h3>
        <ul>
          <li>使用密码保护的伪随机路径生成</li>
          <li>LSB（最低有效位）技术确保图像质量</li>
          <li>SHA-256哈希确保密码安全性</li>
          <li>支持各种图像格式</li>
        </ul>
      </div>
      
      <div class="info-card">
        <h3>📝 使用说明</h3>
        <ol>
          <li><strong>嵌入信息：</strong>选择图像文件，输入秘密信息和密码，点击嵌入</li>
          <li><strong>提取信息：</strong>选择包含隐藏信息的图像，输入相同的密码，点击提取</li>
          <li><strong>注意：</strong>密码必须完全一致才能成功提取信息</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script>
import SteganographyPanel from '@/components/SteganographyPanel.vue'

export default {
  name: 'Steganography',
  components: {
    SteganographyPanel
  }
}
</script>

<style scoped>
.steganography-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.page-header {
  text-align: center;
  color: white;
  margin-bottom: 40px;
  padding-top: 40px;
}

.page-header h1 {
  font-size: 3rem;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0;
}

.content-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 50px;
}

.info-section {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
  padding: 0 20px;
}

.info-card {
  background: rgba(255, 255, 255, 0.95);
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.info-card h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1.3rem;
}

.info-card p {
  color: #555;
  line-height: 1.6;
  margin: 0;
}

.info-card ul,
.info-card ol {
  color: #555;
  line-height: 1.6;
  margin: 0;
  padding-left: 20px;
}

.info-card li {
  margin-bottom: 8px;
}

.info-card strong {
  color: #2c3e50;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .info-section {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .info-card {
    padding: 20px;
  }
}
</style>
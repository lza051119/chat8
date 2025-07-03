<template>
  <div class="contact-list">
    <div class="header">
      <h3>联系人</h3>
      <button @click="showAddModal" class="add-btn">+</button>
    </div>
    
    <div class="contacts">
      <div 
        v-for="contact in store.contacts" 
        :key="contact.id" 
        @click="selectContact(contact)"
        :class="['contact-item', { active: store.currentChat?.id === contact.id }]"
      >
        <div class="avatar">{{ contact.username[0].toUpperCase() }}</div>
        <div class="info">
          <div class="name">{{ contact.username }}</div>
          <div class="status">
            <span :class="['status-dot', { online: contact.online }]"></span>
            {{ contact.online ? '在线' : '离线' }}
          </div>
        </div>
        <div class="contact-actions">
          <button @click.stop="deleteContact(contact)" class="delete-btn" title="删除联系人">
            ×
          </button>
        </div>
      </div>
    </div>
    
    <!-- 添加联系人模态框 -->
    <AddContactModal 
      :isVisible="showModal" 
      @close="hideAddModal"
      @contact-added="onContactAdded"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store } from '../store'
import { hybridStore } from '../store/hybrid-store.js'
import { hybridApi } from '../api/hybrid-api.js'
import AddContactModal from './AddContactModal.vue'

const emit = defineEmits(['select'])
const showModal = ref(false)

function selectContact(contact) {
  store.currentChat = contact
  emit('select', contact)
}

function showAddModal() {
  showModal.value = true
}

function hideAddModal() {
  showModal.value = false
}

function onContactAdded(contact) {
  console.log('联系人添加成功:', contact)
  // 模态框会自动关闭，这里可以添加额外的处理逻辑
}

async function deleteContact(contact) {
  if (!confirm(`确定要删除联系人 "${contact.username}" 吗？`)) {
    return
  }
  
  try {
    await hybridApi.removeContact(contact.id)
    
    // 从本地存储中移除
    hybridStore.removeContact(contact.id)
    
    // 如果当前正在与该联系人聊天，清除当前聊天
    if (store.currentChat?.id === contact.id) {
      store.currentChat = null
    }
    
    console.log('联系人删除成功:', contact.username)
  } catch (error) {
    console.error('删除联系人失败:', error)
    alert('删除联系人失败，请重试')
  }
}
</script>

<style scoped>
.contact-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
}

.add-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid #007bff;
  background: white;
  color: #007bff;
  cursor: pointer;
  font-size: 1.2rem;
}

.contacts {
  flex: 1;
  overflow-y: auto;
}

.contact-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: background 0.2s;
  position: relative;
}

.contact-item:hover {
  background: #f0f0f0;
}

.contact-item:hover .contact-actions {
  opacity: 1;
}

.contact-item.active {
  background: #e3f2fd;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: 1rem;
}

.info .name {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.status {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  margin-right: 0.5rem;
}

.status-dot.online {
  background: #28a745;
}

.contact-actions {
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: auto;
}

.delete-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.delete-btn:hover {
  background: #c82333;
}
</style>
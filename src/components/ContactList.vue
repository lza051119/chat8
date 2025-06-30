<template>
  <div class="contact-list">
    <div class="header">
      <h3>联系人</h3>
      <button @click="addFriend" class="add-btn">+</button>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { store } from '../store';
import { addContact } from '../api';

const emit = defineEmits(['select']);

function selectContact(contact) {
  store.currentChat = contact;
  emit('select', contact);
}

async function addFriend() {
  const friendId = prompt('输入好友用户名：');
  if (friendId) {
    try {
      // await addContact(store.token, friendId);
      // 临时模拟添加好友
      const newContact = { 
        id: Date.now(), 
        username: friendId, 
        online: Math.random() > 0.5 
      };
      store.contacts.push(newContact);
      alert(`已添加好友：${friendId}`);
    } catch (error) {
      alert('添加好友失败（需要后端支持）');
    }
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
}

.contact-item:hover {
  background: #f0f0f0;
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
</style> 
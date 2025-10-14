import { reactive } from 'vue';

export const store = reactive({
  user: null,         // 当前登录用户
  token: '',          // 登录token
  contacts: [],       // 联系人列表
  currentChat: null,  // 当前聊天对象
  messages: {},       // { userId: [msg, ...] }
  ws: null,           // WebSocket实例
  
  // 设置用户信息
  setUser(user, token) {
    this.user = user;
    this.token = token;
  },
  
  // 添加联系人
  addContact(contact) {
    this.contacts.push(contact);
  },
  
  // 设置当前聊天对象
  setCurrentChat(contact) {
    this.currentChat = contact;
  },
  
  // 添加消息
  addMessage(contactId, message) {
    if (!this.messages[contactId]) {
      this.messages[contactId] = [];
    }
    this.messages[contactId].push(message);
  },
  
  // 清空数据（登出时使用）
  clear() {
    this.user = null;
    this.token = '';
    this.contacts = [];
    this.currentChat = null;
    this.messages = {};
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
});
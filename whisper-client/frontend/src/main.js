import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { hybridStore } from './store/hybrid-store';
import { initSingleLogin } from './utils/single-login';

const app = createApp(App);

// 全局属性，便于在模板中使用
app.config.globalProperties.$hybridStore = hybridStore;

app.use(router);

// 初始化单点登录机制
initSingleLogin();

// 直接挂载应用，数据库初始化将在用户登录后进行
console.log('🚀 正在启动 Whisper 应用...');
console.log('💡 本地数据库将在用户登录后初始化');
console.log('🔐 单点登录机制已启用，同一用户不能在多个页面同时登录');
app.mount('#app');
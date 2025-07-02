import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { hybridStore } from './store/hybrid-store';

const app = createApp(App);

// 全局属性，便于在模板中使用
app.config.globalProperties.$hybridStore = hybridStore;

app.use(router);

// 直接挂载应用，数据库初始化将在用户登录后进行
console.log('🚀 正在启动 Chat8 应用...');
console.log('💡 本地数据库将在用户登录后初始化');
app.mount('#app');
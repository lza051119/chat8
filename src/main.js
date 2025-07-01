import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { hybridStore } from './store/hybrid-store';

const app = createApp(App);

// 全局属性，便于在模板中使用
app.config.globalProperties.$hybridStore = hybridStore;

app.use(router);
app.mount('#app');
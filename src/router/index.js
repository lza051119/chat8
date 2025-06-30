import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/chat',
    name: 'HybridChatMain',
    component: () => import('../views/HybridChatMain.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  },
  // 开发模式路由 - 直接访问，无需登录
  {
    path: '/dev/chat',
    name: 'DevChat',
    component: () => import('../views/HybridChatMain.vue')
  },
  {
    path: '/dev/settings',
    name: 'DevSettings',
    component: () => import('../views/Settings.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 简化的路由守卫
router.beforeEach((to, from, next) => {
  try {
    // 开发模式路由直接放行
    if (to.path.startsWith('/dev/')) {
      next();
      return;
    }

    // 检查本地存储中的token
    const token = localStorage.getItem('token');
    const isLoggedIn = !!token;

    // 需要认证的路由
    const requiresAuth = ['HybridChatMain', 'Settings'].includes(to.name);
    
    // 需要游客状态的路由
    const requiresGuest = ['Login', 'Register'].includes(to.name);

    if (requiresAuth && !isLoggedIn) {
      next('/login');
      return;
    }

    if (requiresGuest && isLoggedIn) {
      next('/chat');
      return;
    }

    next();
  } catch (error) {
    console.error('路由守卫错误:', error);
    next('/login');
  }
});

export default router; 
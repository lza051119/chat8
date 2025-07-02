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
  {
    path: '/voice-call/:contactId?',
    name: 'VoiceCall',
    component: () => import('../views/VoiceCall.vue')
  },
  {
    path: '/steganography',
    name: 'Steganography',
    component: () => import('../views/Steganography.vue')
  },
  {
    path: '/dev/chat',
    component: () => import('../views/HybridChatMain.vue')
  },
  {
    path: '/dev/settings',
    component: () => import('../views/Settings.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
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
    component: () => import('../views/AuthPage.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/register.vue')
  },
  {
    path: '/login-transition',
    name: 'LoginTransition',
    component: () => import('../views/LoginTransition.vue')
  },
  {
    path: '/chat',
    name: 'HybridChatMain',
    component: () => import('../views/hybridchatmain.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/settings.vue')
  },
  {
    path: '/voice-call/:contactId?',
    name: 'VoiceCall',
    component: () => import('../views/VoiceCall.vue')
  },
  {
    path: '/video-call/:contactId?',
    name: 'VideoCall',
    component: () => import('../components/VideoCall.vue')
  },
  {
    path: '/steganography',
    name: 'Steganography',
    component: () => import('../views/Steganography.vue')
  },
  {
    path: '/dev/chat',
    component: () => import('../views/hybridchatmain.vue')
  },
  {
    path: '/dev/settings',
    component: () => import('../views/settings.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
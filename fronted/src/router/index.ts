import { createRouter, createWebHistory } from 'vue-router'
import home from '@/router/home'
import wordBook from '@/router/word-book'
import setting from '@/router/setting'
import test from '@/router/test'
import chat from '@/router/chat'
import course from '@/router/course'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...home, //home,
    ...wordBook, //wordBook,
    ...setting, //setting,
    ...test, //test,
    ...chat, //chat,
    ...course, //course,
  ],
})

export default router

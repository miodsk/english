import Home from '@/views/Home/index.vue'
import Layout from '@/layout/index.vue'

export default [
  {
    path: '/',
    name: 'layout',
    component: Layout,
    redirect: { name: 'home' },
    children: [
      {
        path: 'home',
        name: 'home',
        component: Home,
      },
    ],
  },
]

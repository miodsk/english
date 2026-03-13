
import Layout from '@/layout/index.vue'

export default [
  {
    path: '/word-book',
    name: 'wordbook',
    component: Layout,
    redirect: { name: 'wordbook-index' },
    children: [
      {
        path:"index",
        name:"wordbook-index",
        component:()=>import('@/views/WordBook/index.vue')
      }
    ],
  },
]

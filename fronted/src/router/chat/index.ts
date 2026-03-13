import Layout from '@/layout/index.vue'

export default [
  {
    path: '/chat',
    name: 'chat',
    component: Layout,
    redirect: { name: 'chat-composition' },
    children: [
      {
        path: 'index',
        name: 'chat-index',
        component: () => import('@/views/Chat/index.vue'),
      },
      {
        path: 'normal',
        name: 'chat-normal',
        component: () => import('@/views/Chat/normal/index.vue'),
      },
      {
        path: 'composition',
        name: 'chat-composition',
        component: () => import('@/views/Chat/composition/index.vue'),
      },
      {
        path: 'speak',
        name: 'chat-speak',
        component: () => import('@/views/Chat/speak/index.vue'),
      },
      {
        path: 'vocabulary',
        name: 'chat-vocabulary',
        component: () => import('@/views/Chat/vocabulary/index.vue'),
      },
    ],
  },
]

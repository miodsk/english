import Layout from '@/layout/index.vue'

export default [
  {
    path: '/setting',
    name: 'setting',
    component: Layout,
    redirect: { name: 'setting-index' },
    children: [
      {
        path: 'index',
        name: 'setting-index',
        component: () => import('@/views/Setting/index.vue'),
      },
    ],
  },
]

import Layout from '@/layout/index.vue'

export default [
  {
    path: '/courses',
    name: 'courses',
    component: Layout,
    redirect: { name: 'course-index' },
    children: [
      {
        path: 'index',
        name: 'course-index',
        component: () => import('@/views/Course/index.vue'),
      },
      {
        path: 'learn/:courseId/:title',
        component: () => import('@/views/Course/Learn/index.vue'),
      },
    ],
  },
]

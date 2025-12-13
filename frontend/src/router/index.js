import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  // 普通用户路由
  {
    path: '/user',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true, userType: 3 },
    children: [
      {
        path: 'dashboard',
        name: 'UserDashboard',
        component: () => import('@/views/user/Dashboard.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'records',
        name: 'UserRecords',
        component: () => import('@/views/user/Records.vue'),
        meta: { title: '我的借阅记录' }
      },
      {
        path: 'recommendations',
        name: 'UserRecommendations',
        component: () => import('@/views/user/Recommendations.vue'),
        meta: { title: '图书推荐' }
      },
      {
        path: 'reading-profile',
        name: 'ReadingProfile',
        component: () => import('@/views/user/ReadingProfile.vue'),
        meta: { title: '我的阅读画像' }
      },
      {
        path: 'ranking',
        name: 'UserRanking',
        component: () => import('@/views/user/Ranking.vue'),
        meta: { title: '我的排名' }
      },
      {
        path: 'calendar',
        name: 'BorrowCalendar',
        component: () => import('@/views/user/Calendar.vue'),
        meta: { title: '借阅日历' }
      }
    ]
  },
  // 图书管理员路由
  {
    path: '/librarian',
    component: () => import('@/layouts/LibrarianLayout.vue'),
    meta: { requiresAuth: true, userType: 2 },
    children: [
      {
        path: 'dashboard',
        name: 'LibrarianDashboard',
        component: () => import('@/views/librarian/Dashboard.vue'),
        meta: { title: '管理员工作台' }
      },
      {
        path: 'records',
        name: 'LibrarianRecords',
        component: () => import('@/views/librarian/Records.vue'),
        meta: { title: '借阅记录查询' }
      },
      {
        path: 'overdue',
        name: 'OverdueManagement',
        component: () => import('@/views/librarian/OverdueManagement.vue'),
        meta: { title: '逾期情况分析' }
      },
      {
        path: 'active-users',
        name: 'ActiveUsers',
        component: () => import('@/views/librarian/ActiveUsers.vue'),
        meta: { title: '活跃用户分析' }
      },
      {
        path: 'book-detail',
        name: 'BookDetail',
        component: () => import('@/views/librarian/BookDetail.vue'),
        meta: { title: '图书详情分析' }
      },
      {
        path: 'book-ranking',
        name: 'BookRanking',
        component: () => import('@/views/librarian/BookRanking.vue'),
        meta: { title: '图书排行与分析' }
      },
      {
        path: 'time-distribution',
        name: 'TimeDistribution',
        component: () => import('@/views/librarian/TimeDistribution.vue'),
        meta: { title: '时间分布分析' }
      }
    ]
  },
  // 高级管理员路由
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, userType: 1 },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '运营综合看板' }
      },
      {
        path: 'user-profile',
        name: 'UserProfileAnalysis',
        component: () => import('@/views/admin/UserProfile.vue'),
        meta: { title: '用户画像分析' }
      },
      {
        path: 'major-reading',
        name: 'MajorReading',
        component: () => import('@/views/admin/MajorReading.vue'),
        meta: { title: '专业阅读特征' }
      },
      {
        path: 'recommendation-monitor',
        name: 'RecommendationMonitor',
        component: () => import('@/views/admin/RecommendationMonitor.vue'),
        meta: { title: '推荐系统监控' }
      },
      {
        path: 'collection-utilization',
        name: 'CollectionUtilization',
        component: () => import('@/views/admin/CollectionUtilization.vue'),
        meta: { title: '馆藏利用分析' }
      },
      {
        path: 'publisher-analysis',
        name: 'PublisherAnalysis',
        component: () => import('@/views/admin/PublisherAnalysis.vue'),
        meta: { title: '出版分析' }
      },
      {
        path: 'prediction-analysis',
        name: 'PredictionAnalysis',
        component: () => import('@/views/admin/PredictionAnalysis.vue'),
        meta: { title: '预测分析' }
      },
      {
        path: 'book-association',
        name: 'BookAssociation',
        component: () => import('@/views/admin/BookAssociation.vue'),
        meta: { title: '图书关联分析' }
      },
      {
        path: 'user-clustering',
        name: 'UserClustering',
        component: () => import('@/views/admin/UserClustering.vue'),
        meta: { title: '用户聚类分析' }
      }
    ]
  },
  // 根据用户类型重定向到对应的dashboard
  {
    path: '/dashboard',
    name: 'Dashboard',
    beforeEnter: (to, from, next) => {
      const userStore = useUserStore()
      const userType = userStore.getUserType()
      
      if (userType === 1) {
        next('/admin/dashboard')
      } else if (userType === 2) {
        next('/librarian/dashboard')
      } else {
        next('/user/dashboard')
      }
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 图书馆借阅分析系统`
  }
  
  // 判断是否需要登录
  if (to.meta.requiresAuth) {
    if (!userStore.isLogin()) {
      next('/login')
      return
    }
    
    // 判断用户类型权限
    if (to.meta.userType && userStore.getUserType() !== to.meta.userType) {
      next('/dashboard')
      return
    }
  }
  
  // 如果已登录，访问登录页则跳转到dashboard
  if (to.path === '/login' && userStore.isLogin()) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router

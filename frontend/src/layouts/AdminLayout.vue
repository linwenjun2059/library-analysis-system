<template>
  <el-container class="layout-container">
    <el-aside width="200px" class="layout-aside">
      <div class="logo">
        <el-icon :size="24"><Monitor /></el-icon>
        <span>运营中心</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="layout-menu"
        router
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>运营看板</span>
        </el-menu-item>
        <el-menu-item index="/admin/user-profile">
          <el-icon><UserFilled /></el-icon>
          <span>用户画像</span>
        </el-menu-item>
        <el-menu-item index="/admin/major-reading">
          <el-icon><Reading /></el-icon>
          <span>专业阅读</span>
        </el-menu-item>
        <el-menu-item index="/admin/recommendation-monitor">
          <el-icon><Monitor /></el-icon>
          <span>推荐监控</span>
        </el-menu-item>
        <el-menu-item index="/admin/collection-utilization">
          <el-icon><DataLine /></el-icon>
          <span>馆藏利用</span>
        </el-menu-item>
        <el-menu-item index="/admin/publisher-analysis">
          <el-icon><OfficeBuilding /></el-icon>
          <span>出版分析</span>
        </el-menu-item>
        <el-menu-item index="/admin/prediction-analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>预测分析</span>
        </el-menu-item>
        <el-menu-item index="/admin/book-association">
          <el-icon><Connection /></el-icon>
          <span>图书关联分析</span>
        </el-menu-item>
        <el-menu-item index="/admin/user-clustering">
          <el-icon><PieChart /></el-icon>
          <span>用户聚类分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag type="danger">系统管理员</el-tag>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.userInfo.realName }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '运营综合看板')

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('退出成功')
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  width: 100%;
  height: 100vh;
  background: transparent;
}

.layout-aside {
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
  
  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    font-size: 18px;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    color: #111827;
    border-bottom: 1px solid #e5e7eb;
    padding: 0 20px;
    
    .el-icon {
      color: #3b82f6;
      font-size: 24px;
    }
  }
  
  .layout-menu {
    border-right: none;
    padding: 12px 0;
    background: transparent;
    
    :deep(.el-menu-item) {
      margin: 4px 12px;
      border-radius: 8px;
      transition: all 0.2s ease;
      color: #6b7280;
      font-weight: 500;
      font-family: 'Inter', sans-serif;
      
      &:hover {
        background: #f3f4f6;
        color: #111827;
      }
      
      &.is-active {
        background: #eff6ff;
        color: #3b82f6;
        font-weight: 600;
        
        .el-icon {
          color: #3b82f6;
        }
      }
    }
  }
}

.layout-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  
  .header-left {
    .page-title {
      font-size: 20px;
      font-weight: 700;
      font-family: 'Inter', sans-serif;
      color: #111827;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .user-info {
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 8px;
      transition: all 0.2s ease;
      font-weight: 500;
      color: #374151;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      
      &:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
        color: #111827;
      }
    }
  }
}

.layout-main {
  background: transparent;
  padding: 24px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

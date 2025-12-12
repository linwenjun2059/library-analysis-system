<template>
  <el-container class="layout-container">
    <el-aside width="200px" class="layout-aside">
      <div class="logo">
        <el-icon :size="24"><Reading /></el-icon>
        <span>借阅分析</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="layout-menu"
        router
      >
        <el-menu-item index="/user/dashboard">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
        <el-menu-item index="/user/records">
          <el-icon><Document /></el-icon>
          <span>借阅记录</span>
        </el-menu-item>
        <el-menu-item index="/user/recommendations">
          <el-icon><Star /></el-icon>
          <span>图书推荐</span>
        </el-menu-item>
        <el-menu-item index="/user/reading-profile">
          <el-icon><DataAnalysis /></el-icon>
          <span>我的阅读画像</span>
        </el-menu-item>
        <el-menu-item index="/user/ranking">
          <el-icon><Trophy /></el-icon>
          <span>我的排名</span>
        </el-menu-item>
        <el-menu-item index="/user/calendar">
          <el-icon><Calendar /></el-icon>
          <span>借阅日历</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ userStore.userInfo.realName || userStore.userInfo.userid }}
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
const pageTitle = computed(() => route.meta.title || '个人中心')

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
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
}

.layout-aside {
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
  
  .logo {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 700;
    background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    padding: 0 20px;
    
    .el-icon {
      color: #409eff;
      font-size: 24px;
    }
  }
  
  .layout-menu {
    border-right: none;
    padding: 10px 0;
    
    :deep(.el-menu-item) {
      margin: 4px 12px;
      border-radius: 8px;
      transition: all 0.3s;
      
      &:hover {
        background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(103, 194, 58, 0.1) 100%);
        color: #409eff;
      }
      
      &.is-active {
        background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
        color: #fff;
        font-weight: 600;
        
        .el-icon {
          color: #fff;
        }
      }
    }
  }
}

.layout-header {
  background: #ffffff;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  
  .header-left {
    .page-title {
      font-size: 20px;
      font-weight: 700;
      background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
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
      transition: all 0.3s;
      font-weight: 500;
      color: #606266;
      
      &:hover {
        background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(103, 194, 58, 0.1) 100%);
        color: #409eff;
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
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

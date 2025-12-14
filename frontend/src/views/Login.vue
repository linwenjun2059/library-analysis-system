<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    
    <div class="login-card">
      <!-- Logo和标题 -->
      <div class="login-header">
        <div class="logo">
          <el-icon :size="48" color="#ffffff"><Reading /></el-icon>
        </div>
        <h1 class="title">图书馆借阅行为分析系统</h1>
        <p class="subtitle">Library Analysis System</p>
      </div>
      
      <!-- 登录标签页 -->
      <el-tabs v-model="activeTab" class="login-tabs" stretch>
        <!-- 普通用户登录 -->
        <el-tab-pane name="user">
          <template #label>
            <span class="tab-label">
              <el-icon><User /></el-icon>
              <span>普通用户</span>
            </span>
          </template>
          
          <div class="form-container">
            <el-form :model="passwordlessForm" :rules="passwordlessRules" ref="passwordlessFormRef">
              <el-form-item prop="userid">
                <el-input
                  v-model="passwordlessForm.userid"
                  placeholder="请输入用户ID"
                  size="large"
                  clearable
                  @keyup.enter="handlePasswordlessLogin"
                >
                  <template #prefix>
                    <el-icon><Postcard /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-button"
                @click="handlePasswordlessLogin"
              >
                <el-icon v-if="!loading"><Right /></el-icon>
                <span>{{ loading ? '登录中...' : '免密登录' }}</span>
              </el-button>
            </el-form>
            
            <!-- 免密登录说明 -->
            <div class="info-card">
              <div class="info-header">
                <el-icon color="#409eff"><InfoFilled /></el-icon>
                <span>免密登录说明</span>
              </div>
              <p class="info-text">学生/教师可使用数据集中的USERID进行免密登录</p>
              <div class="test-account" @click="useTestUserId('4fc844c094896fc30349e7fa667ffb9b')">
                <span class="account">4fc844c094896fc30349e7fa667ffb9b</span>
                <el-icon class="copy-icon"><CopyDocument /></el-icon>
              </div>
              <p class="hint">💡 点击上方测试账号自动填入</p>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 管理员登录 -->
        <el-tab-pane name="admin">
          <template #label>
            <span class="tab-label">
              <el-icon><Stamp /></el-icon>
              <span>管理员</span>
            </span>
          </template>
          
          <div class="form-container">
            <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef">
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-button"
                @click="handleLogin"
              >
                <el-icon v-if="!loading"><Right /></el-icon>
                <span>{{ loading ? '登录中...' : '登录系统' }}</span>
              </el-button>
            </el-form>
            
            <!-- 默认管理员账号 -->
            <div class="info-card">
              <div class="info-header">
                <el-icon color="#67c23a"><Key /></el-icon>
                <span>默认管理员账号</span>
              </div>
              
              <div class="test-accounts">
                <div class="account-item" @click="useAdminAccount('admin', '123456')">
                  <div class="account-label">
                    <el-icon><Avatar /></el-icon>
                    <span>系统管理员</span>
                  </div>
                  <div class="account-value">
                    <el-tag type="primary" size="small">admin</el-tag>
                    <span class="divider">/</span>
                    <el-tag type="info" size="small">123456</el-tag>
                  </div>
                </div>
                
                <div class="account-item" @click="useAdminAccount('librarian', '123456')">
                  <div class="account-label">
                    <el-icon><Reading /></el-icon>
                    <span>图书管理员</span>
                  </div>
                  <div class="account-value">
                    <el-tag type="success" size="small">librarian</el-tag>
                    <span class="divider">/</span>
                    <el-tag type="info" size="small">123456</el-tag>
                  </div>
                </div>
              </div>
              
              <p class="hint">💡 点击上方测试账号自动填入</p>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 页脚 -->
    <div class="login-footer">
      <p>© 2025 Library Analysis System. All rights reserved.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { login } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('user')
const loading = ref(false)
const loginFormRef = ref(null)
const passwordlessFormRef = ref(null)

// 管理员账号登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 普通用户免密登录表单
const passwordlessForm = reactive({
  userid: ''
})

const passwordlessRules = {
  userid: [{ required: true, message: '请输入用户ID', trigger: 'blur' }]
}

// 管理员账号密码登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      loading.value = true
      const res = await login(loginForm)
      
      // 保存token和用户信息
      userStore.setToken(res.data.token)
      userStore.setUserInfo(res.data)
      
      ElMessage.success('登录成功')
      
      // 根据用户类型跳转
      const userType = res.data.userType
      if (userType === 1) {
        router.push('/admin/dashboard')
      } else if (userType === 2) {
        router.push('/librarian/dashboard')
      } else {
        router.push('/user/dashboard')
      }
    } catch (error) {
      console.error('登录失败：', error)
    } finally {
      loading.value = false
    }
  })
}

// 普通用户免密登录
const handlePasswordlessLogin = async () => {
  if (!passwordlessFormRef.value) return
  
  await passwordlessFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      loading.value = true
      // 普通用户：用户名和密码都是userid
      const res = await login({
        username: passwordlessForm.userid,
        password: passwordlessForm.userid
      })
      
      // 保存token和用户信息
      userStore.setToken(res.data.token)
      userStore.setUserInfo(res.data)
      
      ElMessage.success('登录成功')
      
      // 跳转到普通用户仪表板
      router.push('/user/dashboard')
    } catch (error) {
      console.error('登录失败：', error)
      ElMessage.error('登录失败，请检查用户ID是否正确')
    } finally {
      loading.value = false
    }
  })
}

// 使用测试用户ID
const useTestUserId = (userid) => {
  passwordlessForm.userid = userid
  ElMessage.success('已填入测试账号')
}

// 使用管理员账号
const useAdminAccount = (username, password) => {
  loginForm.username = username
  loginForm.password = password
  ElMessage.success('已填入管理员账号')
}
</script>

<style scoped lang="scss">
.login-container {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.background-decoration {
  display: none;
}

.login-card {
  position: relative;
  width: 480px;
  padding: 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.title {
  font-size: 28px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  color: #111827;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
}

.login-tabs {
  margin-bottom: 0;
}

.login-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  background: #3b82f6;
}

.login-tabs :deep(.el-tabs__item) {
  color: #6b7280;
  font-weight: 500;
  transition: all 0.2s;
  
  &:hover {
    color: #111827;
  }
  
  &.is-active {
    color: #3b82f6;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
}

.form-container {
  padding: 24px 0 0 0;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.info-card {
  margin-top: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  font-family: 'Inter', sans-serif;
}

.info-text {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.test-account {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 2px dashed #3b82f6;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 12px;
}

.test-account:hover {
  border-color: #2563eb;
  background: #eff6ff;
  transform: translateX(4px);
}

.test-account .account {
  flex: 1;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: #3b82f6;
  font-weight: 600;
}

.test-account .copy-icon {
  color: #9ca3af;
  transition: color 0.2s;
}

.test-account:hover .copy-icon {
  color: #3b82f6;
}

.test-accounts {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
}

.account-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s ease;
}

.account-item:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.account-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  font-family: 'Inter', sans-serif;
}

.account-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-value .divider {
  color: #d1d5db;
  font-weight: 600;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
  font-style: italic;
}

.login-footer {
  position: relative;
  margin-top: 30px;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  font-family: 'Inter', sans-serif;
}

.login-footer p {
  margin: 0;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-icon) {
  color: #6b7280;
}

@media (max-width: 768px) {
  .login-card {
    width: 90%;
    max-width: 400px;
    padding: 30px 24px;
  }
  
  .title {
    font-size: 24px;
  }
  
  .test-account .account {
    font-size: 11px;
  }
}
</style>

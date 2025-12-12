<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 个人信息卡片 -->
      <el-col :span="24">
        <el-card class="profile-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span><el-icon><User /></el-icon> 个人信息</span>
            </div>
          </template>
          <div class="profile-content" v-loading="loading">
            <div class="avatar-section">
              <el-avatar :size="80" :icon="UserFilled" />
              <div class="user-info">
                <h3>{{ userDimension?.userid }}</h3>
                <p style="color: #999; margin-top: 5px;">{{ userDimension?.userTypeName }}</p>
              </div>
            </div>
            <el-divider />
            <el-descriptions :column="3" border>
              <el-descriptions-item label="院系">
                {{ userDimension?.deptName || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="用户类型">
                {{ userDimension?.userTypeName || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="性别">
                {{ userDimension?.gender || '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
      
      <!-- 借阅统计 -->
      <el-col :xs="24" :sm="12" :md="8" v-if="lendSummary">
        <el-card shadow="hover">
          <el-statistic title="总借阅次数" :value="lendSummary.totalLendCount">
            <template #prefix>
              <el-icon color="#409eff"><Reading /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" v-if="lendSummary">
        <el-card shadow="hover">
          <el-statistic title="平均借阅天数" :value="lendSummary.avgBorrowDays" :precision="1">
            <template #prefix>
              <el-icon color="#67c23a"><Timer /></el-icon>
            </template>
            <template #suffix>天</template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" v-if="lendSummary">
        <el-card shadow="hover">
          <el-statistic 
            title="逾期率" 
            :value="(lendSummary.overdueRate * 100)" 
            :precision="2"
          >
            <template #prefix>
              <el-icon color="#f56c6c"><Warning /></el-icon>
            </template>
            <template #suffix>%</template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <!-- 借阅偏好 -->
      <el-col :span="24" v-if="lendSummary">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span><el-icon><Histogram /></el-icon> 借阅偏好</span>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-item">
                <span class="label">偏好主题：</span>
                <el-tag type="success" v-if="lendSummary.favoriteSubject">
                  {{ lendSummary.favoriteSubject }}
                </el-tag>
                <span v-else style="color: #999;">暂无数据</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-item">
                <span class="label">偏好位置：</span>
                <el-tag type="info" v-if="lendSummary.favoriteLocation">
                  {{ lendSummary.favoriteLocation }}
                </el-tag>
                <span v-else style="color: #999;">暂无数据</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUserLendSummary, getUserDimension } from '@/api/user'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const lendSummary = ref(null)
const userDimension = ref(null)

const loadData = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    
    // 并发请求
    const [summaryRes, dimensionRes] = await Promise.all([
      getUserLendSummary(userid).catch(() => ({ data: null })),
      getUserDimension(userid).catch(() => ({ data: null }))
    ])
    
    lendSummary.value = summaryRes.data
    userDimension.value = dimensionRes.data
  } catch (error) {
    console.error('加载数据失败：', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 16px;
    color: #303133;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  .profile-card {
    margin-bottom: 20px;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .profile-content {
      .avatar-section {
        display: flex;
        align-items: center;
        gap: 20px;
        
        .user-info {
          h3 {
            margin-bottom: 8px;
            font-size: 22px;
            font-weight: 700;
            background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          }
        }
      }
    }
  }
  
  .info-item {
    margin-bottom: 15px;
    
    .label {
      display: inline-block;
      margin-bottom: 8px;
      font-weight: 600;
      color: #606266;
    }
  }
  
  :deep(.el-card) {
    margin-bottom: 20px;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .el-card__header {
      background: linear-gradient(135deg, rgba(64, 158, 255, 0.05) 0%, rgba(103, 194, 58, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
  }
  
  :deep(.el-statistic) {
    .el-statistic__head {
      font-weight: 600;
      color: #606266;
      margin-bottom: 12px;
    }
    
    .el-statistic__number {
      font-weight: 700;
      font-size: 28px;
    }
  }
}
</style>

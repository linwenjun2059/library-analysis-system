<template>
  <div class="ranking-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Trophy /></el-icon> 我的排名（按借阅量排名）</span>
        </div>
      </template>
      
      <div v-loading="loading">
        <el-empty v-if="!ranking" description="暂无排名数据" />
        
        <div v-else>
          <el-row :gutter="20">
            <!-- 院系排名 -->
            <el-col :span="12">
              <el-card shadow="hover" class="rank-card">
                <div class="rank-header">
                  <h3>院系借阅量排名</h3>
                  <el-tag type="success" size="large">{{ ranking.dept }}</el-tag>
                </div>
                <el-divider />
                <div class="rank-content">
                  <div class="rank-number">
                    <span class="rank">{{ ranking.deptRank }}</span>
                    <span class="total">/ {{ ranking.deptTotalUsers }}</span>
                  </div>
                  <el-progress 
                    :percentage="(1 - ranking.percentileDept / 100) * 100" 
                    :color="progressColors"
                    :stroke-width="20"
                  >
                    <span class="progress-text">超越 {{ (100 - ranking.percentileDept).toFixed(1) }}% 的同学</span>
                  </el-progress>
                </div>
              </el-card>
            </el-col>
            
            <!-- 专业排名 -->
            <el-col :span="12">
              <el-card shadow="hover" class="rank-card">
                <div class="rank-header">
                  <h3>专业借阅量排名</h3>
                  <el-tag type="warning" size="large">{{ ranking.occupation }}</el-tag>
                </div>
                <el-divider />
                <div class="rank-content">
                  <div class="rank-number">
                    <span class="rank">{{ ranking.occupationRank }}</span>
                    <span class="total">/ {{ ranking.occupationTotalUsers }}</span>
                  </div>
                  <el-progress 
                    :percentage="(1 - ranking.percentileOccupation / 100) * 100" 
                    :color="progressColors"
                    :stroke-width="20"
                  >
                    <span class="progress-text">超越 {{ (100 - ranking.percentileOccupation).toFixed(1) }}% 的同学</span>
                  </el-progress>
                </div>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 借阅统计 -->
          <el-card shadow="hover" style="margin-top: 20px;">
            <template #header>
              <span>借阅统计</span>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总借阅量">
                {{ ranking.totalBorrowCount }} 本
              </el-descriptions-item>
              <el-descriptions-item label="平均借阅天数">
                {{ lendSummary?.avgBorrowDays ? lendSummary.avgBorrowDays.toFixed(1) + ' 天' : '-' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUserRanking } from '@/api/statistics'
import { getUserLendSummary } from '@/api/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const ranking = ref(null)
const lendSummary = ref(null)

const progressColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 }
]

const loadRanking = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    
    // 并发加载排名和借阅统计
    const [rankRes, summaryRes] = await Promise.all([
      getUserRanking(userid),
      getUserLendSummary(userid).catch(() => ({ data: null }))
    ])
    
    ranking.value = rankRes.data
    lendSummary.value = summaryRes.data
    
    console.log('✅ 排名数据：', ranking.value)
    console.log('✅ 借阅统计：', lendSummary.value)
  } catch (error) {
    console.error('❌ 加载排名失败：', error)
    ElMessage.error('加载排名失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRanking()
})
</script>

<style scoped lang="scss">
.ranking-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .rank-card {
    .rank-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h3 {
        margin: 0;
        font-size: 18px;
        color: #333;
      }
    }
    
    .rank-content {
      .rank-number {
        text-align: center;
        margin-bottom: 30px;
        
        .rank {
          font-size: 48px;
          font-weight: 700;
          color: #409eff;
        }
        
        .total {
          font-size: 24px;
          color: #999;
          margin-left: 5px;
        }
      }
      
      .progress-text {
        font-size: 14px;
        font-weight: 600;
      }
    }
  }
}
</style>

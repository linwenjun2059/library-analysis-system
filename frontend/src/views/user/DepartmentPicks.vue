<template>
  <div class="dept-picks-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><School /></el-icon> 院系推荐</span>
          <el-tag type="success" v-if="pagination.total > 0">
            共 {{ pagination.total }} 本
          </el-tag>
        </div>
      </template>
      
      <div v-loading="loading">
        <!-- 院系偏好信息 -->
        <el-alert
          v-if="deptPreference"
          :title="`${deptPreference.dept} 最喜欢的主题：${deptPreference.favoriteSubject}`"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <template #default>
            <p>主题借阅次数：{{ deptPreference.subjectLendCount }}</p>
            <p>总借阅次数：{{ deptPreference.totalLendCount }}</p>
            <p>偏好率：{{ (deptPreference.preferenceRate * 100).toFixed(2) }}%</p>
          </template>
        </el-alert>
        
        <!-- 推荐图书列表 -->
        <el-table :data="paginatedBooks" stripe>
          <el-table-column prop="rankNo" label="排名" width="80" align="center">
            <template #default="{ row }">
              <el-tag 
                :type="row.rankNo <= 3 ? 'danger' : row.rankNo <= 10 ? 'warning' : 'info'"
                effect="dark"
              >
                {{ row.rankNo }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip />
          <el-table-column prop="author" label="作者" width="150" show-overflow-tooltip />
          <el-table-column prop="subject" label="主题分类" width="120" />
          <el-table-column prop="borrowCount" label="借阅次数" width="120" align="center" sortable />
        </el-table>
        
        <div class="pagination-container" v-if="books.length > 0">
          <el-pagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 30, 50]"
            :total="pagination.total"
            :background="true"
            :hide-on-single-page="false"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getDeptPreference, getDeptRecommendBooks } from '@/api/statistics'
import { getUserDimension } from '@/api/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const deptPreference = ref(null)
const books = ref([])

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 计算当前页显示的图书
const paginatedBooks = computed(() => {
  const start = (pagination.current - 1) * pagination.size
  const end = start + pagination.size
  return books.value.slice(start, end)
})

const loadData = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    
    // 获取用户院系
    const userRes = await getUserDimension(userid)
    const dept = userRes.data.deptName
    
    // 获取院系偏好
    const preferenceRes = await getDeptPreference(dept)
    deptPreference.value = preferenceRes.data
    
    // 获取院系推荐图书（获取所有数据）
    const booksRes = await getDeptRecommendBooks({ dept, limit: 100 })
    books.value = booksRes.data || []
    pagination.total = books.value.length
    pagination.current = 1
    
    console.log(`✅ 院系推荐加载成功：共 ${pagination.total} 本`)
  } catch (error) {
    console.error('❌ 加载院系推荐失败：', error)
    ElMessage.error('加载院系推荐失败')
    books.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  pagination.current = 1
}

const handleCurrentChange = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.dept-picks-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}
</style>

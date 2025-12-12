<template>
  <div class="hot-books-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><TrendCharts /></el-icon> 热门图书 TOP 100</span>
          <el-tag type="danger" v-if="pagination.total > 0">
            共 {{ pagination.total }} 本
          </el-tag>
        </div>
      </template>
      
      <el-table 
        :data="paginatedBooks" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
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
      
      <div class="pagination-container" v-if="hotBooks.length > 0">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          :background="true"
          :hide-on-single-page="false"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getHotBooks } from '@/api/book'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const hotBooks = ref([])

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

// 计算当前页显示的图书
const paginatedBooks = computed(() => {
  const start = (pagination.current - 1) * pagination.size
  const end = start + pagination.size
  return hotBooks.value.slice(start, end)
})

const loadHotBooks = async () => {
  try {
    loading.value = true
    const res = await getHotBooks({ limit: 100 })
    hotBooks.value = res.data || []
    pagination.total = hotBooks.value.length
    pagination.current = 1
    
    console.log(`✅ 加载热门图书成功：共 ${pagination.total} 本`)
  } catch (error) {
    console.error('❌ 加载热门图书失败：', error)
    ElMessage.error('加载热门图书失败')
    hotBooks.value = []
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
  loadHotBooks()
})
</script>

<style scoped lang="scss">
.hot-books-container {
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

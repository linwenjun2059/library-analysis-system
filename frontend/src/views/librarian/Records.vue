<template>
  <div class="records-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Document /></el-icon> 借阅业务管理</span>
        </div>
      </template>
      
      <div class="search-box">
        <el-row :gutter="20" style="margin-bottom: 15px;">
          <el-col :span="8">
            <el-input
              v-model="searchForm.keyword"
              placeholder="请输入用户ID或图书ID"
              clearable
            />
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 100%;"
            />
          </el-col>
          <el-col :span="8">
            <el-select
              v-model="searchForm.returnStatus"
              placeholder="归还状态"
              clearable
              style="width: 100%;"
            >
              <el-option label="已归还" value="returned" />
              <el-option label="未归还" value="not_returned" />
            </el-select>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-select
              v-model="searchForm.overdueStatus"
              placeholder="逾期状态"
              clearable
              style="width: 100%;"
            >
              <el-option label="正常" value="normal" />
              <el-option label="逾期" value="overdue" />
            </el-select>
          </el-col>
          <el-col :span="16" style="text-align: right;">
            <el-button type="primary" :icon="Search" @click="handleSearch">
              搜索
            </el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </div>
      
      <el-divider />
      
      <el-table 
        :data="tableData" 
        v-loading="loading"
        stripe
      >
        <el-table-column prop="lendId" label="借阅ID" min-width="180" show-overflow-tooltip />
        <el-table-column prop="userid" label="用户ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="bookId" label="图书ID" min-width="180" show-overflow-tooltip />
        <el-table-column prop="lendDate" label="借阅日期" min-width="120" />
        <el-table-column prop="retDate" label="归还日期" min-width="120" />
        <el-table-column prop="borrowDays" label="借阅天数" width="100" align="center" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.retDate ? 'info' : 'warning'">
              {{ row.retDate ? '已归还' : '未归还' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="是否逾期" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.isOverdue ? 'danger' : 'success'">
              {{ row.isOverdue ? '逾期' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAllLendRecords } from '@/api/user'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  keyword: '',
  dateRange: [],
  returnStatus: '',
  overdueStatus: ''
})

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const loadRecords = async () => {
  try {
    loading.value = true
    
    const params = {
      current: pagination.current,
      size: pagination.size,
      keyword: searchForm.keyword || undefined,
      startDate: searchForm.dateRange && searchForm.dateRange[0] ? 
        dayjs(searchForm.dateRange[0]).format('YYYY-MM-DD') : undefined,
      endDate: searchForm.dateRange && searchForm.dateRange[1] ? 
        dayjs(searchForm.dateRange[1]).format('YYYY-MM-DD') : undefined,
      returnStatus: searchForm.returnStatus || undefined,
      overdueStatus: searchForm.overdueStatus || undefined
    }
    
    const res = await getAllLendRecords(params)
    tableData.value = res.data.records || []
    pagination.total = res.data.total || 0
    
    console.log(`✅ 加载借阅记录成功：共 ${pagination.total} 条`)
  } catch (error) {
    console.error('❌ 加载借阅记录失败：', error)
    ElMessage.error('加载借阅记录失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadRecords()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.dateRange = []
  searchForm.returnStatus = ''
  searchForm.overdueStatus = ''
  pagination.current = 1
  loadRecords()
}

const handleSizeChange = () => {
  pagination.current = 1
  loadRecords()
}

const handleCurrentChange = () => {
  loadRecords()
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped lang="scss">
.records-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .search-box {
    margin-bottom: 20px;
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>

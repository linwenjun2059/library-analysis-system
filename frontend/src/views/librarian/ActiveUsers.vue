<template>
  <div class="active-users-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><User /></el-icon> 活跃用户统计</span>
          <el-button type="primary" size="small" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="viewMode">
        <!-- 图表视图 -->
        <el-tab-pane label="📊 图表视图" name="chart">
          <el-row :gutter="20">
            <el-col :span="24">
              <el-card shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>活跃用户排行榜（TOP 20）</span>
                    <el-select v-model="topLimit" @change="loadData" style="width: 120px;">
                      <el-option label="TOP 20" :value="20" />
                      <el-option label="TOP 50" :value="50" />
                      <el-option label="TOP 100" :value="100" />
                    </el-select>
                  </div>
                </template>
                <div ref="chartRef" style="width: 100%; height: 500px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>院系分布（TOP 10）</span>
                </template>
                <div ref="deptChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>读者类型分布</span>
                </template>
                <div ref="typeChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
          <div style="margin-bottom: 15px;">
            <el-space wrap>
              <el-input v-model="searchText" placeholder="搜索用户ID" clearable style="width: 200px;">
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="deptFilter" placeholder="按院系筛选" clearable style="width: 200px;">
                <el-option 
                  v-for="dept in deptList" 
                  :key="dept" 
                  :label="dept" 
                  :value="dept" 
                />
              </el-select>
              <el-select v-model="typeFilter" placeholder="按读者类型筛选" clearable style="width: 150px;">
                <el-option 
                  v-for="type in typeList" 
                  :key="type" 
                  :label="type" 
                  :value="type" 
                />
              </el-select>
            </el-space>
          </div>
          
          <el-table 
            :data="pagedUsers" 
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
            <el-table-column prop="userid" label="用户ID" width="200" />
            <el-table-column prop="dept" label="院系" width="200" show-overflow-tooltip />
            <el-table-column prop="redrTypeName" label="读者类型" width="120" />
            <el-table-column prop="borrowCount" label="借阅次数" width="120" align="center" sortable />
          </el-table>
          
          <el-pagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { getActiveUsers } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const viewMode = ref('chart')
const topLimit = ref(20)
const searchText = ref('')
const deptFilter = ref('')
const typeFilter = ref('')

const chartRef = ref(null)
const deptChartRef = ref(null)
const typeChartRef = ref(null)

let chart = null
let deptChart = null
let typeChart = null

const activeUsersData = ref([])

const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 计算属性
const filteredUsers = computed(() => {
  let result = activeUsersData.value
  
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    result = result.filter(user => 
      user.userid && user.userid.toLowerCase().includes(keyword)
    )
  }
  
  if (deptFilter.value) {
    result = result.filter(user => user.dept === deptFilter.value)
  }
  
  if (typeFilter.value) {
    result = result.filter(user => user.redrTypeName === typeFilter.value)
  }
  
  return result
})

const pagedUsers = computed(() => {
  const start = (pagination.current - 1) * pagination.size
  const end = start + pagination.size
  return filteredUsers.value.slice(start, end)
})

const deptList = computed(() => {
  const depts = new Set()
  activeUsersData.value.forEach(user => {
    if (user.dept) depts.add(user.dept)
  })
  return Array.from(depts).sort()
})

const typeList = computed(() => {
  const types = new Set()
  activeUsersData.value.forEach(user => {
    if (user.redrTypeName) types.add(user.redrTypeName)
  })
  return Array.from(types).sort()
})

// 初始化主图表
const initChart = () => {
  if (!chartRef.value || activeUsersData.value.length === 0) return
  
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  
  const topN = activeUsersData.value.slice(0, topLimit.value).reverse()
  const labels = topN.map(item => {
    const dept = item.dept || '未知院系'
    return dept.length > 20 ? dept.substring(0, 20) + '...' : dept
  })
  const counts = topN.map(item => item.borrowCount || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = topN[params[0].dataIndex]
        return `用户ID: ${item.userid}<br/>院系: ${item.dept || '未知'}<br/>读者类型: ${item.redrTypeName || '未知'}<br/>借阅次数: ${params[0].value}`
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '借阅次数'
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        interval: 0,
        fontSize: 12
      }
    },
    series: [{
      name: '借阅次数',
      type: 'bar',
      data: counts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#f5a623' },
          { offset: 0.5, color: '#e6a23c' },
          { offset: 1, color: '#e6a23c' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  chart.setOption(option)
}

// 初始化院系分布图表
const initDeptChart = () => {
  if (!deptChartRef.value || activeUsersData.value.length === 0) return
  
  if (!deptChart) {
    deptChart = echarts.init(deptChartRef.value)
  }
  
  const deptMap = {}
  activeUsersData.value.forEach(user => {
    if (user.dept) {
      deptMap[user.dept] = (deptMap[user.dept] || 0) + 1
    }
  })
  
  const top10 = Object.entries(deptMap)
    .map(([dept, count]) => ({ dept, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}人'
    },
    grid: {
      left: '30%',
      right: '5%',
      bottom: '10%',
      top: '5%'
    },
    xAxis: {
      type: 'value',
      name: '用户数'
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => {
        const dept = item.dept || '未知'
        return dept.length > 15 ? dept.substring(0, 15) + '...' : dept
      }),
      axisLabel: {
        interval: 0
      }
    },
    series: [{
      name: '用户数',
      type: 'bar',
      data: top10.map(item => item.count),
      itemStyle: { color: '#409eff' },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  deptChart.setOption(option)
}

// 初始化读者类型分布图表
const initTypeChart = () => {
  if (!typeChartRef.value || activeUsersData.value.length === 0) return
  
  if (!typeChart) {
    typeChart = echarts.init(typeChartRef.value)
  }
  
  const typeMap = {}
  activeUsersData.value.forEach(user => {
    const type = user.redrTypeName || '未知'
    typeMap[type] = (typeMap[type] || 0) + 1
  })
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
      name: '用户数',
      type: 'pie',
      radius: '60%',
      data: Object.entries(typeMap).map(([type, count]) => ({
        value: count,
        name: type
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}\n{d}%'
      }
    }]
  }
  
  typeChart.setOption(option)
}

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    const res = await getActiveUsers({ limit: 100 })
    activeUsersData.value = res.data || []
    pagination.total = filteredUsers.value.length
    pagination.current = 1
    
    // 初始化图表
    if (viewMode.value === 'chart') {
      initChart()
      initDeptChart()
      initTypeChart()
    }
    
    console.log(`✅ 加载活跃用户成功：共 ${activeUsersData.value.length} 条`)
  } catch (error) {
    console.error('❌ 加载活跃用户失败：', error)
    ElMessage.error('加载活跃用户失败')
    activeUsersData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 监听筛选条件变化
watch([searchText, deptFilter, typeFilter], () => {
  pagination.total = filteredUsers.value.length
  pagination.current = 1
})

// 监听视图模式变化
watch(viewMode, (newVal) => {
  if (newVal === 'chart' && activeUsersData.value.length > 0) {
    setTimeout(() => {
      initChart()
      initDeptChart()
      initTypeChart()
    }, 100)
  }
})

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {
    chart?.resize()
    deptChart?.resize()
    typeChart?.resize()
  })
})

onUnmounted(() => {
  chart?.dispose()
  deptChart?.dispose()
  typeChart?.dispose()
})
</script>

<style scoped lang="scss">
.active-users-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 700;
    font-size: 16px;
    color: #303133;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
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
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
  }
  
  :deep(.el-tabs) {
    .el-tabs__header {
      margin-bottom: 20px;
    }
    
    .el-tabs__item {
      font-weight: 500;
      transition: all 0.3s;
      
      &.is-active {
        font-weight: 700;
        color: #667eea;
      }
    }
    
    .el-tabs__active-bar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      height: 3px;
    }
  }
}
</style>


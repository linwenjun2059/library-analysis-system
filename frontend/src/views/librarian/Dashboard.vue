<template>
  <div class="dashboard-container" v-loading="loading">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总借阅量" :value="metrics.totalLends">
            <template #prefix>
              <el-icon color="#409eff"><Reading /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总用户数" :value="metrics.totalUsers">
            <template #prefix>
              <el-icon color="#67c23a"><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总逾期数" :value="metrics.totalOverdues">
            <template #prefix>
              <el-icon color="#e6a23c"><Warning /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="平均借阅天数" :value="metrics.avgBorrowDays" :precision="1">
            <template #prefix>
              <el-icon color="#f56c6c"><Timer /></el-icon>
            </template>
            <template #suffix>天</template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <!-- 借阅统计图表 -->
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>每日借阅趋势（数据集内最近30天，截止 2020-12-31）</span>
            </div>
          </template>
          <div ref="borrowChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 用户分布图表 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>院系借阅分布（TOP 10）</span>
            </div>
          </template>
          <div ref="userChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 图书热度图表 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>图书主题分布（TOP 15）</span>
            </div>
          </template>
          <div ref="bookChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 年度借阅趋势 -->
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ selectedYear }} 年借阅趋势分析</span>
              <el-date-picker
                v-model="selectedYear"
                type="year"
                placeholder="选择年份"
                @change="loadTrendData"
                format="YYYY"
                value-format="YYYY"
              />
            </div>
          </template>
          <div ref="chartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getOperationDashboard, getDailyStats, getDeptLendSummary, getSubjectLendSummary } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const loading = ref(false)
const chartRef = ref(null)
const borrowChartRef = ref(null)
const userChartRef = ref(null)
const bookChartRef = ref(null)

let chartInstance = null
let borrowChart = null
let userChart = null
let bookChart = null

const metrics = reactive({
  totalUsers: 0,
  totalBooks: 0,
  totalLends: 0,
  totalOverdues: 0,
  avgBorrowDays: 0
})

const selectedYear = ref('2020')
const trendData = ref([])
const borrowData = ref([])
const deptData = ref([])
const subjectData = ref([])

const initBorrowChart = () => {
  if (!borrowChartRef.value) return
  
  if (!borrowChart) {
    borrowChart = echarts.init(borrowChartRef.value)
  }
  
  // 使用真实数据
  const dates = borrowData.value.map(item => dayjs(item.statDate).format('MM-DD'))
  const lendCounts = borrowData.value.map(item => item.lendCount || 0)
  const returnCounts = borrowData.value.map(item => item.returnCount || 0)
  
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['借阅量', '归还量']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '借阅量',
        type: 'line',
        data: lendCounts,
        smooth: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '归还量',
        type: 'line',
        data: returnCounts,
        smooth: true,
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  
  borrowChart.setOption(option)
}

const initUserChart = () => {
  if (!userChartRef.value) return
  
  if (!userChart) {
    userChart = echarts.init(userChartRef.value)
  }
  
  // 使用真实数据
  const pieData = deptData.value
    .sort((a, b) => b.totalLendCount - a.totalLendCount)
    .slice(0, 10)
    .map(item => ({
      value: item.totalLendCount,
      name: item.dept
    }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [{
      name: '借阅量',
      type: 'pie',
      radius: '50%',
      data: pieData,
      label: {
        formatter: '{b}\n{d}%'
      }
    }]
  }
  
  userChart.setOption(option)
}

const initBookChart = () => {
  if (!bookChartRef.value) return
  
  if (!bookChart) {
    bookChart = echarts.init(bookChartRef.value)
  }
  
  // 使用真实数据
  const sortedData = subjectData.value
    .sort((a, b) => b.totalLendCount - a.totalLendCount)
    .slice(0, 15)
  
  const subjects = sortedData.map(item => item.subject).reverse()
  const counts = sortedData.map(item => item.totalLendCount).reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}'
    },
    grid: {
      left: '25%',
      right: '5%'
    },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: subjects,
      axisLabel: {
        interval: 0
      }
    },
    series: [{
      name: '借阅量',
      type: 'bar',
      data: counts,
      itemStyle: { color: '#67c23a' }
    }]
  }
  
  bookChart.setOption(option)
}

const initChart = (data) => {
  if (!chartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  // 解析数据
  const dates = data.map(item => dayjs(item.statDate).format('YYYY-MM-DD'))
  const lendCounts = data.map(item => item.lendCount || 0)
  const activeUsers = data.map(item => item.activeUserCount || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['借阅量', '活跃用户']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '借阅量',
        type: 'line',
        data: lendCounts,
        smooth: true,
        itemStyle: { color: '#409eff' }
      },
      {
        name: '活跃用户',
        type: 'line',
        data: activeUsers,
        smooth: true,
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

const loadDashboard = async () => {
  try {
    loading.value = true
    
    // 并行加载核心数据
    const [dashboardRes, borrowRes, deptRes, subjectRes] = await Promise.all([
      getOperationDashboard(),
      getDailyStats({ days: 30 }),
      getDeptLendSummary(),
      getSubjectLendSummary()
    ])
    
    // 解析运营看板数据
    const data = dashboardRes.data || []
    const metricsMap = {}
    data.forEach(item => {
      metricsMap[item.metricName] = item
    })
    
    metrics.totalUsers = parseInt(metricsMap['total_users']?.metricValue || 0)
    metrics.totalBooks = parseInt(metricsMap['total_books']?.metricValue || 0)
    metrics.totalLends = parseInt(metricsMap['total_lends']?.metricValue || 0)
    metrics.totalOverdues = parseInt(metricsMap['total_overdues']?.metricValue || 0)
    metrics.avgBorrowDays = parseFloat(metricsMap['avg_borrow_days']?.metricValue || 0)
    
    // 加载统计分析数据
    borrowData.value = (borrowRes.data || []).reverse()
    deptData.value = deptRes.data || []
    subjectData.value = subjectRes.data || []
    
    // 初始化核心图表
    initBorrowChart()
    initUserChart()
    initBookChart()
    
    console.log('✅ 图书管理员工作台数据加载成功', metrics)
  } catch (error) {
    console.error('❌ 加载工作台数据失败：', error)
    ElMessage.error('加载工作台数据失败')
  } finally {
    loading.value = false
  }
}

const loadTrendData = async () => {
  try {
    loading.value = true
    
    // 加载指定年份的数据
    const trendRes = await getDailyStats({ days: 365 })
    const allData = trendRes.data || []
    
    // 过滤出指定年份的数据
    const yearData = allData.filter(item => {
      return dayjs(item.statDate).format('YYYY') === selectedYear.value
    })
    
    trendData.value = yearData.reverse() // 按时间正序
    
    // 初始化图表
    if (trendData.value.length > 0) {
      initChart(trendData.value)
      console.log(`✅ 加载 ${selectedYear.value} 年趋势数据：${trendData.value.length} 天`)
    } else {
      ElMessage.warning(`${selectedYear.value} 年暂无数据`)
    }
  } catch (error) {
    console.error('❌ 加载趋势数据失败：', error)
    ElMessage.error('加载趋势数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
  loadTrendData()
  window.addEventListener('resize', () => {
    chartInstance?.resize()
    borrowChart?.resize()
    userChart?.resize()
    bookChart?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
  borrowChart?.dispose()
  userChart?.dispose()
  bookChart?.dispose()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  .stat-card {
    margin-bottom: 20px;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: none;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
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
  
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 700;
    font-size: 16px;
    color: #303133;
    padding: 4px 0;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  :deep(.el-card) {
    margin-bottom: 20px;
    
    .el-card__header {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
      padding: 16px 20px;
    }
    
    .el-card__body {
      padding: 20px;
    }
  }
}
</style>

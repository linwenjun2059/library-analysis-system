<template>
  <div class="dashboard-container" v-loading="loading">
    <el-row :gutter="20">
      <!-- KPI指标 -->
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <el-statistic title="总借阅量" :value="metrics.totalLends">
            <template #prefix>
              <el-icon color="#409eff"><Reading /></el-icon>
            </template>
          </el-statistic>
          <div class="trend" v-if="metrics.lendsCompare !== 0">
            <span :class="metrics.lendsCompare > 0 ? 'up' : 'down'">
              {{ metrics.lendsCompare > 0 ? '↑' : '↓' }} {{ Math.abs(metrics.lendsCompare) }}%
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <el-statistic title="总用户数" :value="metrics.totalUsers">
            <template #prefix>
              <el-icon color="#67c23a"><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <el-statistic title="总图书数" :value="metrics.totalBooks">
            <template #prefix>
              <el-icon color="#e6a23c"><Reading /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <el-statistic title="平均借阅天数" :value="metrics.avgBorrowDays" :precision="1">
            <template #prefix>
              <el-icon color="#f56c6c"><Timer /></el-icon>
            </template>
            <template #suffix>天</template>
          </el-statistic>
        </el-card>
      </el-col>
      
      <!-- 近30天借阅与活跃趋势 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>近30天借阅与活跃趋势（数据集截止 {{ latestDatasetDate }}）</span>
            </div>
          </template>
          <div ref="recentTrendChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 借阅次数分布（TOP100） -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>借阅次数分布（TOP100）</span>
            </div>
          </template>
          <div ref="borrowDistChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 年度借阅趋势 -->
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>年度借阅趋势</span>
            </div>
          </template>
          <div ref="trendChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 主题借阅分布TOP10 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>主题借阅分布 TOP 10</span>
            </div>
          </template>
          <div ref="subjectChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
      
      <!-- 院系借阅排名TOP10 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>院系借阅排名 TOP 10</span>
            </div>
          </template>
          <div ref="deptRankChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getOperationDashboard, getActiveUsers, getLendTrend, getDailyStats, getDeptLendSummary, getSubjectLendSummary } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const loading = ref(false)
const recentTrendChartRef = ref(null)
const borrowDistChartRef = ref(null)
const trendChartRef = ref(null)
const subjectChartRef = ref(null)
const deptRankChartRef = ref(null)

const metrics = reactive({
  totalUsers: 0,
  totalBooks: 0,
  totalLends: 0,
  todayLends: 0,
  todayActive: 0,
  totalOverdues: 0,
  avgBorrowDays: 0,
  lendsCompare: 0,
  todayCompare: 0,
  activeCompare: 0
})

const activeUsersData = ref([])
const lendTrendData = ref([])
const latestDatasetDate = ref('') // 数据集截止日期说明
const subjectData = ref([])
const deptData = ref([])
let recentTrendChart = null
let borrowDistChart = null
let trendChart = null
let subjectChart = null
let deptRankChart = null

const initRecentTrendChart = () => {
  if (!recentTrendChartRef.value || lendTrendData.value.length === 0) return

  if (!recentTrendChart) {
    recentTrendChart = echarts.init(recentTrendChartRef.value)
  }

  // 取数据集中最近30天
  const latest = lendTrendData.value[lendTrendData.value.length - 1]
  const latestDate = latest ? dayjs(latest.trendDate) : null
  const recent = latestDate
    ? lendTrendData.value.filter(item => dayjs(item.trendDate).isAfter(latestDate.subtract(30, 'day')))
    : lendTrendData.value.slice(-30)

  const xData = recent.map(i => dayjs(i.trendDate).format('MM-DD'))
  const lendSeries = recent.map(i => i.lendCount || 0)
  const activeSeries = recent.map(i => i.activeUserCount || 0)

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '8%', right: '8%', bottom: '10%', top: '10%' },
    legend: { data: ['借阅量', '活跃用户'] },
    xAxis: { type: 'category', data: xData },
    yAxis: [
      { type: 'value', name: '借阅量' },
      { type: 'value', name: '活跃用户' }
    ],
    series: [
      { name: '借阅量', type: 'bar', data: lendSeries, itemStyle: { color: '#409EFF' } },
      { name: '活跃用户', type: 'line', yAxisIndex: 1, data: activeSeries, smooth: true, itemStyle: { color: '#67C23A' } }
    ]
  }

  recentTrendChart.setOption(option)
}

const initBorrowDistChart = () => {
  if (!borrowDistChartRef.value || activeUsersData.value.length === 0) return

  if (!borrowDistChart) {
    borrowDistChart = echarts.init(borrowDistChartRef.value)
  }

  // 借阅次数分布桶（基于 TOP100 的分位数自适应）
  const counts = activeUsersData.value
    .map(u => u.borrowCount || 0)
    .filter(c => c >= 0)
    .sort((a, b) => a - b)
  const n = counts.length
  const q = p => counts.length ? counts[Math.min(n - 1, Math.max(0, Math.floor(n * p)))] : 0
  const p20 = q(0.2)
  const p40 = q(0.4)
  const p60 = q(0.6)
  const p80 = q(0.8)

  const buckets = [
    { label: `≤P20(${p20})`, min: -Infinity, max: p20 === 0 ? 0.000001 : p20 + 1e-9 },
    { label: `P20-P40(${p20}-${p40})`, min: p20, max: p40 === 0 ? p20 + 0.000001 : p40 + 1e-9 },
    { label: `P40-P60(${p40}-${p60})`, min: p40, max: p60 === 0 ? p40 + 0.000001 : p60 + 1e-9 },
    { label: `P60-P80(${p60}-${p80})`, min: p60, max: p80 === 0 ? p60 + 0.000001 : p80 + 1e-9 },
    { label: `≥P80(${p80})`, min: p80, max: Infinity }
  ]

  const dist = buckets.map(b => ({
    label: b.label,
    value: activeUsersData.value.filter(u => {
      const c = u.borrowCount || 0
      return c >= b.min && c < b.max
    }).length
  }))

  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '12%', right: '8%', bottom: '12%', top: '10%' },
    xAxis: { 
      type: 'category', 
      data: dist.map(d => d.label),
      axisLabel: { interval: 0 }
    },
    yAxis: { type: 'value', name: '人数', splitNumber: 6 },
    series: [{
      type: 'bar',
      data: dist.map(d => d.value),
      itemStyle: { color: '#F56C6C' },
      label: { show: true, position: 'top' }
    }]
  }

  borrowDistChart.setOption(option)
}

const initTrendChart = () => {
  if (!trendChartRef.value || lendTrendData.value.length === 0) return
  
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }
  
  // 按月份聚合数据
  const monthlyData = {}
  lendTrendData.value.forEach(item => {
    const date = dayjs(item.trendDate)
    const yearMonth = date.format('YYYY-MM')
    if (!monthlyData[yearMonth]) {
      monthlyData[yearMonth] = {
        lendCount: 0,
        returnCount: 0,
        activeUsers: 0,
        count: 0
      }
    }
    monthlyData[yearMonth].lendCount += item.lendCount || 0
    monthlyData[yearMonth].returnCount += item.returnCount || 0
    monthlyData[yearMonth].activeUsers += item.activeUserCount || 0
    monthlyData[yearMonth].count += 1
  })
  
  // 按年份分组（排除2021年）
  const years = {}
  Object.keys(monthlyData).sort().forEach(yearMonth => {
    const [year, month] = yearMonth.split('-')
    if (year === '2021') return  // 跳过2021年
    if (!years[year]) years[year] = {}
    years[year][month] = monthlyData[yearMonth]
  })
  
  const allYears = Object.keys(years).sort()
  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
  const monthLabels = months.map(m => `${parseInt(m)}月`)
  
  const series = allYears.map(year => {
    const data = months.map(month => {
      return years[year][month]?.lendCount || 0
    })
    return {
      name: `${year}年`,
      type: 'line',
      data: data,
      smooth: true
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = params[0].name + '<br/>'
        params.forEach(p => {
          result += `${p.marker}${p.seriesName}: ${p.value.toLocaleString()}<br/>`
        })
        return result
      }
    },
    legend: {
      data: allYears.map(y => `${y}年`)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: monthLabels
    },
    yAxis: {
      type: 'value',
      name: '借阅量'
    },
    series: series
  }
  
  trendChart.setOption(option)
}

const loadDashboard = async () => {
  try {
    loading.value = true
    
    // 并行加载所有数据
    const [dashboardRes, activeUsersRes, trendRes, subjectRes, deptRes] = await Promise.all([
      getOperationDashboard(),
      getActiveUsers({ limit: 100 }),
      getLendTrend({ days: 730 }),  // 获取2年数据
      getSubjectLendSummary(),
      getDeptLendSummary()
    ])
    
    // 解析运营看板数据
    const data = dashboardRes.data || []
    const metricsMap = {}
    data.forEach(item => {
      metricsMap[item.metricName] = item
    })
    
    // 填充KPI指标
    metrics.totalUsers = parseInt(metricsMap['total_users']?.metricValue || 0)
    metrics.totalBooks = parseInt(metricsMap['total_books']?.metricValue || 0)
    metrics.totalLends = parseInt(metricsMap['total_lends']?.metricValue || 0)
    // ADS 中字段名为 latest_date_lends / latest_date_active_users
    metrics.todayLends = parseInt(metricsMap['latest_date_lends']?.metricValue || 0)
    metrics.todayActive = parseInt(metricsMap['latest_date_active_users']?.metricValue || 0)
    metrics.totalOverdues = parseInt(metricsMap['total_overdues']?.metricValue || 0)
    metrics.avgBorrowDays = parseFloat(metricsMap['avg_borrow_days']?.metricValue || 0)
    
    // 环比数据
    metrics.lendsCompare = metricsMap['latest_date_lends']?.compareYesterday || 0
    metrics.todayCompare = metricsMap['latest_date_lends']?.compareYesterday || 0
    metrics.activeCompare = metricsMap['latest_date_active_users']?.compareYesterday || 0
    
    // 活跃用户数据
    activeUsersData.value = activeUsersRes.data || []
    
    // 借阅趋势数据：按日期升序，最大日期作为数据集截止日
    lendTrendData.value = (trendRes.data || [])
      .filter(i => i?.trendDate)
      .sort((a, b) => dayjs(a.trendDate).valueOf() - dayjs(b.trendDate).valueOf())
    const latest = lendTrendData.value[lendTrendData.value.length - 1]
    latestDatasetDate.value = latest ? dayjs(latest.trendDate).format('YYYY-MM-DD') : ''
    
    // 主题和院系数据
    subjectData.value = subjectRes.data || []
    deptData.value = deptRes.data || []
    
    // 初始化图表
    initRecentTrendChart()
    initBorrowDistChart()
    initTrendChart()
    initSubjectChart()
    initDeptRankChart()
    
    console.log('✅ 运营看板数据加载成功', {
      metrics,
      activeUsers: activeUsersData.value.length,
      trendData: lendTrendData.value.length
    })
  } catch (error) {
    console.error('❌ 加载运营看板数据失败：', error)
    ElMessage.error('加载运营看板数据失败')
  } finally {
    loading.value = false
  }
}


onMounted(() => {
  loadDashboard()
  
  window.addEventListener('resize', () => {
    recentTrendChart?.resize()
    borrowDistChart?.resize()
    trendChart?.resize()
    subjectChart?.resize()
    deptRankChart?.resize()
  })
})

const initSubjectChart = () => {
  if (!subjectChartRef.value || subjectData.value.length === 0) return
  
  if (!subjectChart) {
    subjectChart = echarts.init(subjectChartRef.value)
  }
  
  const top10 = subjectData.value
    .sort((a, b) => b.totalLendCount - a.totalLendCount)
    .slice(0, 10)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}次 ({d}%)'
    },
    series: [{
      name: '借阅量',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: top10.map(item => ({
        value: item.totalLendCount,
        name: item.subject
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
  
  subjectChart.setOption(option)
}

const initDeptRankChart = () => {
  if (!deptRankChartRef.value || deptData.value.length === 0) return
  
  if (!deptRankChart) {
    deptRankChart = echarts.init(deptRankChartRef.value)
  }
  
  const top10 = deptData.value
    .sort((a, b) => b.totalLendCount - a.totalLendCount)
    .slice(0, 10)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>借阅量: ${p.value.toLocaleString()}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '借阅量'
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => item.dept)
    },
    series: [{
      name: '借阅量',
      type: 'bar',
      data: top10.map(item => item.totalLendCount),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  deptRankChart.setOption(option)
}

onUnmounted(() => {
  recentTrendChart?.dispose()
  borrowDistChart?.dispose()
  trendChart?.dispose()
  subjectChart?.dispose()
  deptRankChart?.dispose()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  .kpi-card {
    margin-bottom: 20px;
    transition: all 0.2s ease;
    
    &:hover {
      transform: translateY(-2px);
    }
    
    .trend {
      margin-top: 12px;
      font-size: 13px;
      font-weight: 600;
      font-family: 'Inter', sans-serif;
      
      .up {
        color: #10b981;
      }
      
      .down {
        color: #ef4444;
      }
    }
    
    :deep(.el-statistic) {
      .el-statistic__head {
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        color: #6b7280;
        margin-bottom: 12px;
        font-size: 14px;
      }
      
      .el-statistic__number {
        font-weight: 700;
        font-size: 28px;
        font-family: 'Inter', sans-serif;
        color: #111827;
      }
      
      .el-statistic__suffix {
        color: #6b7280;
      }
    }
  }
  
  .card-header {
    font-weight: 700;
    font-size: 16px;
    font-family: 'Inter', sans-serif;
    color: #111827;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  :deep(.el-card) {
    margin-bottom: 20px;
    transition: all 0.2s ease;
    
    &:hover {
      transform: translateY(-2px);
    }
    
    .el-card__header {
      background: #f9fafb;
      border-bottom: 1px solid #e5e7eb;
      padding: 16px 20px;
    }
    
    .el-card__body {
      padding: 20px;
    }
  }
}
</style>

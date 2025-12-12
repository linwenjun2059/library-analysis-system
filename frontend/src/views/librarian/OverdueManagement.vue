<template>
  <div class="overdue-management-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><WarningFilled /></el-icon> 逾期管理</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab 1: 逾期概览 -->
        <el-tab-pane label="逾期概览" name="overview">
          <!-- 4个指标卡片 -->
          <el-row :gutter="20" style="margin-bottom: 20px;">
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="stat-card">
                <el-statistic title="总逾期数" :value="totalOverdue">
                  <template #prefix>
                    <el-icon color="#f56c6c"><Warning /></el-icon>
                  </template>
                </el-statistic>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="stat-card">
                <el-statistic title="当前逾期" :value="currentOverdue">
                  <template #prefix>
                    <el-icon color="#e6a23c"><Clock /></el-icon>
                  </template>
                </el-statistic>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="stat-card">
                <el-statistic title="高风险用户" :value="highRiskUsers">
                  <template #prefix>
                    <el-icon color="#f56c6c"><User /></el-icon>
                  </template>
                </el-statistic>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="stat-card">
                <el-statistic title="平均逾期天数" :value="avgOverdueDays" :precision="1" suffix="天">
                  <template #prefix>
                    <el-icon color="#909399"><Calendar /></el-icon>
                  </template>
                </el-statistic>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 图表区域 -->
          <el-row :gutter="20">
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" style="margin-bottom: 20px;">
                <template #header>
                  <span>风险等级分布</span>
                </template>
                <div ref="riskLevelChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" style="margin-bottom: 20px;">
                <template #header>
                  <span>逾期率TOP10院系</span>
                </template>
                <div ref="overdueRateChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" style="margin-bottom: 20px;">
                <template #header>
                  <span>逾期用户 TOP 10</span>
                </template>
                <div ref="overdueUsersChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" style="margin-bottom: 20px;">
                <template #header>
                  <span>逾期图书 TOP 10</span>
                </template>
                <div ref="overdueBooksChartRef" style="width: 100%; height: 350px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- Tab 2: 用户逾期 -->
        <el-tab-pane label="用户逾期" name="user">
          <div style="margin-bottom: 15px;">
            <el-space wrap>
              <el-select v-model="riskFilter" placeholder="按风险等级筛选" clearable style="width: 150px;">
                <el-option label="高风险" value="高" />
                <el-option label="中风险" value="中" />
                <el-option label="低风险" value="低" />
              </el-select>
              <el-input v-model="userSearchText" placeholder="搜索用户ID" clearable style="width: 200px;">
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-space>
          </div>
          
          <el-table 
            :data="pagedUserOverdueData" 
            v-loading="loading"
            stripe
            :max-height="600"
            style="width: 100%"
          >
            <el-table-column prop="targetId" label="用户ID" width="120" />
            <el-table-column prop="targetName" label="院系" min-width="150" show-overflow-tooltip />
            <el-table-column prop="overdueCount" label="逾期次数" width="100" align="center" sortable />
            <el-table-column prop="totalBorrowCount" label="总借阅" width="100" align="center" sortable />
            <el-table-column prop="overdueRate" label="逾期率" width="120" align="center" sortable>
              <template #default="{ row }">
                <span :style="{ color: getProgressColor(row.overdueRate), fontWeight: 'bold' }">
                  {{ (row.overdueRate * 100).toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="avgOverdueDays" label="平均逾期天数" width="120" align="center" sortable>
              <template #default="{ row }">
                {{ row.avgOverdueDays.toFixed(1) }} 天
              </template>
            </el-table-column>
            <el-table-column prop="currentOverdueCount" label="当前逾期" width="100" align="center" sortable>
              <template #default="{ row }">
                <el-tag v-if="row.currentOverdueCount > 0" type="danger">
                  {{ row.currentOverdueCount }}
                </el-tag>
                <span v-else>0</span>
              </template>
            </el-table-column>
            <el-table-column prop="riskLevel" label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)" size="large">
                  {{ row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页器 -->
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredUserOverdueData.length"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
          />
        </el-tab-pane>
        
        <!-- Tab 3: 院系逾期 -->
        <el-tab-pane label="院系逾期" name="dept">
          <el-table 
            :data="pagedDeptOverdueData" 
            v-loading="loading"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="targetName" label="院系" min-width="200" />
            <el-table-column prop="overdueCount" label="逾期次数" width="120" align="center" sortable />
            <el-table-column prop="totalBorrowCount" label="总借阅" width="120" align="center" sortable />
            <el-table-column prop="overdueRate" label="逾期率" width="150" align="center" sortable>
              <template #default="{ row }">
                {{ (row.overdueRate * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="avgOverdueDays" label="平均逾期天数" width="140" align="center" sortable>
              <template #default="{ row }">
                {{ row.avgOverdueDays.toFixed(1) }} 天
              </template>
            </el-table-column>
            <el-table-column prop="currentOverdueCount" label="当前逾期" width="120" align="center" sortable />
            <el-table-column prop="riskLevel" label="风险等级" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)">
                  {{ row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页器 -->
          <el-pagination
            v-model:current-page="deptCurrentPage"
            v-model:page-size="deptPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="deptOverdueData.length"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { getOverdueAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const activeTab = ref('overview')

const riskLevelChartRef = ref(null)
const overdueRateChartRef = ref(null)
const overdueUsersChartRef = ref(null)
const overdueBooksChartRef = ref(null)

let riskLevelChart = null
let overdueRateChart = null
let overdueUsersChart = null
let overdueBooksChart = null

const userOverdueData = ref([])
const deptOverdueData = ref([])
const bookOverdueData = ref([])

// 筛选条件
const riskFilter = ref('')
const userSearchText = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const deptCurrentPage = ref(1)
const deptPageSize = ref(20)

// 统计指标
const totalOverdue = computed(() => {
  return userOverdueData.value.reduce((sum, item) => sum + item.overdueCount, 0)
})

const currentOverdue = computed(() => {
  return userOverdueData.value.reduce((sum, item) => sum + item.currentOverdueCount, 0)
})

const highRiskUsers = computed(() => {
  return userOverdueData.value.filter(item => item.riskLevel === '高').length
})

const avgOverdueDays = computed(() => {
  if (userOverdueData.value.length === 0) return 0
  const sum = userOverdueData.value.reduce((acc, item) => acc + item.avgOverdueDays, 0)
  return sum / userOverdueData.value.length
})

// 过滤后的用户数据（不分页）
const filteredUserOverdueData = computed(() => {
  let data = userOverdueData.value
  
  if (riskFilter.value) {
    data = data.filter(item => item.riskLevel === riskFilter.value)
  }
  
  if (userSearchText.value) {
    const searchText = userSearchText.value.toLowerCase()
    data = data.filter(item => 
      String(item.targetId || '').toLowerCase().includes(searchText)
    )
  }
  
  return data
})

// 分页后的用户数据
const pagedUserOverdueData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUserOverdueData.value.slice(start, end)
})

// 分页后的院系数据
const pagedDeptOverdueData = computed(() => {
  const start = (deptCurrentPage.value - 1) * deptPageSize.value
  const end = start + deptPageSize.value
  return deptOverdueData.value.slice(start, end)
})

const loadData = async () => {
  try {
    loading.value = true
    console.log('🔄 加载逾期分析数据...')
    
    // 限制返回数量，提升性能
    const res = await getOverdueAnalysis({ limit: 500 })
    const data = res.data || []
    
    console.log('📥 收到数据:', data.length, '条')
    
    // 分类数据
    userOverdueData.value = data.filter(item => item.analysisType === '用户')
    deptOverdueData.value = data.filter(item => item.analysisType === '院系')
    bookOverdueData.value = data.filter(item => item.analysisType === '图书')
    
    console.log('✅ 分类完成:', {
      用户逾期: userOverdueData.value.length,
      院系逾期: deptOverdueData.value.length,
      图书逾期: bookOverdueData.value.length
    })
    
    // 初始化图表
    await nextTick()
    if (activeTab.value === 'overview') {
      initOverviewCharts()
    }
    
    console.log('✅ 逾期数据加载成功')
  } catch (error) {
    console.error('❌ 加载逾期数据失败：', error)
    ElMessage.error('加载逾期数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const initOverviewCharts = () => {
  initRiskLevelChart()
  initOverdueRateChart()
  initOverdueUsersChart()
  initOverdueBooksChart()
}

const initRiskLevelChart = () => {
  if (!riskLevelChartRef.value) return
  
  if (!riskLevelChart) {
    riskLevelChart = echarts.init(riskLevelChartRef.value)
  }
  
  // 统计各风险等级的数量
  const riskStats = {
    '高': 0,
    '中': 0,
    '低': 0
  }
  
  userOverdueData.value.forEach(item => {
    if (riskStats[item.riskLevel] !== undefined) {
      riskStats[item.riskLevel]++
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '风险等级',
      type: 'pie',
      radius: '60%',
      center: ['60%', '50%'],
      data: [
        { value: riskStats['高'], name: '高风险', itemStyle: { color: '#f56c6c' } },
        { value: riskStats['中'], name: '中风险', itemStyle: { color: '#e6a23c' } },
        { value: riskStats['低'], name: '低风险', itemStyle: { color: '#67c23a' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  riskLevelChart.setOption(option)
}

const initOverdueRateChart = () => {
  if (!overdueRateChartRef.value || deptOverdueData.value.length === 0) return
  
  if (!overdueRateChart) {
    overdueRateChart = echarts.init(overdueRateChartRef.value)
  }
  
  // 取逾期率TOP10院系
  const top10 = deptOverdueData.value
    .sort((a, b) => b.overdueRate - a.overdueRate)
    .slice(0, 10)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>逾期率: ${(p.value * 100).toFixed(2)}%`
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
      name: '逾期率(%)',
      axisLabel: {
        formatter: (value) => (value * 100).toFixed(0) + '%'
      }
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => item.targetName)
    },
    series: [{
      name: '逾期率',
      type: 'bar',
      data: top10.map(item => item.overdueRate),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#ffa726' },
          { offset: 1, color: '#f56c6c' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        formatter: (params) => (params.value * 100).toFixed(1) + '%'
      }
    }]
  }
  
  overdueRateChart.setOption(option)
}

const initOverdueUsersChart = () => {
  if (!overdueUsersChartRef.value || userOverdueData.value.length === 0) return
  
  if (!overdueUsersChart) {
    overdueUsersChart = echarts.init(overdueUsersChartRef.value)
  }
  
  const top10 = userOverdueData.value
    .sort((a, b) => (b.overdueCount || 0) - (a.overdueCount || 0))
    .slice(0, 10)
    .reverse()
  
  const labels = top10.map(item => {
    const name = item.targetName || item.targetId || '未知'
    return name.length > 15 ? name.substring(0, 15) + '...' : name
  })
  const counts = top10.map(item => item.overdueCount || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = top10[params[0].dataIndex]
        return `${item.targetName || item.targetId}<br/>逾期次数: ${params[0].value}<br/>逾期率: ${((item.overdueRate || 0) * 100).toFixed(2)}%`
      }
    },
    grid: {
      left: '20%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        interval: 0,
        fontSize: 11
      }
    },
    series: [{
      name: '逾期次数',
      type: 'bar',
      data: counts,
      itemStyle: { color: '#f56c6c' },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  overdueUsersChart.setOption(option)
}

const initOverdueBooksChart = () => {
  if (!overdueBooksChartRef.value || bookOverdueData.value.length === 0) return
  
  if (!overdueBooksChart) {
    overdueBooksChart = echarts.init(overdueBooksChartRef.value)
  }
  
  const top10 = bookOverdueData.value
    .sort((a, b) => (b.overdueCount || 0) - (a.overdueCount || 0))
    .slice(0, 10)
    .reverse()
  
  const labels = top10.map(item => {
    const name = item.targetName || item.targetId || '未知'
    // 根据卡片宽度优化截断长度：12个字符适合大多数场景
    return name.length > 12 ? name.substring(0, 12) + '...' : name
  })
  const counts = top10.map(item => item.overdueCount || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      position: function (point, params, dom, rect, size) {
        // 智能定位：横向条形图始终显示在右侧，避免被左侧Y轴遮挡
        return [point[0] + 20, point[1] - size.contentSize[1] / 2]
      },
      formatter: (params) => {
        const item = top10[params[0].dataIndex]
        return `${item.targetName || item.targetId}<br/>逾期次数: ${params[0].value}<br/>逾期率: ${((item.overdueRate || 0) * 100).toFixed(2)}%`
      }
    },
    grid: {
      left: '25%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        interval: 0,
        fontSize: 10,
        overflow: 'truncate',
        width: 130
      }
    },
    series: [{
      name: '逾期次数',
      type: 'bar',
      data: counts,
      itemStyle: { color: '#e6a23c' },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  overdueBooksChart.setOption(option)
}

const handleTabChange = (tabName) => {
  nextTick(() => {
    if (tabName === 'overview') {
      initOverviewCharts()
    }
  })
}

const getRiskTagType = (level) => {
  const map = {
    '高': 'danger',
    '中': 'warning',
    '低': 'success'
  }
  return map[level] || 'info'
}

const getProgressColor = (rate) => {
  if (rate > 0.3) return '#f56c6c'
  if (rate > 0.1) return '#e6a23c'
  return '#67c23a'
}

// 监听筛选条件变化，重置到第一页
watch([riskFilter, userSearchText], () => {
  currentPage.value = 1
})

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    riskLevelChart?.resize()
    overdueRateChart?.resize()
    overdueUsersChart?.resize()
    overdueBooksChart?.resize()
  })
})

onUnmounted(() => {
  riskLevelChart?.dispose()
  overdueRateChart?.dispose()
  overdueUsersChart?.dispose()
  overdueBooksChart?.dispose()
})
</script>

<style scoped lang="scss">
.overdue-management-container {
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
  
  .stat-card {
    margin-bottom: 20px;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
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
  
  :deep(.el-card) {
    margin-bottom: 20px;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .el-card__header {
      background: linear-gradient(135deg, rgba(245, 108, 108, 0.05) 0%, rgba(230, 162, 60, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
  }
  
  :deep(.el-tabs) {
    .el-tabs__item {
      font-weight: 500;
      transition: all 0.3s;
      
      &.is-active {
        font-weight: 700;
        color: #f56c6c;
      }
    }
    
    .el-tabs__active-bar {
      background: linear-gradient(135deg, #f56c6c 0%, #e6a23c 100%);
      height: 3px;
    }
  }
}
</style>

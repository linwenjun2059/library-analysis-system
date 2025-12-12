<template>
  <div class="overdue-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><WarningFilled /></el-icon> 逾期管理</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <!-- 逾期概览 -->
        <el-tab-pane label="逾期概览" name="overview">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="8" v-for="stat in overdueStats" :key="stat.riskLevel">
              <el-card shadow="hover" class="stat-card">
                <el-statistic 
                  :title="`${stat.riskLevel}风险用户`" 
                  :value="stat.count"
                >
                  <template #prefix>
                    <el-icon :color="getRiskColor(stat.riskLevel)"><Warning /></el-icon>
                  </template>
                </el-statistic>
              </el-card>
            </el-col>
          </el-row>
          
          <div ref="pieChartRef" style="width: 100%; height: 400px; margin-top: 20px;"></div>
        </el-tab-pane>
        
        <!-- 逾期用户 -->
        <el-tab-pane label="逾期用户" name="users">
          <el-table :data="overdueUsers" v-loading="loading" stripe>
            <el-table-column prop="targetId" label="用户ID" min-width="150" show-overflow-tooltip />
            <el-table-column prop="targetName" label="院系" min-width="120" show-overflow-tooltip />
            <el-table-column prop="overdueCount" label="逾期次数" width="100" align="center" sortable />
            <el-table-column prop="totalBorrowCount" label="总借阅" width="100" align="center" />
            <el-table-column prop="overdueRate" label="逾期率" width="100" align="center" sortable>
              <template #default="{ row }">
                {{ (row.overdueRate * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="avgOverdueDays" label="平均逾期天数" width="120" align="center" sortable>
              <template #default="{ row }">
                {{ row.avgOverdueDays ? row.avgOverdueDays.toFixed(1) : '-' }} 天
              </template>
            </el-table-column>
            <el-table-column prop="currentOverdueCount" label="当前逾期" width="100" align="center" sortable />
            <el-table-column prop="riskLevel" label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)">
                  {{ row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="userPagination.current"
            v-model:page-size="userPagination.size"
            :total="userPagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: flex-end;"
          />
        </el-tab-pane>
        
        <!-- 逾期图书 -->
        <el-tab-pane label="逾期图书" name="books">
          <el-empty 
            v-if="overdueBooks.length === 0 && !loading"
            description="暂无图书维度的逾期分析数据"
            :image-size="120"
          />
          <el-table 
            v-else
            :data="overdueBooks" 
            v-loading="loading" 
            stripe
          >
            <el-table-column prop="targetName" label="图书名称" min-width="200" show-overflow-tooltip />
            <el-table-column prop="overdueCount" label="逾期次数" width="120" align="center" sortable />
            <el-table-column prop="totalBorrowCount" label="总借阅次数" width="120" align="center" />
            <el-table-column prop="overdueRate" label="逾期率" width="120" align="center">
              <template #default="{ row }">
                {{ (row.overdueRate * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="riskLevel" label="风险等级" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)">
                  {{ row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <!-- 院系逾期率 -->
        <el-tab-pane label="院系逾期率" name="dept">
          <el-table :data="overdueDepts" v-loading="loading" stripe style="margin-bottom: 20px;">
            <el-table-column prop="targetName" label="院系" min-width="150" show-overflow-tooltip />
            <el-table-column prop="overdueCount" label="逾期次数" width="100" align="center" sortable />
            <el-table-column prop="totalBorrowCount" label="总借阅" width="100" align="center" />
            <el-table-column prop="overdueRate" label="逾期率" width="100" align="center" sortable>
              <template #default="{ row }">
                {{ (row.overdueRate * 100).toFixed(2) }}%
              </template>
            </el-table-column>
            <el-table-column prop="avgOverdueDays" label="平均逾期天数" width="120" align="center" sortable>
              <template #default="{ row }">
                {{ row.avgOverdueDays ? row.avgOverdueDays.toFixed(1) : '-' }} 天
              </template>
            </el-table-column>
            <el-table-column prop="currentOverdueCount" label="当前逾期" width="100" align="center" sortable />
            <el-table-column prop="riskLevel" label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)">
                  {{ row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-model:current-page="deptPagination.current"
            v-model:page-size="deptPagination.size"
            :total="deptPagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-bottom: 20px; justify-content: flex-end;"
          />
          
          <el-divider />
          
          <div ref="barChartRef" style="width: 100%; height: 500px;"></div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getOverdueAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const activeTab = ref('overview')
const allOverdueUsers = ref([])  // 全部逾期用户数据
const allOverdueDepts = ref([])  // 全部院系数据
const overdueBooks = ref([])
const overdueStats = ref([])

// 分页状态
const userPagination = ref({
  current: 1,
  size: 10,
  total: 0
})

const deptPagination = ref({
  current: 1,
  size: 10,
  total: 0
})

// 分页后的数据
const overdueUsers = computed(() => {
  const start = (userPagination.value.current - 1) * userPagination.value.size
  const end = start + userPagination.value.size
  return allOverdueUsers.value.slice(start, end)
})

const overdueDepts = computed(() => {
  const start = (deptPagination.value.current - 1) * deptPagination.value.size
  const end = start + deptPagination.value.size
  return allOverdueDepts.value.slice(start, end)
})

const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieChart = null
let barChart = null

const getRiskColor = (level) => {
  const colorMap = { '高': '#f56c6c', '中': '#e6a23c', '低': '#67c23a' }
  return colorMap[level] || '#909399'
}

const getRiskTagType = (level) => {
  const typeMap = { '高': 'danger', '中': 'warning', '低': 'success' }
  return typeMap[level] || 'info'
}

const loadData = async () => {
  try {
    loading.value = true
    
    // 加载所有逾期分析数据
    const res = await getOverdueAnalysis({})
    const data = res.data || []
    
    // 按分析类型分类（Spark写入的是中文：'用户'、'院系'）
    allOverdueUsers.value = data.filter(item => item.analysisType === '用户')
    allOverdueDepts.value = data.filter(item => item.analysisType === '院系')
    
    // 更新分页总数
    userPagination.value.total = allOverdueUsers.value.length
    deptPagination.value.total = allOverdueDepts.value.length
    
    // 注意：Spark没有生成图书维度的逾期分析数据，所以图书列表为空
    overdueBooks.value = []
    
    // 统计风险等级
    const riskStats = {}
    data.forEach(item => {
      const level = item.riskLevel || '未知'
      riskStats[level] = (riskStats[level] || 0) + 1
    })
    
    overdueStats.value = Object.entries(riskStats).map(([riskLevel, count]) => ({
      riskLevel,
      count
    })).sort((a, b) => {
      const order = { '高': 1, '中': 2, '低': 3 }
      return (order[a.riskLevel] || 999) - (order[b.riskLevel] || 999)
    })
    
    console.log('✅ 逾期数据加载成功：', {
      用户: allOverdueUsers.value.length,
      院系: allOverdueDepts.value.length,
      图书: '暂无数据（Spark未生成）'
    })
  } catch (error) {
    console.error('❌ 加载逾期数据失败：', error)
    ElMessage.error('加载逾期数据失败')
  } finally {
    loading.value = false
  }
}

const initPieChart = () => {
  if (!pieChartRef.value || overdueStats.value.length === 0) return
  
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  
  const option = {
    title: { text: '逾期风险等级分布', left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      name: '用户数',
      type: 'pie',
      radius: '60%',
      data: overdueStats.value.map(item => ({
        value: item.count,
        name: `${item.riskLevel}风险`
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  pieChart.setOption(option)
}

const initBarChart = () => {
  if (!barChartRef.value || allOverdueDepts.value.length === 0) return
  
  if (!barChart) {
    barChart = echarts.init(barChartRef.value)
  }
  
  // 使用全部院系数据绘制图表
  const sortedDepts = [...allOverdueDepts.value]
    .sort((a, b) => b.overdueRate - a.overdueRate)
    .slice(0, 20)  // 只显示TOP 20
  
  const option = {
    title: { text: '院系逾期率对比（TOP 20）', left: 'center' },
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' },
      formatter: '{b}<br/>逾期率: {c}%'
    },
    xAxis: {
      type: 'category',
      data: sortedDepts.map(item => item.targetName),
      axisLabel: { rotate: 45, interval: 0 }
    },
    yAxis: {
      type: 'value',
      name: '逾期率 (%)',
      axisLabel: { formatter: '{value}%' }
    },
    series: [{
      name: '逾期率',
      type: 'bar',
      data: sortedDepts.map(item => (item.overdueRate * 100).toFixed(2)),
      itemStyle: { color: '#e6a23c' }
    }]
  }
  
  barChart.setOption(option)
}

watch(activeTab, (newVal) => {
  if (newVal === 'overview') {
    setTimeout(() => initPieChart(), 100)
  } else if (newVal === 'dept') {
    setTimeout(() => initBarChart(), 100)
  }
})

onMounted(() => {
  loadData().then(() => {
    initPieChart()
  })
  
  window.addEventListener('resize', () => {
    pieChart?.resize()
    barChart?.resize()
  })
})

onUnmounted(() => {
  pieChart?.dispose()
  barChart?.dispose()
})
</script>

<style scoped lang="scss">
.overdue-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .stat-card {
    margin-bottom: 20px;
  }
}
</style>

<template>
  <div class="user-clustering-container">
    <!-- 聚类概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总用户数" :value="clusterStats.totalUsers || 0">
            <template #prefix>
              <el-icon color="#409eff"><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="聚类群体数" :value="clusterStats.clusterCount || 0">
            <template #prefix>
              <el-icon color="#67c23a"><DataAnalysis /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="最大群体占比" :value="maxClusterPercentage" :precision="1" suffix="%">
            <template #prefix>
              <el-icon color="#e6a23c"><PieChart /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 聚类分布图表 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>用户群体分布</span>
          </template>
          <div ref="pieChartRef" style="width: 100%; height: 350px;"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover">
          <template #header>
            <span>群体特征对比</span>
          </template>
          <div ref="radarChartRef" style="width: 100%; height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 聚类详情卡片 -->
    <el-card shadow="hover" class="cluster-detail-card">
      <template #header>
        <span>聚类群体详情</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :xs="24" :md="8" :lg="6" v-for="cluster in clusterSummary" :key="cluster.cluster">
          <el-card 
            shadow="hover" 
            class="cluster-card"
            :class="{ active: selectedCluster === cluster.cluster }"
            @click="selectCluster(cluster.cluster)"
          >
            <div class="cluster-header">
              <el-tag :type="getClusterTagType(cluster.cluster)" size="large">
                {{ cluster.clusterName }}
              </el-tag>
              <span class="user-count">{{ cluster.userCount.toLocaleString() }}人</span>
            </div>
            <div class="cluster-characteristics">
              <el-tag 
                v-for="(char, idx) in cluster.clusterCharacteristics.split('、')" 
                :key="idx"
                size="small"
                type="info"
                class="char-tag"
              >
                {{ char }}
              </el-tag>
            </div>
            <el-divider />
            <div class="cluster-metrics">
              <div class="metric">
                <span class="label">平均借阅</span>
                <span class="value">{{ cluster.avgBorrowCount.toFixed(1) }}本</span>
              </div>
              <div class="metric">
                <span class="label">活跃天数</span>
                <span class="value">{{ cluster.avgActiveDays.toFixed(1) }}天</span>
              </div>
              <div class="metric">
                <span class="label">阅读广度</span>
                <span class="value">{{ cluster.avgReadingBreadth.toFixed(1) }}类</span>
              </div>
              <div class="metric">
                <span class="label">逾期率</span>
                <span class="value" :class="{ warning: cluster.avgOverdueRate > 0.1 }">
                  {{ (cluster.avgOverdueRate * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 选中聚类的用户列表 -->
    <el-card shadow="hover" class="users-card" v-if="selectedCluster !== null">
      <template #header>
        <div class="card-header">
          <span>{{ selectedClusterName }} - 用户列表</span>
          <el-input
            v-model="deptFilter"
            placeholder="按院系筛选"
            style="width: 200px;"
            clearable
            @clear="loadClusterUsers"
            @keyup.enter="loadClusterUsers"
          >
            <template #append>
              <el-button @click="loadClusterUsers">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="clusterUsers" v-loading="usersLoading" stripe>
        <el-table-column prop="userid" label="用户ID" width="120" />
        <el-table-column prop="dept" label="院系" min-width="150" show-overflow-tooltip />
        <el-table-column prop="userType" label="用户类型" width="100" />
        <el-table-column prop="occupation" label="专业" min-width="150" show-overflow-tooltip />
        <el-table-column prop="borrowCount" label="借阅量" width="100" align="center" sortable />
        <el-table-column prop="activeDays" label="活跃天数" width="100" align="center" sortable />
        <el-table-column label="逾期率" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.overdueRate > 0.1 ? 'danger' : 'success'" size="small">
              {{ (row.overdueRate * 100).toFixed(1) }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="readingBreadth" label="阅读广度" width="100" align="center" />
      </el-table>

      <div class="pagination-area">
        <el-pagination
          v-model:current-page="userCurrentPage"
          v-model:page-size="userPageSize"
          :page-sizes="[10, 20, 50]"
          :total="userTotal"
          layout="total, sizes, prev, pager, next"
          @size-change="loadClusterUsers"
          @current-change="loadClusterUsers"
        />
      </div>
    </el-card>

    <!-- 院系聚类分布 -->
    <el-card shadow="hover" class="dept-card">
      <template #header>
        <span>院系聚类分布</span>
      </template>
      <div ref="deptChartRef" style="width: 100%; height: 400px;"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { User, DataAnalysis, PieChart, Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getClusterSummary, getClusterStats, getClusterUsers, getDeptClusterDistribution } from '@/api/advanced'

const clusterStats = ref({})
const clusterSummary = ref([])
const selectedCluster = ref(null)
const clusterUsers = ref([])
const usersLoading = ref(false)
const deptFilter = ref('')
const userCurrentPage = ref(1)
const userPageSize = ref(10)
const userTotal = ref(0)
const deptDistribution = ref([])

const pieChartRef = ref(null)
const radarChartRef = ref(null)
const deptChartRef = ref(null)
let pieChart = null
let radarChart = null
let deptChart = null

const maxClusterPercentage = computed(() => {
  if (!clusterStats.value.distribution || clusterStats.value.distribution.length === 0) return 0
  return Math.max(...clusterStats.value.distribution.map(d => d.percentage))
})

const selectedClusterName = computed(() => {
  const cluster = clusterSummary.value.find(c => c.cluster === selectedCluster.value)
  return cluster ? cluster.clusterName : ''
})

const getClusterTagType = (clusterId) => {
  const types = ['primary', 'success', 'warning', 'danger', 'info']
  return types[clusterId % types.length]
}

const loadClusterStats = async () => {
  try {
    const res = await getClusterStats()
    if (res.code === 200) {
      clusterStats.value = res.data
      renderPieChart()
    }
  } catch (error) {
    console.error('加载聚类统计失败:', error)
  }
}

const loadClusterSummary = async () => {
  try {
    const res = await getClusterSummary()
    if (res.code === 200) {
      clusterSummary.value = res.data
      renderRadarChart()
    }
  } catch (error) {
    console.error('加载聚类摘要失败:', error)
  }
}

const selectCluster = (clusterId) => {
  selectedCluster.value = clusterId
  userCurrentPage.value = 1
  loadClusterUsers()
}

const loadClusterUsers = async () => {
  if (selectedCluster.value === null) return
  
  usersLoading.value = true
  try {
    const res = await getClusterUsers(selectedCluster.value, {
      current: userCurrentPage.value,
      size: userPageSize.value,
      dept: deptFilter.value
    })
    if (res.code === 200) {
      clusterUsers.value = res.data.records
      userTotal.value = res.data.total
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    usersLoading.value = false
  }
}

const loadDeptDistribution = async () => {
  try {
    const res = await getDeptClusterDistribution()
    if (res.code === 200) {
      deptDistribution.value = res.data.slice(0, 10) // TOP10院系
      renderDeptChart()
    }
  } catch (error) {
    console.error('加载院系分布失败:', error)
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value || !clusterStats.value.distribution) return
  
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}\n{d}%'
      },
      data: clusterStats.value.distribution.map((d, i) => ({
        value: d.count,
        name: d.name,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  }
  
  pieChart.setOption(option)
}

const renderRadarChart = () => {
  if (!radarChartRef.value || clusterSummary.value.length === 0) return
  
  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }
  
  // 计算各指标的最大值用于归一化
  const maxBorrow = Math.max(...clusterSummary.value.map(c => c.avgBorrowCount))
  const maxActive = Math.max(...clusterSummary.value.map(c => c.avgActiveDays))
  const maxBreadth = Math.max(...clusterSummary.value.map(c => c.avgReadingBreadth))
  const maxOverdue = Math.max(...clusterSummary.value.map(c => c.avgOverdueRate))
  const maxBorrowDays = Math.max(...clusterSummary.value.map(c => c.avgBorrowDays))
  
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
  
  const option = {
    tooltip: {},
    legend: {
      bottom: '5%',
      data: clusterSummary.value.map(c => c.clusterName)
    },
    radar: {
      indicator: [
        { name: '借阅量', max: maxBorrow * 1.2 },
        { name: '活跃天数', max: maxActive * 1.2 },
        { name: '阅读广度', max: maxBreadth * 1.2 },
        { name: '借阅天数', max: maxBorrowDays * 1.2 },
        { name: '逾期率', max: maxOverdue * 1.2 || 0.5 }
      ]
    },
    series: [{
      type: 'radar',
      data: clusterSummary.value.map((c, i) => ({
        value: [
          c.avgBorrowCount,
          c.avgActiveDays,
          c.avgReadingBreadth,
          c.avgBorrowDays,
          c.avgOverdueRate
        ],
        name: c.clusterName,
        lineStyle: { color: colors[i % colors.length] },
        areaStyle: { color: colors[i % colors.length], opacity: 0.2 }
      }))
    }]
  }
  
  radarChart.setOption(option)
}

const renderDeptChart = () => {
  if (!deptChartRef.value || deptDistribution.value.length === 0) return
  
  if (!deptChart) {
    deptChart = echarts.init(deptChartRef.value)
  }
  
  const depts = deptDistribution.value.map(d => d.dept)
  const clusterNames = [...new Set(deptDistribution.value.flatMap(d => Object.keys(d.clusters)))]
  const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
  
  const series = clusterNames.map((name, i) => ({
    name,
    type: 'bar',
    stack: 'total',
    emphasis: { focus: 'series' },
    itemStyle: { color: colors[i % colors.length] },
    data: deptDistribution.value.map(d => d.clusters[name] || 0)
  }))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      bottom: '0%'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: depts,
      axisLabel: {
        rotate: 30,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '用户数'
    },
    series
  }
  
  deptChart.setOption(option)
}

onMounted(async () => {
  await Promise.all([
    loadClusterStats(),
    loadClusterSummary(),
    loadDeptDistribution()
  ])
  
  window.addEventListener('resize', () => {
    pieChart?.resize()
    radarChart?.resize()
    deptChart?.resize()
  })
})
</script>

<style scoped>
.user-clustering-container {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  margin-bottom: 20px;
}

.chart-row {
  margin-bottom: 20px;
}

.cluster-detail-card {
  margin-bottom: 20px;
}

.cluster-card {
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.cluster-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.cluster-card.active {
  border: 2px solid #409eff;
}

.cluster-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.user-count {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.cluster-characteristics {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.char-tag {
  margin: 2px;
}

.cluster-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.metric {
  display: flex;
  justify-content: space-between;
}

.metric .label {
  color: #909399;
  font-size: 12px;
}

.metric .value {
  font-weight: 500;
  color: #303133;
}

.metric .value.warning {
  color: #f56c6c;
}

.users-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination-area {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dept-card {
  margin-bottom: 20px;
}
</style>

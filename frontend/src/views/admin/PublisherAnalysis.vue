<template>
  <div class="publish-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><OfficeBuilding /></el-icon>出版分析</span>
          <el-button type="primary" size="small" @click="loadAllData" :loading="loading">
            <el-icon><Refresh /></el-icon>刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="mainTab" @tab-change="handleTabChange">
        <!-- Tab 1: 出版社分析 -->
        <el-tab-pane name="publisher">
          <template #label>
            <span><el-icon><OfficeBuilding /></el-icon>出版社分析</span>
          </template>
          <el-tabs v-model="publisherViewMode">
            <el-tab-pane name="chart">
              <template #label>
                <span><el-icon><DataAnalysis /></el-icon>图表视图</span>
              </template>
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-card shadow="hover">
                    <template #header>
                      <span>出版社借阅排行榜（TOP 20）</span>
                    </template>
                    <div ref="publisherRankingChartRef" style="width: 100%; height: 500px;"></div>
                  </el-card>
                </el-col>
                
                <el-col :xs="24" :lg="12">
                  <el-card shadow="hover">
                    <template #header>
                      <span>出版社图书数量分布</span>
                    </template>
                    <div ref="publisherBookCountChartRef" style="width: 100%; height: 400px;"></div>
                  </el-card>
                </el-col>
                
                <el-col :xs="24" :lg="12">
                  <el-card shadow="hover">
                    <template #header>
                      <span>出版社平均借阅次数</span>
                    </template>
                    <div ref="publisherAvgLendChartRef" style="width: 100%; height: 400px;"></div>
                  </el-card>
                </el-col>
              </el-row>
            </el-tab-pane>
            
            <el-tab-pane name="table">
              <template #label>
                <span><el-icon><List /></el-icon> 表格视图</span>
              </template>
              <el-table :data="publisherPageData" v-loading="loading" stripe style="width: 100%">
                <el-table-column type="index" label="排名" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.rankNo <= 3 ? 'danger' : row.rankNo <= 10 ? 'warning' : 'info'" effect="dark">
                      {{ row.rankNo }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="publisher" label="出版社" min-width="200" show-overflow-tooltip />
                <el-table-column prop="bookCount" label="图书数量" min-width="120" align="center" sortable />
                <el-table-column prop="totalLendCount" label="总借阅次数" min-width="140" align="center" sortable />
                <el-table-column prop="totalUserCount" label="总借阅用户数" min-width="140" align="center" sortable />
                <el-table-column prop="avgLendCount" label="平均借阅次数" min-width="140" align="center" :formatter="formatNumber" sortable />
              </el-table>
              <el-pagination
                v-model:current-page="publisherPage"
                v-model:page-size="publisherPageSize"
                :page-sizes="[10, 20, 50]"
                :total="publisherList.length"
                layout="total, sizes, prev, pager, next, jumper"
                style="margin-top: 16px; justify-content: flex-end;"
              />
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
        
        <!-- Tab 2: 出版年份分析 -->
        <el-tab-pane name="year">
          <template #label>
            <span><el-icon><Calendar /></el-icon> 出版年份分析</span>
          </template>
          <el-tabs v-model="yearViewMode">
            <el-tab-pane name="chart">
              <template #label>
                <span><el-icon><DataAnalysis /></el-icon> 图表视图</span>
              </template>
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-card shadow="hover">
                    <template #header>
                      <span>出版年份分布趋势</span>
                    </template>
                    <div ref="yearTrendChartRef" style="width: 100%; height: 500px;"></div>
                  </el-card>
                </el-col>
                
                <el-col :xs="24" :lg="12">
                  <el-card shadow="hover">
                    <template #header>
                      <span>各年份图书数量</span>
                    </template>
                    <div ref="yearBookCountChartRef" style="width: 100%; height: 400px;"></div>
                  </el-card>
                </el-col>
                
                <el-col :xs="24" :lg="12">
                  <el-card shadow="hover">
                    <template #header>
                      <span>各年份借阅次数</span>
                    </template>
                    <div ref="yearLendCountChartRef" style="width: 100%; height: 400px;"></div>
                  </el-card>
                </el-col>
              </el-row>
            </el-tab-pane>
            
            <el-tab-pane name="table">
              <template #label>
                <span><el-icon><List /></el-icon> 表格视图</span>
              </template>
              <el-table :data="yearPageData" v-loading="loading" stripe style="width: 100%">
                <el-table-column prop="pubYear" label="出版年份" min-width="120" align="center" sortable />
                <el-table-column prop="bookCount" label="图书数量" min-width="120" align="center" sortable />
                <el-table-column prop="totalLendCount" label="总借阅次数" min-width="140" align="center" sortable />
                <el-table-column prop="avgLendCount" label="平均借阅次数" min-width="140" align="center" :formatter="formatNumber" sortable />
              </el-table>
              <el-pagination
                v-model:current-page="yearPage"
                v-model:page-size="yearPageSize"
                :page-sizes="[10, 20, 50]"
                :total="yearList.length"
                layout="total, sizes, prev, pager, next, jumper"
                style="margin-top: 16px; justify-content: flex-end;"
              />
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getPublisherAnalysis, getPublishYearAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { OfficeBuilding, Refresh, DataAnalysis, List, Calendar } from '@element-plus/icons-vue'

const loading = ref(false)
const mainTab = ref('publisher')
const publisherViewMode = ref('chart')
const yearViewMode = ref('chart')
const publisherList = ref([])
const yearList = ref([])

// 分页参数
const publisherPage = ref(1)
const publisherPageSize = ref(10)
const yearPage = ref(1)
const yearPageSize = ref(10)

// 分页数据计算
const publisherPageData = computed(() => {
  const start = (publisherPage.value - 1) * publisherPageSize.value
  const end = start + publisherPageSize.value
  return publisherList.value.slice(start, end)
})

const yearPageData = computed(() => {
  const start = (yearPage.value - 1) * yearPageSize.value
  const end = start + yearPageSize.value
  return yearList.value.slice(start, end)
})

// 懒加载状态：记录每个 Tab 是否已加载数据
const publisherLoaded = ref(false)
const yearLoaded = ref(false)

// 出版社图表refs
const publisherRankingChartRef = ref(null)
const publisherBookCountChartRef = ref(null)
const publisherAvgLendChartRef = ref(null)
let publisherRankingChart = null
let publisherBookCountChart = null
let publisherAvgLendChart = null

// 出版年份图表refs
const yearTrendChartRef = ref(null)
const yearBookCountChartRef = ref(null)
const yearLendCountChartRef = ref(null)
let yearTrendChart = null
let yearBookCountChart = null
let yearLendCountChart = null

const formatNumber = (row, column, cellValue) => {
  return cellValue ? cellValue.toFixed(2) : '0.00'
}

// 刷新当前 Tab 数据
const loadAllData = async () => {
  if (mainTab.value === 'publisher') {
    publisherLoaded.value = false
    await loadPublisherData()
  } else {
    yearLoaded.value = false
    await loadYearData()
  }
}

const loadPublisherData = async () => {
  if (publisherLoaded.value && publisherList.value.length > 0) {
    // 已加载过，直接渲染图表
    nextTick(() => initPublisherCharts())
    return
  }
  
  loading.value = true
  try {
    const result = await getPublisherAnalysis()
    publisherList.value = result.data || []
    publisherLoaded.value = true
    
    nextTick(() => initPublisherCharts())
  } catch (error) {
    ElMessage.error('加载出版社数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadYearData = async () => {
  if (yearLoaded.value && yearList.value.length > 0) {
    // 已加载过，直接渲染图表
    nextTick(() => initYearCharts())
    return
  }
  
  loading.value = true
  try {
    const result = await getPublishYearAnalysis()
    yearList.value = result.data || []
    yearLoaded.value = true
    
    nextTick(() => initYearCharts())
  } catch (error) {
    ElMessage.error('加载出版年份数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleTabChange = (tab) => {
  nextTick(() => {
    setTimeout(() => {
      if (tab === 'publisher') {
        // 懒加载：切换到出版社 Tab 时才加载数据
        loadPublisherData()
      } else if (tab === 'year') {
        // 懒加载：切换到出版年份 Tab 时才加载数据
        loadYearData()
      }
    }, 100)
  })
}

const initPublisherCharts = () => {
  if (publisherList.value.length === 0) return
  
  const top20 = publisherList.value.slice(0, 20)
  const names = top20.map(item => item.publisher)
  
  // 排行榜柱状图
  if (publisherRankingChartRef.value) {
    if (!publisherRankingChart) {
      publisherRankingChart = echarts.init(publisherRankingChartRef.value)
    }
    publisherRankingChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'category', data: names, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', name: '总借阅次数' },
      series: [{
        data: top20.map(item => item.totalLendCount),
        type: 'bar',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }]
    })
  }
  
  // 图书数量分布饼图
  if (publisherBookCountChartRef.value) {
    if (!publisherBookCountChart) {
      publisherBookCountChart = echarts.init(publisherBookCountChartRef.value)
    }
    publisherBookCountChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        name: '图书数量',
        type: 'pie',
        radius: ['40%', '70%'],
        data: top20.map(item => ({ value: item.bookCount, name: item.publisher })),
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
      }]
    })
  }
  
  // 平均借阅次数柱状图
  if (publisherAvgLendChartRef.value) {
    if (!publisherAvgLendChart) {
      publisherAvgLendChart = echarts.init(publisherAvgLendChartRef.value)
    }
    publisherAvgLendChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: names, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', name: '平均借阅次数' },
      series: [{ data: top20.map(item => item.avgLendCount), type: 'bar', itemStyle: { color: '#67c23a' } }]
    })
  }
}

const initYearCharts = () => {
  if (yearList.value.length === 0) return
  
  const sortedYears = [...yearList.value].sort((a, b) => a.pubYear - b.pubYear)
  const years = sortedYears.map(item => item.pubYear.toString())
  
  // 趋势图
  if (yearTrendChartRef.value) {
    if (!yearTrendChart) {
      yearTrendChart = echarts.init(yearTrendChartRef.value)
    }
    yearTrendChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: ['图书数量', '借阅次数'], top: 10 },
      xAxis: { type: 'category', data: years },
      yAxis: [
        { type: 'value', name: '图书数量', position: 'left' },
        { type: 'value', name: '借阅次数', position: 'right' }
      ],
      series: [
        { name: '图书数量', type: 'bar', data: sortedYears.map(item => item.bookCount), itemStyle: { color: '#5470c6' } },
        { name: '借阅次数', type: 'line', yAxisIndex: 1, data: sortedYears.map(item => item.totalLendCount), itemStyle: { color: '#91cc75' } }
      ]
    })
  }
  
  // 图书数量柱状图
  if (yearBookCountChartRef.value) {
    if (!yearBookCountChart) {
      yearBookCountChart = echarts.init(yearBookCountChartRef.value)
    }
    yearBookCountChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: years, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: '图书数量' },
      series: [{ data: sortedYears.map(item => item.bookCount), type: 'bar', itemStyle: { color: '#409eff' } }]
    })
  }
  
  // 借阅次数柱状图
  if (yearLendCountChartRef.value) {
    if (!yearLendCountChart) {
      yearLendCountChart = echarts.init(yearLendCountChartRef.value)
    }
    yearLendCountChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: years, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: '借阅次数' },
      series: [{ data: sortedYears.map(item => item.totalLendCount), type: 'bar', itemStyle: { color: '#67c23a' } }]
    })
  }
}

const handleResize = () => {
  publisherRankingChart?.resize()
  publisherBookCountChart?.resize()
  publisherAvgLendChart?.resize()
  yearTrendChart?.resize()
  yearBookCountChart?.resize()
  yearLendCountChart?.resize()
}

onMounted(() => {
  // 懒加载：只加载当前 Tab 的数据（默认是出版社分析）
  loadPublisherData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  publisherRankingChart?.dispose()
  publisherBookCountChart?.dispose()
  publisherAvgLendChart?.dispose()
  yearTrendChart?.dispose()
  yearBookCountChart?.dispose()
  yearLendCountChart?.dispose()
})
</script>

<style scoped>
.publish-analysis-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-row) {
  .el-col {
    margin-bottom: 20px;
  }
}
</style>


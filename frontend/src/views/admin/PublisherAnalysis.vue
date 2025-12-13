<template>
  <div class="publish-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><OfficeBuilding /></el-icon> 出版分析</span>
          <el-button type="primary" size="small" @click="loadAllData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="mainTab" @tab-change="handleTabChange">
        <!-- Tab 1: 出版社分析 -->
        <el-tab-pane label="🏢 出版社分析" name="publisher">
          <el-tabs v-model="publisherViewMode">
            <el-tab-pane label="📊 图表视图" name="chart">
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
            
            <el-tab-pane label="📋 表格视图" name="table">
              <el-table :data="publisherList" v-loading="loading" stripe style="width: 100%">
                <el-table-column type="index" label="排名" width="80" align="center">
                  <template #default="{ $index }">
                    <el-tag :type="$index < 3 ? 'danger' : $index < 10 ? 'warning' : 'info'" effect="dark">
                      {{ $index + 1 }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="publisher" label="出版社" min-width="200" show-overflow-tooltip />
                <el-table-column prop="bookCount" label="图书数量" min-width="120" align="center" sortable />
                <el-table-column prop="totalLendCount" label="总借阅次数" min-width="140" align="center" sortable />
                <el-table-column prop="totalUserCount" label="总借阅用户数" min-width="140" align="center" sortable />
                <el-table-column prop="avgLendCount" label="平均借阅次数" min-width="140" align="center" :formatter="formatNumber" sortable />
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
        
        <!-- Tab 2: 出版年份分析 -->
        <el-tab-pane label="📅 出版年份分析" name="year">
          <el-tabs v-model="yearViewMode">
            <el-tab-pane label="📊 图表视图" name="chart">
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
            
            <el-tab-pane label="📋 表格视图" name="table">
              <el-table :data="yearList" v-loading="loading" stripe style="width: 100%">
                <el-table-column prop="year" label="出版年份" min-width="120" align="center" sortable />
                <el-table-column prop="bookCount" label="图书数量" min-width="120" align="center" sortable />
                <el-table-column prop="totalLendCount" label="总借阅次数" min-width="140" align="center" sortable />
                <el-table-column label="平均借阅次数" min-width="140" align="center" sortable>
                  <template #default="{ row }">
                    {{ row.bookCount > 0 ? (row.totalLendCount / row.bookCount).toFixed(2) : '0.00' }}
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getPublisherAnalysis, getPublishYearAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { OfficeBuilding, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const mainTab = ref('publisher')
const publisherViewMode = ref('chart')
const yearViewMode = ref('chart')
const publisherList = ref([])
const yearList = ref([])

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

const loadAllData = async () => {
  await Promise.all([loadPublisherData(), loadYearData()])
}

const loadPublisherData = async () => {
  loading.value = true
  try {
    const result = await getPublisherAnalysis()
    publisherList.value = result.data || []
    
    if (mainTab.value === 'publisher') {
      nextTick(() => initPublisherCharts())
    }
  } catch (error) {
    ElMessage.error('加载出版社数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadYearData = async () => {
  try {
    const result = await getPublishYearAnalysis()
    yearList.value = (result.data || []).sort((a, b) => b.year - a.year)
    
    if (mainTab.value === 'year') {
      nextTick(() => initYearCharts())
    }
  } catch (error) {
    console.error('加载出版年份数据失败：', error)
  }
}

const handleTabChange = (tab) => {
  nextTick(() => {
    setTimeout(() => {
      if (tab === 'publisher' && publisherList.value.length > 0) {
        initPublisherCharts()
      } else if (tab === 'year' && yearList.value.length > 0) {
        initYearCharts()
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
  
  const sortedYears = [...yearList.value].sort((a, b) => a.year - b.year)
  const years = sortedYears.map(item => item.year.toString())
  
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
  loadAllData()
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
</style>


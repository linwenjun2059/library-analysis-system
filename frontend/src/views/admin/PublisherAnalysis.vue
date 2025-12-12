<template>
  <div class="publisher-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><OfficeBuilding /></el-icon> 出版社分析</span>
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
                  <span>出版社借阅排行榜（TOP 20）</span>
                </template>
                <div ref="rankingChartRef" style="width: 100%; height: 500px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>出版社图书数量分布</span>
                </template>
                <div ref="bookCountChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>出版社平均借阅次数</span>
                </template>
                <div ref="avgLendChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
          <el-table 
            :data="publisherList" 
            v-loading="loading"
            stripe
            style="width: 100%"
          >
            <el-table-column type="index" label="排名" width="80" align="center">
              <template #default="{ $index }">
                <el-tag 
                  :type="$index < 3 ? 'danger' : $index < 10 ? 'warning' : 'info'"
                  effect="dark"
                >
                  {{ $index + 1 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="publisher" label="出版社" min-width="200" show-overflow-tooltip />
            <el-table-column prop="bookCount" label="图书数量" width="120" align="center" sortable />
            <el-table-column prop="totalLendCount" label="总借阅次数" width="140" align="center" sortable />
            <el-table-column prop="totalUserCount" label="总借阅用户数" width="140" align="center" sortable />
            <el-table-column prop="avgLendCount" label="平均借阅次数" width="140" align="center" :formatter="formatNumber" sortable />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getPublisherAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { OfficeBuilding, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const viewMode = ref('chart')
const publisherList = ref([])
const rankingChartRef = ref(null)
const bookCountChartRef = ref(null)
const avgLendChartRef = ref(null)
let rankingChart = null
let bookCountChart = null
let avgLendChart = null

const formatNumber = (row, column, cellValue) => {
  return cellValue ? cellValue.toFixed(2) : '0.00'
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await getPublisherAnalysis()
    publisherList.value = result.data || []
    
    if (viewMode.value === 'chart') {
      nextTick(() => {
        initCharts()
      })
    }
  } catch (error) {
    ElMessage.error('加载数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const initCharts = () => {
  if (publisherList.value.length === 0) return
  
  const top20 = publisherList.value.slice(0, 20)
  const names = top20.map(item => item.publisher)
  
  // 排行榜柱状图
  if (rankingChartRef.value) {
    if (rankingChart) {
      rankingChart.dispose()
    }
    rankingChart = echarts.init(rankingChartRef.value)
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: {
          rotate: 30
        }
      },
      yAxis: {
        type: 'value',
        name: '总借阅次数'
      },
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
    }
    rankingChart.setOption(option)
  }
  
  // 图书数量分布饼图
  if (bookCountChartRef.value) {
    if (bookCountChart) {
      bookCountChart.dispose()
    }
    bookCountChart = echarts.init(bookCountChartRef.value)
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [{
        name: '图书数量',
        type: 'pie',
        radius: ['40%', '70%'],
        data: top20.map(item => ({
          value: item.bookCount,
          name: item.publisher
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
    bookCountChart.setOption(option)
  }
  
  // 平均借阅次数柱状图
  if (avgLendChartRef.value) {
    if (avgLendChart) {
      avgLendChart.dispose()
    }
    avgLendChart = echarts.init(avgLendChartRef.value)
    
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: {
          rotate: 30
        }
      },
      yAxis: {
        type: 'value',
        name: '平均借阅次数'
      },
      series: [{
        data: top20.map(item => item.avgLendCount),
        type: 'bar',
        itemStyle: {
          color: '#67c23a'
        }
      }]
    }
    avgLendChart.setOption(option)
  }
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (rankingChart) rankingChart.dispose()
  if (bookCountChart) bookCountChart.dispose()
  if (avgLendChart) avgLendChart.dispose()
})
</script>

<style scoped>
.publisher-analysis-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


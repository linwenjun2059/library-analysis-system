<template>
  <div class="location-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Location /></el-icon> 馆藏位置分析</span>
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
                  <span>馆藏位置借阅排行榜</span>
                </template>
                <div ref="rankingChartRef" style="width: 100%; height: 500px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>位置流通率分析</span>
                </template>
                <div ref="circulationChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>位置图书数量分布</span>
                </template>
                <div ref="bookCountChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
          <el-table 
            :data="locationList" 
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
            <el-table-column prop="location" label="馆藏位置" min-width="200" show-overflow-tooltip />
            <el-table-column prop="bookCount" label="图书总数" width="120" align="center" sortable />
            <el-table-column prop="borrowedBooks" label="已借图书数" width="120" align="center" sortable />
            <el-table-column prop="totalLendCount" label="总借阅次数" width="140" align="center" sortable />
            <el-table-column prop="circulationRate" label="流通率" width="120" align="center" :formatter="formatPercent" sortable />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getLocationAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Location, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const viewMode = ref('chart')
const locationList = ref([])
const rankingChartRef = ref(null)
const circulationChartRef = ref(null)
const bookCountChartRef = ref(null)
let rankingChart = null
let circulationChart = null
let bookCountChart = null

const formatPercent = (row, column, cellValue) => {
  return cellValue ? (cellValue * 100).toFixed(2) + '%' : '0.00%'
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await getLocationAnalysis()
    locationList.value = result.data || []
    
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
  if (locationList.value.length === 0) return
  
  const names = locationList.value.map(item => item.location)
  
  // 排行榜柱状图
  if (rankingChartRef.value) {
    if (rankingChart) {
      rankingChart.dispose()
    }
    rankingChart = echarts.init(rankingChartRef.value)
    
    const option = {
      title: {
        text: '馆藏位置借阅排行榜',
        left: 'center'
      },
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
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '总借阅次数'
      },
      series: [{
        data: locationList.value.map(item => item.totalLendCount),
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
  
  // 流通率柱状图
  if (circulationChartRef.value) {
    if (circulationChart) {
      circulationChart.dispose()
    }
    circulationChart = echarts.init(circulationChartRef.value)
    
    const option = {
      title: {
        text: '位置流通率分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: '{b}: {c}%'
      },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '流通率(%)',
        max: 100
      },
      series: [{
        data: locationList.value.map(item => (item.circulationRate * 100).toFixed(2)),
        type: 'bar',
        itemStyle: {
          color: function(params) {
            const rate = locationList.value[params.dataIndex].circulationRate * 100
            if (rate >= 70) return '#67c23a'
            if (rate >= 50) return '#e6a23c'
            return '#f56c6c'
          }
        }
      }]
    }
    circulationChart.setOption(option)
  }
  
  // 图书数量分布饼图
  if (bookCountChartRef.value) {
    if (bookCountChart) {
      bookCountChart.dispose()
    }
    bookCountChart = echarts.init(bookCountChartRef.value)
    
    const option = {
      title: {
        text: '位置图书数量分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [{
        name: '图书数量',
        type: 'pie',
        radius: ['40%', '70%'],
        data: locationList.value.map(item => ({
          value: item.bookCount,
          name: item.location
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
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (rankingChart) rankingChart.dispose()
  if (circulationChart) circulationChart.dispose()
  if (bookCountChart) bookCountChart.dispose()
})
</script>

<style scoped>
.location-analysis-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


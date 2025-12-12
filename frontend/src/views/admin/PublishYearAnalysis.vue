<template>
  <div class="publish-year-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Calendar /></el-icon> 出版年份分析</span>
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
                  <span>出版年份分布趋势</span>
                </template>
                <div ref="trendChartRef" style="width: 100%; height: 500px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>各年份图书数量</span>
                </template>
                <div ref="bookCountChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>各年份借阅次数</span>
                </template>
                <div ref="lendCountChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
          <el-table 
            :data="yearList" 
            v-loading="loading"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="year" label="出版年份" width="120" align="center" sortable />
            <el-table-column prop="bookCount" label="图书数量" width="120" align="center" sortable />
            <el-table-column prop="totalLendCount" label="总借阅次数" width="140" align="center" sortable />
            <el-table-column label="平均借阅次数" width="140" align="center" sortable>
              <template #default="{ row }">
                {{ row.bookCount > 0 ? (row.totalLendCount / row.bookCount).toFixed(2) : '0.00' }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getPublishYearAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Calendar, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const viewMode = ref('chart')
const yearList = ref([])
const trendChartRef = ref(null)
const bookCountChartRef = ref(null)
const lendCountChartRef = ref(null)
let trendChart = null
let bookCountChart = null
let lendCountChart = null

const loadData = async () => {
  loading.value = true
  try {
    const result = await getPublishYearAnalysis()
    yearList.value = (result.data || []).sort((a, b) => b.year - a.year)
    
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
  if (yearList.value.length === 0) return
  
  const sortedYears = [...yearList.value].sort((a, b) => a.year - b.year)
  const years = sortedYears.map(item => item.year.toString())
  
  // 趋势图（双Y轴）
  if (trendChartRef.value) {
    if (trendChart) {
      trendChart.dispose()
    }
    trendChart = echarts.init(trendChartRef.value)
    
    const option = {
      title: {
        text: '出版年份分布趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['图书数量', '借阅次数'],
        top: 30
      },
      xAxis: {
        type: 'category',
        data: years
      },
      yAxis: [
        {
          type: 'value',
          name: '图书数量',
          position: 'left'
        },
        {
          type: 'value',
          name: '借阅次数',
          position: 'right'
        }
      ],
      series: [
        {
          name: '图书数量',
          type: 'bar',
          data: sortedYears.map(item => item.bookCount),
          itemStyle: {
            color: '#5470c6'
          }
        },
        {
          name: '借阅次数',
          type: 'line',
          yAxisIndex: 1,
          data: sortedYears.map(item => item.totalLendCount),
          itemStyle: {
            color: '#91cc75'
          }
        }
      ]
    }
    trendChart.setOption(option)
  }
  
  // 图书数量柱状图
  if (bookCountChartRef.value) {
    if (bookCountChart) {
      bookCountChart.dispose()
    }
    bookCountChart = echarts.init(bookCountChartRef.value)
    
    const option = {
      title: {
        text: '各年份图书数量',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: years,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '图书数量'
      },
      series: [{
        data: sortedYears.map(item => item.bookCount),
        type: 'bar',
        itemStyle: {
          color: '#409eff'
        }
      }]
    }
    bookCountChart.setOption(option)
  }
  
  // 借阅次数柱状图
  if (lendCountChartRef.value) {
    if (lendCountChart) {
      lendCountChart.dispose()
    }
    lendCountChart = echarts.init(lendCountChartRef.value)
    
    const option = {
      title: {
        text: '各年份借阅次数',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: years,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: '借阅次数'
      },
      series: [{
        data: sortedYears.map(item => item.totalLendCount),
        type: 'bar',
        itemStyle: {
          color: '#67c23a'
        }
      }]
    }
    lendCountChart.setOption(option)
  }
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (trendChart) trendChart.dispose()
  if (bookCountChart) bookCountChart.dispose()
  if (lendCountChart) lendCountChart.dispose()
})
</script>

<style scoped>
.publish-year-analysis-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


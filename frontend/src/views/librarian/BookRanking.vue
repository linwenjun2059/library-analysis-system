<template>
  <div class="book-ranking-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Trophy /></el-icon> 图书排行与分析</span>
          <el-button type="primary" size="small" @click="loadAllData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <!-- 维度选择 -->
      <div style="margin-bottom: 20px;">
        <el-radio-group v-model="dimension" @change="loadRankingData">
          <el-radio-button label="totalLendCount">借阅次数</el-radio-button>
          <el-radio-button label="uniqueUserCount">借阅用户数</el-radio-button>
          <el-radio-button label="lendFrequency">借阅频率</el-radio-button>
          <el-radio-button label="avgBorrowDays">平均借阅天数</el-radio-button>
        </el-radio-group>
        <el-select v-model="limit" @change="loadRankingData" style="width: 120px; margin-left: 20px;">
          <el-option label="TOP 10" :value="10" />
          <el-option label="TOP 20" :value="20" />
          <el-option label="TOP 50" :value="50" />
        </el-select>
      </div>
      
      <el-tabs v-model="viewMode">
        <!-- 图表视图 -->
        <el-tab-pane name="chart">
          <template #label>
            <span><el-icon><DataAnalysis /></el-icon> 图表视图</span>
          </template>
          <div ref="chartRef" :style="{ width: '100%', height: chartHeight + 'px' }"></div>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane name="table">
          <template #label>
            <span><el-icon><List /></el-icon> 表格视图</span>
          </template>
          <el-table 
            :data="bookList" 
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
            <el-table-column prop="title" label="书名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
            <el-table-column prop="subject" label="主题" width="120" show-overflow-tooltip />
            <el-table-column prop="totalLendCount" label="借阅次数" width="120" align="center" sortable />
            <el-table-column prop="uniqueUserCount" label="借阅用户数" width="120" align="center" sortable />
            <el-table-column prop="lendFrequency" label="借阅频率" width="120" align="center" :formatter="formatNumber" sortable />
            <el-table-column prop="avgBorrowDays" label="平均借阅天数" width="140" align="center" :formatter="formatNumber" sortable />
            <el-table-column prop="renewCount" label="续借次数" width="120" align="center" sortable />
          </el-table>
        </el-tab-pane>
      </el-tabs>
      
      <!-- 主题/作者分布 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :lg="12">
          <el-card shadow="hover">
            <template #header>
              <span>当前排行榜 - 主题分布</span>
            </template>
            <div ref="subjectChartRef" style="width: 100%; height: 350px;"></div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card shadow="hover">
            <template #header>
              <span>当前排行榜 - 作者分布</span>
            </template>
            <div ref="authorChartRef" style="width: 100%; height: 350px;"></div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getBookRanking } from '@/api/book'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Trophy, Refresh, DataAnalysis, List } from '@element-plus/icons-vue'

const loading = ref(false)
const dimension = ref('totalLendCount')
const limit = ref(20)
const viewMode = ref('chart')
const bookList = ref([])

// 根据limit动态计算图表高度
const chartHeight = computed(() => {
  if (limit.value <= 10) return 400
  if (limit.value <= 20) return 600
  return 700
})

const chartRef = ref(null)
const subjectChartRef = ref(null)
const authorChartRef = ref(null)

let chart = null
let subjectChart = null
let authorChart = null

const dimensionNames = {
  totalLendCount: '借阅次数',
  uniqueUserCount: '借阅用户数',
  lendFrequency: '借阅频率',
  avgBorrowDays: '平均借阅天数'
}

const formatNumber = (row, column, cellValue) => {
  return cellValue ? cellValue.toFixed(2) : '0.00'
}

const loadAllData = async () => {
  await loadRankingData()
}

const loadRankingData = async () => {
  loading.value = true
  try {
    const result = await getBookRanking({
      dimension: dimension.value,
      limit: limit.value
    })
    bookList.value = result.data || []
    
    nextTick(() => {
      initChart()
      initSubjectChart()
      initAuthorChart()
    })
  } catch (error) {
    ElMessage.error('加载排行数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const initSubjectChart = () => {
  if (!subjectChartRef.value || bookList.value.length === 0) return
  
  if (!subjectChart) {
    subjectChart = echarts.init(subjectChartRef.value)
  }
  
  const subjectMap = {}
  bookList.value.forEach(book => {
    if (book.subject) {
      subjectMap[book.subject] = (subjectMap[book.subject] || 0) + 1
    }
  })
  
  const sortedData = Object.entries(subjectMap)
    .map(([subject, count]) => ({ subject, count }))
    .sort((a, b) => b.count - a.count)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}本 ({d}%)'
    },
    series: [{
      name: '图书数量',
      type: 'pie',
      radius: ['40%', '70%'],
      data: sortedData.map(item => ({
        value: item.count,
        name: item.subject || '未知'
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}\n{c}本'
      }
    }]
  }
  
  subjectChart.setOption(option, true)
}

const initAuthorChart = () => {
  if (!authorChartRef.value || bookList.value.length === 0) return
  
  if (!authorChart) {
    authorChart = echarts.init(authorChartRef.value)
  }
  
  const authorMap = {}
  bookList.value.forEach(book => {
    if (book.author) {
      authorMap[book.author] = (authorMap[book.author] || 0) + 1
    }
  })
  
  const topCount = Math.min(limit.value, Object.keys(authorMap).length)
  const sortedData = Object.entries(authorMap)
    .map(([author, count]) => ({ author, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, topCount)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}本'
    },
    grid: {
      left: '30%',
      right: '10%',
      bottom: '10%',
      top: '5%'
    },
    xAxis: {
      type: 'value',
      name: '图书数量'
    },
    yAxis: {
      type: 'category',
      data: sortedData.map(item => {
        const author = item.author || '未知'
        return author.length > 12 ? author.substring(0, 12) + '...' : author
      }),
      axisLabel: {
        interval: 0
      }
    },
    series: [{
      name: '图书数量',
      type: 'bar',
      data: sortedData.map(item => item.count),
      itemStyle: { color: '#67c23a' },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  authorChart.setOption(option, true)
}

const initChart = () => {
  if (!chartRef.value || bookList.value.length === 0) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const data = bookList.value.slice(0, limit.value).reverse()
  const names = data.map((item, index) => {
    const title = item.title || item.bookId || '未知'
    return title.length > 20 ? title.substring(0, 20) + '...' : title
  })
  const values = data.map(item => {
    switch (dimension.value) {
      case 'totalLendCount':
        return item.totalLendCount || 0
      case 'uniqueUserCount':
        return item.uniqueUserCount || 0
      case 'lendFrequency':
        return item.lendFrequency || 0
      case 'avgBorrowDays':
        return item.avgBorrowDays || 0
      case 'overdueRate':
        return (item.overdueRate || 0) * 100
      default:
        return 0
    }
  })
  
  const option = {
    title: {
      text: `${dimensionNames[dimension.value]}排行榜 TOP ${limit.value}`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const item = data[params[0].dataIndex]
        return `${item.title || item.bookId}<br/>作者: ${item.author || '未知'}<br/>${dimensionNames[dimension.value]}: ${params[0].value}`
      }
    },
    grid: {
      left: '25%',
      right: '5%',
      bottom: '5%',
      top: '10%'
    },
    xAxis: {
      type: 'value',
      name: dimensionNames[dimension.value]
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        interval: 0,
        fontSize: limit.value > 20 ? 10 : 12
      }
    },
    series: [{
      data: values,
      type: 'bar',
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
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        }
      }
    }]
  }
  
  chart.setOption(option)
}

onMounted(() => {
  loadAllData()
  window.addEventListener('resize', handleResize)
})

const handleResize = () => {
  chart?.resize()
  subjectChart?.resize()
  authorChart?.resize()
}

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  subjectChart?.dispose()
  authorChart?.dispose()
})
</script>

<style scoped>
.book-ranking-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


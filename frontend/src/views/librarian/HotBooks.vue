<template>
  <div class="hot-books-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Trophy /></el-icon> 热门图书统计</span>
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
                  <div class="card-header">
                    <span>热门图书排行榜（TOP 20）</span>
                    <el-select v-model="topLimit" @change="loadData" style="width: 120px;">
                      <el-option label="TOP 20" :value="20" />
                      <el-option label="TOP 50" :value="50" />
                      <el-option label="TOP 100" :value="100" />
                    </el-select>
                  </div>
                </template>
                <div ref="chartRef" style="width: 100%; height: 500px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>主题分布（TOP 10）</span>
                </template>
                <div ref="subjectChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
            
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover">
                <template #header>
                  <span>作者分布（TOP 10）</span>
                </template>
                <div ref="authorChartRef" style="width: 100%; height: 400px;"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
          <div style="margin-bottom: 15px;">
            <el-space wrap>
              <el-input v-model="searchText" placeholder="搜索书名、作者" clearable style="width: 250px;">
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="subjectFilter" placeholder="按主题筛选" clearable style="width: 150px;">
                <el-option 
                  v-for="subject in subjectList" 
                  :key="subject" 
                  :label="subject" 
                  :value="subject" 
                />
              </el-select>
            </el-space>
          </div>
          
          <el-table 
            :data="pagedBooks" 
            v-loading="loading"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="rankNo" label="排名" width="80" align="center">
              <template #default="{ row }">
                <el-tag 
                  :type="row.rankNo <= 3 ? 'danger' : row.rankNo <= 10 ? 'warning' : 'info'"
                  effect="dark"
                >
                  {{ row.rankNo }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="书名" min-width="250" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="180" show-overflow-tooltip />
            <el-table-column prop="subject" label="主题分类" width="120" />
            <el-table-column prop="borrowCount" label="借阅次数" width="120" align="center" sortable />
          </el-table>
          
          <el-pagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { getHotBooks } from '@/api/book'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const viewMode = ref('chart')
const topLimit = ref(20)
const searchText = ref('')
const subjectFilter = ref('')

const chartRef = ref(null)
const subjectChartRef = ref(null)
const authorChartRef = ref(null)

let chart = null
let subjectChart = null
let authorChart = null

const hotBooksData = ref([])

const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

// 计算属性
const filteredBooks = computed(() => {
  let result = hotBooksData.value
  
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    result = result.filter(book => 
      (book.title && book.title.toLowerCase().includes(keyword)) ||
      (book.author && book.author.toLowerCase().includes(keyword))
    )
  }
  
  if (subjectFilter.value) {
    result = result.filter(book => book.subject === subjectFilter.value)
  }
  
  return result
})

const pagedBooks = computed(() => {
  const start = (pagination.current - 1) * pagination.size
  const end = start + pagination.size
  return filteredBooks.value.slice(start, end)
})

const subjectList = computed(() => {
  const subjects = new Set()
  hotBooksData.value.forEach(book => {
    if (book.subject) subjects.add(book.subject)
  })
  return Array.from(subjects).sort()
})

// 初始化主图表
const initChart = () => {
  if (!chartRef.value || hotBooksData.value.length === 0) return
  
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  
  const topN = hotBooksData.value.slice(0, topLimit.value).reverse()
  const titles = topN.map(item => {
    const title = item.title || '未知'
    return title.length > 25 ? title.substring(0, 25) + '...' : title
  })
  const counts = topN.map(item => item.borrowCount || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = topN[params[0].dataIndex]
        return `${item.title}<br/>作者: ${item.author || '未知'}<br/>主题: ${item.subject || '未知'}<br/>借阅次数: ${params[0].value}`
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '借阅次数'
    },
    yAxis: {
      type: 'category',
      data: titles,
      axisLabel: {
        interval: 0,
        fontSize: 12
      }
    },
    series: [{
      name: '借阅次数',
      type: 'bar',
      data: counts,
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
  
  chart.setOption(option)
}

// 初始化主题分布图表
const initSubjectChart = () => {
  if (!subjectChartRef.value || hotBooksData.value.length === 0) return
  
  if (!subjectChart) {
    subjectChart = echarts.init(subjectChartRef.value)
  }
  
  const subjectMap = {}
  hotBooksData.value.forEach(book => {
    if (book.subject) {
      subjectMap[book.subject] = (subjectMap[book.subject] || 0) + (book.borrowCount || 0)
    }
  })
  
  const top10 = Object.entries(subjectMap)
    .map(([subject, count]) => ({ subject, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}次 ({d}%)'
    },
    series: [{
      name: '借阅次数',
      type: 'pie',
      radius: '60%',
      data: top10.map(item => ({
        value: item.count,
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

// 初始化作者分布图表
const initAuthorChart = () => {
  if (!authorChartRef.value || hotBooksData.value.length === 0) return
  
  if (!authorChart) {
    authorChart = echarts.init(authorChartRef.value)
  }
  
  const authorMap = {}
  hotBooksData.value.forEach(book => {
    if (book.author) {
      authorMap[book.author] = (authorMap[book.author] || 0) + (book.borrowCount || 0)
    }
  })
  
  const top10 = Object.entries(authorMap)
    .map(([author, count]) => ({ author, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}次'
    },
    grid: {
      left: '30%',
      right: '5%',
      bottom: '10%',
      top: '5%'
    },
    xAxis: {
      type: 'value',
      name: '借阅次数'
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => {
        const author = item.author || '未知'
        return author.length > 15 ? author.substring(0, 15) + '...' : author
      }),
      axisLabel: {
        interval: 0
      }
    },
    series: [{
      name: '借阅次数',
      type: 'bar',
      data: top10.map(item => item.count),
      itemStyle: { color: '#67c23a' },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}'
      }
    }]
  }
  
  authorChart.setOption(option)
}

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    const res = await getHotBooks({ limit: 100 })
    hotBooksData.value = res.data || []
    pagination.total = filteredBooks.value.length
    pagination.current = 1
    
    // 初始化图表
    if (viewMode.value === 'chart') {
      initChart()
      initSubjectChart()
      initAuthorChart()
    }
    
    console.log(`✅ 加载热门图书成功：共 ${hotBooksData.value.length} 条`)
  } catch (error) {
    console.error('❌ 加载热门图书失败：', error)
    ElMessage.error('加载热门图书失败')
    hotBooksData.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 监听筛选条件变化
watch([searchText, subjectFilter], () => {
  pagination.total = filteredBooks.value.length
  pagination.current = 1
})

// 监听视图模式变化
watch(viewMode, (newVal) => {
  if (newVal === 'chart' && hotBooksData.value.length > 0) {
    setTimeout(() => {
      initChart()
      initSubjectChart()
      initAuthorChart()
    }, 100)
  }
})

onMounted(() => {
  loadData()
  window.addEventListener('resize', () => {
    chart?.resize()
    subjectChart?.resize()
    authorChart?.resize()
  })
})

onUnmounted(() => {
  chart?.dispose()
  subjectChart?.dispose()
  authorChart?.dispose()
})
</script>

<style scoped lang="scss">
.hot-books-container {
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
  
  :deep(.el-card) {
    margin-bottom: 20px;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .el-card__header {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
  }
  
  :deep(.el-tabs) {
    .el-tabs__header {
      margin-bottom: 20px;
    }
    
    .el-tabs__item {
      font-weight: 500;
      transition: all 0.3s;
      
      &.is-active {
        font-weight: 700;
        color: #667eea;
      }
    }
    
    .el-tabs__active-bar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      height: 3px;
    }
  }
}
</style>


<template>
  <div class="book-detail-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Document /></el-icon> 图书详情分析</span>
        </div>
      </template>
      
      <!-- 搜索框 -->
      <div class="search-box">
        <el-input
          v-model="keyword"
          placeholder="请输入书名、作者或主题进行搜索"
          clearable
          size="large"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button @click="handleSearch" :loading="loading">搜索</el-button>
          </template>
        </el-input>
      </div>
      
      <el-divider />
      
      <!-- 图书列表 -->
      <el-table 
        :data="books" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="showBookDetail(row)" :underline="false">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="150" show-overflow-tooltip />
        <el-table-column prop="publisher" label="出版社" width="150" show-overflow-tooltip />
        <el-table-column prop="pubYear" label="出版年份" width="100" align="center" />
        <el-table-column prop="subject" label="主题分类" width="120" />
        <el-table-column prop="locationName" label="馆藏位置" width="150" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showBookDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 图书详情分析对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="图书详情分析"
      width="90%"
      :loading="detailLoading"
    >
      <div v-if="bookInfo" v-loading="detailLoading">
        <!-- 图书基本信息 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <span>图书基本信息</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="书名">{{ bookInfo.title }}</el-descriptions-item>
            <el-descriptions-item label="作者">{{ bookInfo.author }}</el-descriptions-item>
            <el-descriptions-item label="出版社">{{ bookInfo.publisher }}</el-descriptions-item>
            <el-descriptions-item label="出版年份">{{ bookInfo.pubYear }}</el-descriptions-item>
            <el-descriptions-item label="主题分类">{{ bookInfo.subject }}</el-descriptions-item>
            <el-descriptions-item label="馆藏位置">{{ bookInfo.locationName }}</el-descriptions-item>
            <el-descriptions-item label="ISBN">{{ bookInfo.isbn }}</el-descriptions-item>
            <el-descriptions-item label="索书号">{{ bookInfo.callNo }}</el-descriptions-item>
            <el-descriptions-item label="文献类型">{{ bookInfo.docTypeName }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        
        <!-- 借阅统计 -->
        <el-row :gutter="20" v-if="lendSummary">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="总借阅次数" :value="lendSummary.totalLendCount || 0">
              <template #prefix>
                <el-icon color="#409eff"><Reading /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="借阅用户数" :value="lendSummary.uniqueUserCount || 0">
              <template #prefix>
                <el-icon color="#67c23a"><User /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="平均借阅天数" :value="lendSummary.avgBorrowDays || 0" :precision="1">
              <template #prefix>
                <el-icon color="#e6a23c"><Timer /></el-icon>
              </template>
              <template #suffix>天</template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="借阅频率" :value="lendSummary.lendFrequency || 0" :precision="2">
              <template #prefix>
                <el-icon color="#909399"><TrendCharts /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="逾期次数" :value="lendSummary.overdueCount || 0">
              <template #prefix>
                <el-icon color="#f56c6c"><Warning /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic 
              title="逾期率" 
              :value="(lendSummary.overdueRate || 0) * 100" 
              :precision="2"
            >
              <template #prefix>
                <el-icon color="#f56c6c"><WarningFilled /></el-icon>
              </template>
              <template #suffix>%</template>
            </el-statistic>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6">
          <el-card shadow="hover">
            <el-statistic title="续借次数" :value="lendSummary.renewCount || 0">
              <template #prefix>
                <el-icon color="#409eff"><Refresh /></el-icon>
              </template>
            </el-statistic>
          </el-card>
        </el-col>
        </el-row>
        
        <!-- 数据可视化图表 -->
        <el-row :gutter="20" style="margin-top: 20px;">
          <!-- 借阅指标对比 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover">
              <template #header>
                <span><el-icon><DataAnalysis /></el-icon> 借阅指标对比</span>
              </template>
              <div ref="barChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          
          <!-- 借阅情况分布 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover">
              <template #header>
                <span><el-icon><PieChart /></el-icon> 借阅情况分布</span>
              </template>
              <div ref="pieChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 20px;">
          <!-- 续借率仪表盘 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover">
              <template #header>
                <span><el-icon><Odometer /></el-icon> 续借率分析</span>
              </template>
              <div ref="gaugeChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          
          <!-- 受欢迎程度 -->
          <el-col :xs="24" :md="12">
            <el-card shadow="hover">
              <template #header>
                <span><el-icon><TrendCharts /></el-icon> 受欢迎程度</span>
              </template>
              <div ref="popularityChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 时间信息 -->
        <el-card v-if="lendSummary" shadow="hover" style="margin-top: 20px;">
          <template #header>
            <span>时间信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="首次借阅日期">
              {{ lendSummary.firstLendDate ? formatDate(lendSummary.firstLendDate) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="最后借阅日期">
              {{ lendSummary.lastLendDate ? formatDate(lendSummary.lastLendDate) : '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { searchBooks, getBookLendSummary } from '@/api/book'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  Document, Search, Reading, User, Timer, TrendCharts, 
  Warning, WarningFilled, Refresh, DataAnalysis, PieChart, Odometer
} from '@element-plus/icons-vue'

const loading = ref(false)
const keyword = ref('')
const books = ref([])
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const bookInfo = ref(null)
const lendSummary = ref(null)

const barChartRef = ref(null)
const pieChartRef = ref(null)
const gaugeChartRef = ref(null)
const popularityChartRef = ref(null)
let barChart = null
let pieChart = null
let gaugeChart = null
let popularityChart = null

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN')
}

const handleSearch = async () => {
  pagination.current = 1
  await loadBooks()
}

const loadBooks = async () => {
  try {
    loading.value = true
    const res = await searchBooks({
      keyword: keyword.value,
      current: pagination.current,
      size: pagination.size
    })
    
    books.value = res.data.records
    pagination.total = res.data.total
  } catch (error) {
    console.error('搜索图书失败：', error)
    ElMessage.error('搜索图书失败')
  } finally {
    loading.value = false
  }
}

const showBookDetail = async (book) => {
  bookInfo.value = book
  detailDialogVisible.value = true
  detailLoading.value = true
  lendSummary.value = null
  
  try {
    // 加载借阅汇总
    const summaryResult = await getBookLendSummary(book.bookId)
    lendSummary.value = summaryResult.data
    
    // 初始化图表
    nextTick(() => {
      initCharts()
    })
  } catch (error) {
    console.error('加载图书详情失败：', error)
    ElMessage.error('加载图书详情失败')
  } finally {
    detailLoading.value = false
  }
}

const initCharts = () => {
  if (!lendSummary.value) return
  
  initBarChart()
  initPieChart()
  initGaugeChart()
  initPopularityChart()
}

// 借阅指标对比柱状图
const initBarChart = () => {
  if (!barChartRef.value) return
  
  if (barChart) barChart.dispose()
  barChart = echarts.init(barChartRef.value)
  
  const summary = lendSummary.value
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value'
    },
    yAxis: {
      type: 'category',
      data: ['借阅次数', '借阅用户', '续借次数']
    },
    series: [{
      type: 'bar',
      data: [
        { value: summary.totalLendCount || 0, itemStyle: { color: '#409eff' } },
        { value: summary.uniqueUserCount || 0, itemStyle: { color: '#67c23a' } },
        { value: summary.renewCount || 0, itemStyle: { color: '#e6a23c' } }
      ],
      label: {
        show: true,
        position: 'right'
      },
      barWidth: '60%'
    }]
  }
  
  barChart.setOption(option)
}

// 借阅情况饼图
const initPieChart = () => {
  if (!pieChartRef.value) return
  
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieChartRef.value)
  
  const summary = lendSummary.value
  const normalCount = (summary.totalLendCount || 0) - (summary.overdueCount || 0)
  const overdueCount = summary.overdueCount || 0
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
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
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      data: [
        { value: normalCount, name: '正常借阅', itemStyle: { color: '#67c23a' } },
        { value: overdueCount, name: '逾期借阅', itemStyle: { color: '#f56c6c' } }
      ]
    }]
  }
  
  pieChart.setOption(option)
}

// 续借率仪表盘
const initGaugeChart = () => {
  if (!gaugeChartRef.value) return
  
  if (gaugeChart) gaugeChart.dispose()
  gaugeChart = echarts.init(gaugeChartRef.value)
  
  const summary = lendSummary.value
  const renewRate = summary.totalLendCount > 0 
    ? ((summary.renewCount || 0) / summary.totalLendCount * 100).toFixed(1)
    : 0
  
  const option = {
    series: [{
      type: 'gauge',
      center: ['50%', '60%'],
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 10,
      itemStyle: {
        color: '#409eff'
      },
      progress: {
        show: true,
        width: 18
      },
      pointer: {
        show: false
      },
      axisLine: {
        lineStyle: {
          width: 18
        }
      },
      axisTick: {
        distance: -30,
        splitNumber: 5,
        lineStyle: {
          width: 1,
          color: '#999'
        }
      },
      splitLine: {
        distance: -32,
        length: 14,
        lineStyle: {
          width: 2,
          color: '#999'
        }
      },
      axisLabel: {
        distance: -20,
        color: '#999',
        fontSize: 12
      },
      anchor: {
        show: false
      },
      title: {
        show: false
      },
      detail: {
        valueAnimation: true,
        width: '60%',
        lineHeight: 40,
        borderRadius: 8,
        offsetCenter: [0, '-15%'],
        fontSize: 32,
        fontWeight: 'bolder',
        formatter: '{value}%',
        color: 'inherit'
      },
      data: [{ value: renewRate }]
    }]
  }
  
  gaugeChart.setOption(option)
}

// 受欢迎程度雷达图
const initPopularityChart = () => {
  if (!popularityChartRef.value) return
  
  if (popularityChart) popularityChart.dispose()
  popularityChart = echarts.init(popularityChartRef.value)
  
  const summary = lendSummary.value
  
  // 归一化分数 (0-100)
  const normalizeScore = (value, max) => {
    return Math.min(100, (value / max) * 100)
  }
  
  // 实际数值
  const actualValues = {
    lendCount: summary.totalLendCount || 0,
    userCount: summary.uniqueUserCount || 0,
    frequency: (summary.lendFrequency || 0).toFixed(2),
    renewCount: summary.renewCount || 0,
    overdueRate: ((summary.overdueRate || 0) * 100).toFixed(2)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const dimensionNames = ['借阅次数', '用户覆盖', '借阅频率', '续借活跃', '守时情况']
        const actualData = [
          `${actualValues.lendCount}次`,
          `${actualValues.userCount}人`,
          `${actualValues.frequency}次/年`,
          `${actualValues.renewCount}次`,
          `逾期率${actualValues.overdueRate}%`
        ]
        
        let result = `<div style="font-weight: bold; margin-bottom: 8px;">${params.seriesName}</div>`
        params.value.forEach((val, idx) => {
          result += `
            <div style="margin: 4px 0;">
              ${dimensionNames[idx]}: 
              <span style="font-weight: bold; color: #409eff;">${val.toFixed(1)}</span>分
              <span style="color: #909399; margin-left: 8px;">(${actualData[idx]})</span>
            </div>
          `
        })
        return result
      }
    },
    radar: {
      indicator: [
        { name: '借阅次数', max: 100 },
        { name: '用户覆盖', max: 100 },
        { name: '借阅频率', max: 100 },
        { name: '续借活跃', max: 100 },
        { name: '守时情况', max: 100 }
      ],
      center: ['50%', '55%'],
      radius: '70%'
    },
    series: [{
      type: 'radar',
      name: '图书指标',
      data: [{
        value: [
          normalizeScore(summary.totalLendCount || 0, 200),
          normalizeScore(summary.uniqueUserCount || 0, 100),
          normalizeScore((summary.lendFrequency || 0), 5),
          normalizeScore((summary.renewCount || 0), 50),
          100 - ((summary.overdueRate || 0) * 100)
        ],
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.3)'
        },
        lineStyle: {
          color: '#409eff',
          width: 2
        },
        itemStyle: {
          color: '#409eff'
        }
      }]
    }]
  }
  
  popularityChart.setOption(option)
}

const handleResize = () => {
  barChart?.resize()
  pieChart?.resize()
  gaugeChart?.resize()
  popularityChart?.resize()
}

const handleSizeChange = () => {
  pagination.current = 1
  loadBooks()
}

const handleCurrentChange = () => {
  loadBooks()
}

onMounted(() => {
  loadBooks()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  barChart?.dispose()
  pieChart?.dispose()
  gaugeChart?.dispose()
  popularityChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.book-detail-container {
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .search-box {
    margin-bottom: 20px;
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .chart-container {
    width: 100%;
    height: 320px;
  }
}
</style>


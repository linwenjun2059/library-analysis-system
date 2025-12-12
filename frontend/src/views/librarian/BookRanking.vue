<template>
  <div class="book-ranking-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Trophy /></el-icon> 多维度图书排行榜</span>
          <el-button type="primary" size="small" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <!-- 维度选择 -->
      <div style="margin-bottom: 20px;">
        <el-radio-group v-model="dimension" @change="loadData">
          <el-radio-button label="totalLendCount">借阅次数</el-radio-button>
          <el-radio-button label="uniqueUserCount">借阅用户数</el-radio-button>
          <el-radio-button label="lendFrequency">借阅频率</el-radio-button>
          <el-radio-button label="avgBorrowDays">平均借阅天数</el-radio-button>
          <el-radio-button label="overdueRate">逾期率</el-radio-button>
        </el-radio-group>
        <el-select v-model="limit" @change="loadData" style="width: 120px; margin-left: 20px;">
          <el-option label="TOP 10" :value="10" />
          <el-option label="TOP 20" :value="20" />
          <el-option label="TOP 50" :value="50" />
        </el-select>
      </div>
      
      <el-tabs v-model="viewMode">
        <!-- 图表视图 -->
        <el-tab-pane label="📊 图表视图" name="chart">
          <div ref="chartRef" style="width: 100%; height: 500px;"></div>
        </el-tab-pane>
        
        <!-- 表格视图 -->
        <el-tab-pane label="📋 表格视图" name="table">
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
            <el-table-column prop="bookId" label="图书ID" min-width="150" />
            <el-table-column prop="totalLendCount" label="借阅次数" width="120" align="center" sortable />
            <el-table-column prop="uniqueUserCount" label="借阅用户数" width="120" align="center" sortable />
            <el-table-column prop="lendFrequency" label="借阅频率" width="120" align="center" :formatter="formatNumber" sortable />
            <el-table-column prop="avgBorrowDays" label="平均借阅天数" width="140" align="center" :formatter="formatNumber" sortable />
            <el-table-column prop="overdueRate" label="逾期率" width="120" align="center" :formatter="formatPercent" sortable />
            <el-table-column prop="renewCount" label="续借次数" width="120" align="center" sortable />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getBookRanking } from '@/api/book'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Trophy, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const dimension = ref('totalLendCount')
const limit = ref(20)
const viewMode = ref('chart')
const bookList = ref([])
const chartRef = ref(null)
let chart = null

const dimensionNames = {
  totalLendCount: '借阅次数',
  uniqueUserCount: '借阅用户数',
  lendFrequency: '借阅频率',
  avgBorrowDays: '平均借阅天数',
  overdueRate: '逾期率'
}

const formatNumber = (row, column, cellValue) => {
  return cellValue ? cellValue.toFixed(2) : '0.00'
}

const formatPercent = (row, column, cellValue) => {
  return cellValue ? (cellValue * 100).toFixed(2) + '%' : '0.00%'
}

const loadData = async () => {
  loading.value = true
  try {
    const result = await getBookRanking({
      dimension: dimension.value,
      limit: limit.value
    })
    bookList.value = result.data || []
    
    if (viewMode.value === 'chart') {
      nextTick(() => {
        initChart()
      })
    }
  } catch (error) {
    ElMessage.error('加载数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const initChart = () => {
  if (!chartRef.value || bookList.value.length === 0) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(chartRef.value)
  
  const data = bookList.value.slice(0, limit.value)
  const names = data.map((item, index) => `第${index + 1}名`)
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
      name: dimensionNames[dimension.value]
    },
    series: [{
      data: values,
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
  loadData()
})

onUnmounted(() => {
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.book-ranking-container {
  padding: 0px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


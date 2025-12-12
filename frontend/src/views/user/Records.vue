<template>
  <div class="records-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Document /></el-icon> 我的借阅记录</span>
          <div class="header-stats" v-if="pagination.total > 0">
            <el-tag type="info">共 {{ pagination.total }} 条记录</el-tag>
          </div>
        </div>
      </template>

      <!-- 借阅折线图（最近6个月） -->
      <el-card shadow="never" class="inner-card" style="margin-bottom: 20px;">
        <template #header>
          <div class="card-sub-header">
            <el-icon><TrendCharts /></el-icon>
            <span>借阅记录折线图（数据集内最近6个月，截止 2020-12-31）</span>
          </div>
        </template>
        <div ref="trendChartRef" style="width: 100%; height: 320px;"></div>
      </el-card>
      
      <el-table 
        :data="records" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="lendId" label="借阅ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="bookId" label="图书ID" min-width="150" show-overflow-tooltip />
        <el-table-column label="借阅日期" width="110">
          <template #default="{ row }">
            <span>{{ formatDate(row.lendDate) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lendTime" label="借阅时间" width="90" align="center" />
        <el-table-column label="归还日期" width="110">
          <template #default="{ row }">
            <span>{{ row.retDate ? formatDate(row.retDate) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="retTime" label="归还时间" width="90" align="center">
          <template #default="{ row }">
            <span>{{ row.retTime || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="borrowDays" label="借阅天数" width="100" align="center" />
        <el-table-column prop="renewTimes" label="续借次数" width="100" align="center" />
        <el-table-column label="是否逾期" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="Number(row.isOverdue) === 1 ? 'danger' : 'success'" size="small">
              {{ Number(row.isOverdue) === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.retDate ? 'info' : 'warning'" size="small">
              {{ row.retDate ? '已归还' : '未归还' }}
            </el-tag>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无借阅记录" />
        </template>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          :background="true"
          :hide-on-single-page="false"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUserLendRecords } from '@/api/user'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { TrendCharts } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const records = ref([])
const chartRecords = ref([])

const pagination = reactive({
  current: 1,
  size: 10,
  total: 0
})

const trendChartRef = ref(null)
let trendChart = null

// 日期格式化函数
const formatDate = (date) => {
  if (!date) return '-'
  
  // 如果已经是格式化的字符串，直接返回
  if (typeof date === 'string' && date.match(/^\d{4}-\d{2}-\d{2}$/)) {
    return date
  }
  
  // 处理 ISO 8601 格式或 Date 对象
  try {
    const d = new Date(date)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch (error) {
    console.error('日期格式化失败：', date, error)
    return '-'
  }
}

// 格式化为 YYYY-MM-DD
const formatDateYMD = (date) => {
  if (!date) return ''
  const d = new Date(date)
  if (Number.isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// 初始化折线图（最近6个月）
const initTrendChart = () => {
  if (!trendChartRef.value || chartRecords.value.length === 0) return

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }

  // 基于数据集中最大日期向前6个月
  const dates = chartRecords.value
    .map(r => new Date(r.lendDate))
    .filter(d => !Number.isNaN(d.getTime()))
    .sort((a, b) => a - b)

  if (dates.length === 0) return

  const maxDate = dates[dates.length - 1]
  const sixMonthsAgo = new Date(maxDate)
  sixMonthsAgo.setMonth(maxDate.getMonth() - 5)
  sixMonthsAgo.setDate(1) // 从所在月初开始

  const dailyCounts = {}
  chartRecords.value.forEach(record => {
    const dayStr = formatDateYMD(record.lendDate)
    if (!dayStr) return
    const d = new Date(dayStr)
    if (d >= sixMonthsAgo && d <= maxDate) {
      dailyCounts[dayStr] = (dailyCounts[dayStr] || 0) + 1
    }
  })

  const days = Object.keys(dailyCounts).sort()
  if (days.length === 0) return

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        if (!params || !params.length) return ''
        return `${params[0].axisValue}<br/>借阅次数: ${params[0].value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: days,
      boundaryGap: false,
      axisLabel: {
        interval: 'auto',
        rotate: days.length > 12 ? 30 : 0
      }
    },
    yAxis: {
      type: 'value',
      name: '借阅次数',
      minInterval: 1
    },
    series: [{
      name: '借阅次数',
      type: 'line',
      smooth: true,
      data: days.map(d => dailyCounts[d]),
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.25)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      itemStyle: {
        color: '#409eff'
      },
      lineStyle: {
        width: 3
      }
    }]
  }

  trendChart.setOption(option)
}

const loadRecords = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    // 分页表格
    const res = await getUserLendRecords(userid, {
      current: pagination.current,
      size: pagination.size
    })
    // 折线图用更大范围（最多1000条，取最近6个月）
    const chartRes = await getUserLendRecords(userid, {
      current: 1,
      size: 1000
    })
    
    console.log('===== 借阅记录API完整返回 =====')
    console.log('res:', res)
    console.log('res.data:', res.data)
    console.log('res.data.records:', res.data?.records)
    console.log('res.data.total:', res.data?.total)
    console.log('================================')
    
    // 直接赋值，不做复杂判断
    records.value = res.data?.records || []
    pagination.total = res.data?.total || 0
    chartRecords.value = chartRes.data?.records || []
    
    console.log(`✅ 最终结果：共 ${pagination.total} 条，显示 ${records.value.length} 条`)
    console.log('records.value:', records.value)
    
    await nextTick()
    initTrendChart()

  } catch (error) {
    console.error('❌ 加载失败：', error)
    ElMessage.error('加载借阅记录失败')
    records.value = []
    pagination.total = 0
    chartRecords.value = []
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  pagination.current = 1
  loadRecords()
}

const handleCurrentChange = () => {
  loadRecords()
}

onMounted(() => {
  loadRecords()
})

onUnmounted(() => {
  trendChart?.dispose()
})
</script>

<style scoped lang="scss">
.records-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
    
    > span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .header-stats {
      font-weight: 400;
    }
  }

  .inner-card {
    .card-sub-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}
</style>

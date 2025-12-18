<template>
  <div class="calendar-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Calendar /></el-icon> 借阅日历</span>
          <div class="header-controls">
            <el-date-picker
              v-model="selectedYear"
              type="year"
              placeholder="选择年份"
              @change="loadCalendar"
              format="YYYY"
              value-format="YYYY"
            />
          </div>
        </div>
      </template>
      
      <div v-loading="loading">
        <!-- 统计卡片 -->
        <el-row :gutter="20" style="margin-bottom: 20px;" v-if="calendarStats">
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-mini-card">
              <el-statistic title="借阅天数" :value="calendarStats.activeDays">
                <template #prefix><el-icon color="#409eff"><Calendar /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-mini-card">
              <el-statistic title="总借阅量" :value="calendarStats.totalBorrows">
                <template #prefix><el-icon color="#67c23a"><Reading /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-mini-card">
              <el-statistic title="最长连续" :value="calendarStats.maxStreak">
                <template #prefix><el-icon color="#e6a23c"><Histogram /></el-icon></template>
                <template #suffix>天</template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-card shadow="never" class="stat-mini-card">
              <el-statistic title="当前连续" :value="calendarStats.currentStreak">
                <template #prefix><el-icon color="#f56c6c"><TrendCharts /></el-icon></template>
                <template #suffix>天</template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <!-- GitHub风格日历热力图 -->
        <div ref="calendarChartRef" style="width: 100%; height: 200px; margin-bottom: 20px;"></div>
        
        <!-- 月度分布图表 -->
        <el-row :gutter="20">
          <el-col :xs="24" :lg="12">
            <el-card shadow="never">
              <template #header>
                <span>📊 月度借阅分布</span>
              </template>
              <div ref="monthChartRef" style="width: 100%; height: 280px;"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card shadow="never">
              <template #header>
                <span>📅 星期分布热力</span>
              </template>
              <div ref="weekHeatmapRef" style="width: 100%; height: 280px;"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getBorrowCalendar } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import { Calendar, Reading, Histogram, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const calendarChartRef = ref(null)
const monthChartRef = ref(null)
const weekHeatmapRef = ref(null)
const selectedYear = ref('2020')
const calendarData = ref({})
const calendarStats = ref(null)

let chartInstance = null
let monthChart = null
let weekHeatmapChart = null

// 计算日历统计
const calculateStats = (data) => {
  const dates = Object.keys(data).sort()
  const activeDays = dates.filter(date => data[date] > 0).length
  const totalBorrows = Object.values(data).reduce((sum, count) => sum + count, 0)
  
  // 计算连续天数
  let maxStreak = 0
  let currentStreak = 0
  let tempStreak = 0
  const today = dayjs()
  
  dates.forEach((date, index) => {
    if (data[date] > 0) {
      tempStreak++
      maxStreak = Math.max(maxStreak, tempStreak)
      
      // 检查是否是连续到今天
      const daysDiff = today.diff(dayjs(date), 'day')
      if (daysDiff === 0 || (index > 0 && dayjs(date).diff(dayjs(dates[index - 1]), 'day') === 1)) {
        currentStreak = tempStreak
      }
    } else {
      tempStreak = 0
    }
  })
  
  return {
    activeDays,
    totalBorrows,
    maxStreak,
    currentStreak: currentStreak || 0
  }
}

const loadCalendar = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    const res = await getBorrowCalendar(userid, { yearMonth: selectedYear.value })
    
    calendarData.value = res.data || {}
    calendarStats.value = calculateStats(calendarData.value)
    
    // 转换数据格式为ECharts需要的格式
    const data = Object.entries(calendarData.value).map(([date, count]) => [date, count])
    
    console.log(`✅ 加载 ${selectedYear.value} 年借阅数据：${data.length} 天`)
    initChart(data)
    initMonthChart(data)
    initWeekHeatmap(data)
  } catch (error) {
    console.error('❌ 加载借阅日历失败：', error)
    ElMessage.error('加载借阅日历失败')
  } finally {
    loading.value = false
  }
}

// GitHub风格日历热力图
const initChart = (data) => {
  if (!calendarChartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(calendarChartRef.value)
  }
  
  // GitHub配色方案
  const option = {
    tooltip: {
      formatter: function(params) {
        return `${params.data[0]}<br/>借阅 ${params.data[1]} 本`
      }
    },
    visualMap: {
      show: false,
      min: 0,
      max: 5,
      inRange: {
        color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
      }
    },
    calendar: {
      top: 20,
      left: 40,
      right: 20,
      bottom: 10,
      cellSize: ['auto', 13],
      range: selectedYear.value,
      itemStyle: {
        borderWidth: 3,
        borderColor: '#fff',
        borderRadius: 2
      },
      yearLabel: { 
        show: false 
      },
      dayLabel: {
        firstDay: 1,
        nameMap: ['日', '一', '二', '三', '四', '五', '六'],
        fontSize: 11,
        color: '#606266'
      },
      monthLabel: {
        show: true,
        nameMap: 'cn',
        fontSize: 12,
        color: '#303133',
        margin: 8
      },
      splitLine: {
        show: false
      }
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: data
    }]
  }
  
  chartInstance.setOption(option)
}

// 月度分布柱状图
const initMonthChart = (data) => {
  if (!monthChartRef.value) return
  
  if (!monthChart) {
    monthChart = echarts.init(monthChartRef.value)
  }
  
  // 按月统计
  const monthStats = {}
  data.forEach(([date, count]) => {
    const month = dayjs(date).month() + 1
    monthStats[month] = (monthStats[month] || 0) + count
  })
  
  const months = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
  const values = months.map((_, i) => monthStats[i + 1] || 0)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '8%',
      right: '4%',
      bottom: '12%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        interval: 0,
        rotate: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '借阅量'
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#67c23a' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      label: {
        show: true,
        position: 'top',
        color: '#303133'
      }
    }]
  }
  
  monthChart.setOption(option)
}

// 星期×小时热力图
const initWeekHeatmap = (data) => {
  if (!weekHeatmapRef.value) return
  
  if (!weekHeatmapChart) {
    weekHeatmapChart = echarts.init(weekHeatmapRef.value)
  }
  
  // 按星期统计
  const weekStats = Array(7).fill(0)
  data.forEach(([date, count]) => {
    const day = dayjs(date).day()
    const index = day === 0 ? 6 : day - 1
    weekStats[index] += count
  })
  
  const weekNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '8%',
      right: '4%',
      bottom: '8%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: weekNames
    },
    yAxis: {
      type: 'value',
      name: '借阅量'
    },
    series: [{
      type: 'bar',
      data: weekStats,
      itemStyle: {
        color: (params) => {
          const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452']
          return colors[params.dataIndex]
        },
        borderRadius: [4, 4, 0, 0]
      },
      label: {
        show: true,
        position: 'top',
        color: '#303133',
        fontWeight: 'bold'
      }
    }]
  }
  
  weekHeatmapChart.setOption(option)
}

onMounted(() => {
  loadCalendar()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
    monthChart?.resize()
    weekHeatmapChart?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
  monthChart?.dispose()
  weekHeatmapChart?.dispose()
})
</script>

<style scoped lang="scss">
.calendar-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }

    .header-controls {
      display: flex;
      gap: 10px;
    }
  }

  .stat-mini-card {
    text-align: center;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
      transform: translateY(-2px);
    }

    :deep(.el-statistic__head) {
      font-size: 13px;
      color: #909399;
    }

    :deep(.el-statistic__content) {
      font-size: 24px;
      font-weight: bold;
    }
  }
}
</style>

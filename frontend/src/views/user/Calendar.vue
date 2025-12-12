<template>
  <div class="calendar-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Calendar /></el-icon> 借阅日历</span>
          <el-date-picker
            v-model="selectedYear"
            type="year"
            placeholder="选择年份"
            @change="loadCalendar"
            format="YYYY"
            value-format="YYYY"
          />
        </div>
      </template>
      
      <div v-loading="loading">
        <div ref="calendarChartRef" style="width: 100%; height: 600px;"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getBorrowCalendar } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const calendarChartRef = ref(null)
const selectedYear = ref('2020')
let chartInstance = null

const loadCalendar = async () => {
  try {
    loading.value = true
    const userid = userStore.getUserId()
    const res = await getBorrowCalendar(userid, { yearMonth: selectedYear.value })
    
    // 转换数据格式为ECharts需要的格式
    const data = Object.entries(res.data).map(([date, count]) => [date, count])
    
    console.log(`✅ 加载 ${selectedYear.value} 年借阅数据：${data.length} 天`)
    initChart(data)
  } catch (error) {
    console.error('❌ 加载借阅日历失败：', error)
    ElMessage.error('加载借阅日历失败')
  } finally {
    loading.value = false
  }
}

const initChart = (data) => {
  if (!calendarChartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(calendarChartRef.value)
  }
  
  const option = {
    title: {
      text: `${selectedYear.value} 年借阅日历`,
      left: 'center'
    },
    tooltip: {
      formatter: function(params) {
        return `${params.data[0]}<br/>借阅次数：${params.data[1]}`
      }
    },
    visualMap: {
      min: 0,
      max: 10,
      type: 'piecewise',
      orient: 'horizontal',
      left: 'center',
      top: 50,
      pieces: [
        { min: 5, label: '5次及以上', color: '#c23531' },
        { min: 3, max: 4, label: '3-4次', color: '#e6a23c' },
        { min: 1, max: 2, label: '1-2次', color: '#91cc75' },
        { value: 0, label: '无借阅', color: '#f0f0f0' }
      ]
    },
    calendar: {
      top: 120,
      left: 50,
      right: 50,
      cellSize: ['auto', 13],
      range: selectedYear.value,
      itemStyle: {
        borderWidth: 0.5
      },
      yearLabel: { show: true },
      dayLabel: {
        firstDay: 1,
        nameMap: ['日', '一', '二', '三', '四', '五', '六']
      },
      monthLabel: {
        show: true,
        nameMap: 'cn'
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

onMounted(() => {
  loadCalendar()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<style scoped lang="scss">
.calendar-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
    }
  }
}
</style>

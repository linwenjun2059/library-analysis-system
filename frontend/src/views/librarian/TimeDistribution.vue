<template>
  <div class="time-distribution-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Clock /></el-icon> 时间分布分析</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab 1: 小时分布 -->
        <el-tab-pane label="⏰ 小时分布" name="hour">
          <el-empty v-if="hourData.length === 0" description="暂无小时分布数据" />
          <template v-else>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-card shadow="hover" style="margin-bottom: 20px;">
                  <template #header>
                    <span>24小时借还分布</span>
                  </template>
                  <div ref="hourChartRef" style="width: 100%; height: 400px;"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="24">
                <el-card shadow="hover">
                  <template #header>
                    <span>活跃用户数（按小时）</span>
                  </template>
                  <div ref="hourActiveChartRef" style="width: 100%; height: 350px;"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <!-- 建议提示 -->
            <el-alert 
              :title="`高峰时段: ${peakHour}时，建议增加值班人员`" 
              type="info" 
              show-icon 
              style="margin-top: 20px;"
              v-if="peakHour !== null"
            />
          </template>
        </el-tab-pane>
        
        <!-- Tab 2: 星期分布 -->
        <el-tab-pane label="📅 星期分布" name="weekday">
          <el-empty v-if="weekdayData.length === 0" description="暂无星期分布数据" />
          <template v-else>
            <el-card shadow="hover" style="margin-bottom: 20px;">
              <template #header>
                <span>星期几最忙碌？</span>
              </template>
              <div ref="weekdayChartRef" style="width: 100%; height: 450px;"></div>
            </el-card>
            
            <!-- 建议信息 -->
            <el-row :gutter="20">
              <el-col :span="12">
                <el-card shadow="hover">
                  <div style="text-align: center;">
                    <div style="font-size: 14px; color: #909399; margin-bottom: 8px;">最忙碌日</div>
                    <div style="font-size: 32px; font-weight: bold; color: #f56c6c;">
                      <el-icon style="vertical-align: middle;"><TrendCharts /></el-icon>
                      {{ peakWeekday || '-' }}
                    </div>
                    <div style="margin-top: 10px; font-size: 14px; color: #909399;">
                      建议增加值班人员
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card shadow="hover">
                  <div style="text-align: center;">
                    <div style="font-size: 14px; color: #909399; margin-bottom: 8px;">最清闲日</div>
                    <div style="font-size: 32px; font-weight: bold; color: #67c23a;">
                      <el-icon style="vertical-align: middle;"><Sunny /></el-icon>
                      {{ lowWeekday || '-' }}
                    </div>
                    <div style="margin-top: 10px; font-size: 14px; color: #909399;">
                      可安排设备维护
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </template>
        </el-tab-pane>
        
        <!-- Tab 3: 月份分布 -->
        <el-tab-pane label="📆 月份分布" name="month">
          <el-empty v-if="monthData.length === 0" description="暂无月份分布数据" />
          <template v-else>
            <el-card shadow="hover" style="margin-bottom: 20px;">
              <template #header>
                <span>月度借阅趋势</span>
              </template>
              <div ref="monthChartRef" style="width: 100%; height: 400px;"></div>
            </el-card>
            
            <!-- 季节性分析 -->
            <el-card shadow="hover">
              <template #header>
                <span>季节性分析</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="开学季（9-10月）">
                  <el-tag type="success">{{ fallSemesterBorrow }} 次借阅</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="期末季（12-1月）">
                  <el-tag type="warning">{{ winterExamBorrow }} 次借阅</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="春季学期（3-4月）">
                  <el-tag type="primary">{{ springSemesterBorrow }} 次借阅</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="暑期（7-8月）">
                  <el-tag type="info">{{ summerBorrow }} 次借阅</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </template>
        </el-tab-pane>
        
        <!-- Tab 4: 续借分析 -->
        <el-tab-pane label="🔄 续借分析" name="renew">
          <el-card shadow="hover" style="margin-bottom: 20px;">
            <template #header>
              <span>续借行为统计</span>
            </template>
            <el-row :gutter="20" v-if="renewAnalysis">
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="总借阅记录" :value="renewAnalysis.totalRecords || 0">
                  <template #prefix>
                    <el-icon color="#409eff"><Document /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="续借记录数" :value="renewAnalysis.renewRecords || 0">
                  <template #prefix>
                    <el-icon color="#67c23a"><Refresh /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic 
                  title="续借率" 
                  :value="(renewAnalysis.renewRate || 0) * 100" 
                  :precision="2"
                >
                  <template #prefix>
                    <el-icon color="#e6a23c"><TrendCharts /></el-icon>
                  </template>
                  <template #suffix>%</template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic 
                  title="平均续借次数" 
                  :value="renewAnalysis.avgRenewTimes || 0" 
                  :precision="2"
                >
                  <template #prefix>
                    <el-icon color="#909399"><DataAnalysis /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            <div ref="renewChartRef" style="width: 100%; height: 350px; margin-top: 20px;"></div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { getTimeDistribution, getRenewAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Clock, Refresh, Document, TrendCharts, DataAnalysis, Sunny } from '@element-plus/icons-vue'

const loading = ref(false)
const activeTab = ref('hour')

const hourChartRef = ref(null)
const hourActiveChartRef = ref(null)
const weekdayChartRef = ref(null)
const monthChartRef = ref(null)
const renewChartRef = ref(null)

let hourChart = null
let hourActiveChart = null
let weekdayChart = null
let monthChart = null
let renewChart = null

const timeData = ref([])
const renewAnalysis = ref(null)

// 分类后的数据
const hourData = computed(() => timeData.value.filter(item => item.timeType === '小时'))
const weekdayData = computed(() => timeData.value.filter(item => item.timeType === '星期'))
const monthData = computed(() => timeData.value.filter(item => item.timeType === '月份'))

// 高峰时段
const peakHour = computed(() => {
  if (hourData.value.length === 0) return null
  const peak = hourData.value.reduce((max, item) => 
    item.borrowCount > max.borrowCount ? item : max
  )
  return peak.timeValue
})

// 最忙碌/清闲的星期
const peakWeekday = computed(() => {
  if (weekdayData.value.length === 0) return null
  const peak = weekdayData.value.reduce((max, item) => 
    item.borrowCount > max.borrowCount ? item : max
  )
  const weekdayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return weekdayNames[peak.timeValue]
})

const lowWeekday = computed(() => {
  if (weekdayData.value.length === 0) return null
  const low = weekdayData.value.reduce((min, item) => 
    item.borrowCount < min.borrowCount ? item : min
  )
  const weekdayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return weekdayNames[low.timeValue]
})

// 季节性数据
const fallSemesterBorrow = computed(() => {
  return monthData.value
    .filter(item => item.timeValue >= 9 && item.timeValue <= 10)
    .reduce((sum, item) => sum + item.borrowCount, 0)
})

const winterExamBorrow = computed(() => {
  return monthData.value
    .filter(item => item.timeValue === 12 || item.timeValue === 1)
    .reduce((sum, item) => sum + item.borrowCount, 0)
})

const springSemesterBorrow = computed(() => {
  return monthData.value
    .filter(item => item.timeValue >= 3 && item.timeValue <= 4)
    .reduce((sum, item) => sum + item.borrowCount, 0)
})

const summerBorrow = computed(() => {
  return monthData.value
    .filter(item => item.timeValue >= 7 && item.timeValue <= 8)
    .reduce((sum, item) => sum + item.borrowCount, 0)
})

const loadData = async () => {
  try {
    loading.value = true
    console.log('🔄 加载时间分布数据...')
    
    const [timeRes, renewRes] = await Promise.all([
      getTimeDistribution(),
      getRenewAnalysis()
    ])
    
    timeData.value = timeRes.data || []
    renewAnalysis.value = renewRes.data || null
    
    console.log('📥 收到数据:', timeData.value.length, '条')
    
    if (timeData.value.length === 0) {
      console.warn('⚠️ 暂无时间分布数据')
      ElMessage.warning('暂无时间分布数据，请联系管理员确认数据是否已生成')
      loading.value = false
      return
    }
    
    console.log('📊 原始数据示例:', timeData.value.slice(0, 3))
    console.log('✅ 分类完成:', {
      小时数据: hourData.value.length,
      星期数据: weekdayData.value.length,
      月份数据: monthData.value.length
    })
    
    // 初始化图表 - 增加延迟确保DOM完全渲染
    await nextTick()
    setTimeout(() => {
      console.log('🎨 开始初始化图表，当前Tab:', activeTab.value)
      if (activeTab.value === 'hour') {
        initHourCharts()
      } else if (activeTab.value === 'weekday') {
        initWeekdayChart()
      } else if (activeTab.value === 'month') {
        initMonthChart()
      }
    }, 300)
    
    console.log('✅ 时间分布数据加载成功')
  } catch (error) {
    console.error('❌ 加载时间分布数据失败：', error)
    ElMessage.error('加载时间分布数据失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const initHourCharts = () => {
  initHourChart()
  initHourActiveChart()
}

const initHourChart = () => {
  console.log('📈 初始化小时图表...')
  console.log('  hourChartRef存在:', !!hourChartRef.value)
  console.log('  hourData长度:', hourData.value.length)
  
  if (!hourChartRef.value) {
    console.warn('⚠️ hourChartRef不存在')
    return
  }
  
  if (hourData.value.length === 0) {
    console.warn('⚠️ hourData为空')
    return
  }
  
  if (!hourChart) {
    hourChart = echarts.init(hourChartRef.value)
    console.log('✅ hourChart实例已创建')
  }
  
  const sorted = hourData.value.sort((a, b) => a.timeValue - b.timeValue)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['借阅量', '归还量']
    },
    xAxis: {
      type: 'category',
      data: sorted.map(item => `${item.timeValue}时`),
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series: [
      {
        name: '借阅量',
        type: 'line',
        data: sorted.map(item => item.borrowCount),
        smooth: true,
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      },
      {
        name: '归还量',
        type: 'line',
        data: sorted.map(item => item.returnCount),
        smooth: true,
        itemStyle: { color: '#67c23a' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ])
        }
      }
    ]
  }
  
  hourChart.setOption(option)
  console.log('✅ 小时图表配置已设置')
}

const initHourActiveChart = () => {
  console.log('📈 初始化小时活跃用户图表...')
  
  if (!hourActiveChartRef.value) {
    console.warn('⚠️ hourActiveChartRef不存在')
    return
  }
  
  if (hourData.value.length === 0) {
    console.warn('⚠️ hourData为空')
    return
  }
  
  if (!hourActiveChart) {
    hourActiveChart = echarts.init(hourActiveChartRef.value)
    console.log('✅ hourActiveChart实例已创建')
  }
  
  const sorted = hourData.value.sort((a, b) => a.timeValue - b.timeValue)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: sorted.map(item => `${item.timeValue}时`)
    },
    yAxis: {
      type: 'value',
      name: '活跃用户数'
    },
    series: [{
      name: '活跃用户数',
      type: 'bar',
      data: sorted.map(item => item.activeUserCount),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#ffd666' },
          { offset: 1, color: '#ffa940' }
        ])
      }
    }]
  }
  
  hourActiveChart.setOption(option)
}

const initWeekdayChart = () => {
  console.log('📈 初始化星期图表...')
  console.log('  weekdayData长度:', weekdayData.value.length)
  
  if (!weekdayChartRef.value) {
    console.warn('⚠️ weekdayChartRef不存在')
    return
  }
  
  if (weekdayData.value.length === 0) {
    console.warn('⚠️ weekdayData为空')
    return
  }
  
  if (!weekdayChart) {
    weekdayChart = echarts.init(weekdayChartRef.value)
    console.log('✅ weekdayChart实例已创建')
  }
  
  const sorted = weekdayData.value.sort((a, b) => a.timeValue - b.timeValue)
  const weekdayNames = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  const option = {
    title: { text: '星期借阅分布' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['借阅量', '归还量']
    },
    xAxis: {
      type: 'category',
      data: sorted.map(item => weekdayNames[item.timeValue])
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '借阅量',
        type: 'bar',
        data: sorted.map(item => item.borrowCount),
        itemStyle: { color: '#5470c6' }
      },
      {
        name: '归还量',
        type: 'bar',
        data: sorted.map(item => item.returnCount),
        itemStyle: { color: '#91cc75' }
      }
    ]
  }
  
  weekdayChart.setOption(option)
}

const initMonthChart = () => {
  console.log('📈 初始化月份图表...')
  console.log('  monthData长度:', monthData.value.length)
  
  if (!monthChartRef.value) {
    console.warn('⚠️ monthChartRef不存在')
    return
  }
  
  if (monthData.value.length === 0) {
    console.warn('⚠️ monthData为空')
    return
  }
  
  if (!monthChart) {
    monthChart = echarts.init(monthChartRef.value)
    console.log('✅ monthChart实例已创建')
  }
  
  const sorted = monthData.value.sort((a, b) => a.timeValue - b.timeValue)
  
  const option = {
    title: { text: '月度借阅趋势' },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['借阅量', '活跃用户数']
    },
    xAxis: {
      type: 'category',
      data: sorted.map(item => `${item.timeValue}月`)
    },
    yAxis: [
      {
        type: 'value',
        name: '借阅量',
        position: 'left'
      },
      {
        type: 'value',
        name: '活跃用户数',
        position: 'right'
      }
    ],
    series: [
      {
        name: '借阅量',
        type: 'line',
        data: sorted.map(item => item.borrowCount),
        smooth: true,
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '活跃用户数',
        type: 'line',
        yAxisIndex: 1,
        data: sorted.map(item => item.activeUserCount),
        smooth: true,
        itemStyle: { color: '#f56c6c' }
      }
    ]
  }
  
  monthChart.setOption(option)
}

const initRenewChart = () => {
  console.log('📈 初始化续借图表...')
  
  if (!renewChartRef.value || !renewAnalysis.value) {
    console.warn('⚠️ renewChartRef不存在或renewAnalysis为空')
    return
  }
  
  if (!renewChart) {
    renewChart = echarts.init(renewChartRef.value)
    console.log('✅ renewChart实例已创建')
  }
  
  const distribution = renewAnalysis.value.renewTimesDistribution || {}
  const categories = Object.keys(distribution).map(k => parseInt(k)).sort((a, b) => a - b)
  const values = categories.map(cat => distribution[cat])
  
  const option = {
    title: {
      text: '续借次数分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: categories.map(c => c + '次'),
      name: '续借次数'
    },
    yAxis: {
      type: 'value',
      name: '记录数'
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
      }
    }]
  }
  
  renewChart.setOption(option)
}

const handleTabChange = (tabName) => {
  console.log('🔄 Tab切换到:', tabName)
  nextTick(() => {
    setTimeout(() => {
      if (tabName === 'hour') {
        initHourCharts()
      } else if (tabName === 'weekday') {
        initWeekdayChart()
      } else if (tabName === 'month') {
        initMonthChart()
      } else if (tabName === 'renew') {
        initRenewChart()
      }
    }, 200)
  })
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    hourChart?.resize()
    hourActiveChart?.resize()
    weekdayChart?.resize()
    monthChart?.resize()
    renewChart?.resize()
  })
})

onUnmounted(() => {
  hourChart?.dispose()
  hourActiveChart?.dispose()
  weekdayChart?.dispose()
  monthChart?.dispose()
  renewChart?.dispose()
})
</script>

<style scoped lang="scss">
.time-distribution-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}
</style>

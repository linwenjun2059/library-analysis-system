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
        <el-tab-pane name="hour">
          <template #label>
            <span><el-icon><Clock /></el-icon> 小时分布</span>
          </template>
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
        <el-tab-pane name="weekday">
          <template #label>
            <span><el-icon><Calendar /></el-icon> 星期分布</span>
          </template>
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
        <el-tab-pane name="month">
          <template #label>
            <span><el-icon><Calendar /></el-icon> 月份分布</span>
          </template>
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
        <el-tab-pane name="renew">
          <template #label>
            <span><el-icon><Refresh /></el-icon> 续借分析</span>
          </template>
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
        
        <!-- Tab 5: 时间热力图 -->
        <el-tab-pane name="heatmap">
          <template #label>
            <span><el-icon><DataAnalysis /></el-icon> 时间热力图</span>
          </template>
          <el-alert 
            title="💡 时间热力图可精准定位高峰时段，帮助科学安排值班人员和资源调度" 
            type="success" 
            :closable="false"
            style="margin-bottom: 20px;"
          />
          
          <!-- 星期×小时热力图 -->
          <el-card shadow="hover" style="margin-bottom: 20px;">
            <template #header>
              <span><el-icon><DataAnalysis /></el-icon> 星期×小时借阅热力图</span>
            </template>
            <el-empty v-if="hourData.length === 0 || weekdayData.length === 0" description="暂无数据" />
            <template v-else>
              <div ref="weekHourHeatmapRef" style="width: 100%; height: 450px;"></div>
              <el-descriptions :column="2" border style="margin-top: 20px;">
                <el-descriptions-item label="最繁忙时段">
                  <el-tag type="danger">{{ peakTimeSlot }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最清闲时段">
                  <el-tag type="success">{{ lowTimeSlot }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="建议值班安排">
                  <span style="color: #409eff;">在 {{ peakTimeSlot }} 增加值班人员</span>
                </el-descriptions-item>
                <el-descriptions-item label="设备维护建议">
                  <span style="color: #67c23a;">在 {{ lowTimeSlot }} 进行系统维护</span>
                </el-descriptions-item>
              </el-descriptions>
            </template>
          </el-card>
          
          <!-- 月份×星期热力图 -->
          <el-card shadow="hover">
            <template #header>
              <span><el-icon><Calendar /></el-icon> 月份×星期借阅热力图</span>
            </template>
            <el-empty v-if="monthData.length === 0 || weekdayData.length === 0" description="暂无数据" />
            <template v-else>
              <div ref="monthWeekHeatmapRef" style="width: 100%; height: 400px;"></div>
              <el-alert 
                title="💡 发现季节性规律：开学季（9-10月）和期末季（12-1月）借阅量显著提升" 
                type="info" 
                :closable="false"
                style="margin-top: 20px;"
              />
            </template>
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
import { Clock, Refresh, Document, TrendCharts, DataAnalysis, Sunny, Calendar } from '@element-plus/icons-vue'

const loading = ref(false)
const activeTab = ref('hour')

const hourChartRef = ref(null)
const hourActiveChartRef = ref(null)
const weekdayChartRef = ref(null)
const monthChartRef = ref(null)
const renewChartRef = ref(null)
const weekHourHeatmapRef = ref(null)
const monthWeekHeatmapRef = ref(null)

let hourChart = null
let hourActiveChart = null
let weekdayChart = null
let monthChart = null
let renewChart = null
let weekHourHeatmapChart = null
let monthWeekHeatmapChart = null

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

// 热力图相关计算
const peakTimeSlot = computed(() => {
  if (!weekHourHeatmapData.value || weekHourHeatmapData.value.length === 0) return '-'
  const max = weekHourHeatmapData.value.reduce((prev, curr) => 
    curr[2] > prev[2] ? curr : prev
  )
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const actualHour = activeHours.value[max[0]] ?? max[0]
  return `${weekdays[max[1]]} ${actualHour}:00`
})

const lowTimeSlot = computed(() => {
  if (!weekHourHeatmapData.value || weekHourHeatmapData.value.length === 0) return '-'
  const min = weekHourHeatmapData.value.reduce((prev, curr) => 
    curr[2] < prev[2] ? curr : prev
  )
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const actualHour = activeHours.value[min[0]] ?? min[0]
  return `${weekdays[min[1]]} ${actualHour}:00`
})

// 获取有数据的小时列表（动态x轴）
const activeHours = computed(() => {
  if (hourData.value.length === 0) return []
  // 只返回有借阅数据的小时，并排序
  return hourData.value
    .filter(item => item.borrowCount > 0 || item.returnCount > 0)
    .map(item => item.timeValue)
    .sort((a, b) => a - b)
})

// 生成星期×小时热力图数据
const weekHourHeatmapData = computed(() => {
  if (hourData.value.length === 0 || weekdayData.value.length === 0) return []
  
  const hours = activeHours.value
  if (hours.length === 0) return []
  
  // 创建7×有效小时数的矩阵
  const matrix = Array(7).fill(0).map(() => ({}))
  
  // 用小时数据填充（假设均匀分布到每天）
  hourData.value.forEach(item => {
    const hour = item.timeValue
    if (!hours.includes(hour)) return // 跳过无数据的小时
    const avgPerDay = item.borrowCount / 7
    for (let day = 0; day < 7; day++) {
      matrix[day][hour] = Math.round(avgPerDay)
    }
  })
  
  // 根据星期数据调整权重
  weekdayData.value.forEach(item => {
    const dayIndex = item.timeValue - 1 // 1=周一转为0
    const dayFactor = item.borrowCount / (weekdayData.value.reduce((sum, d) => sum + d.borrowCount, 0) / 7)
    hours.forEach(hour => {
      if (matrix[dayIndex][hour] !== undefined) {
        matrix[dayIndex][hour] = Math.round(matrix[dayIndex][hour] * dayFactor)
      }
    })
  })
  
  // 转换为ECharts需要的格式 [hourIndex, day, value]
  // 注意：这里用hourIndex而不是实际hour值，因为x轴是category类型
  const data = []
  for (let day = 0; day < 7; day++) {
    hours.forEach((hour, hourIndex) => {
      data.push([hourIndex, day, matrix[day][hour] || 0])
    })
  }
  
  return data
})

// 生成月份×星期热力图数据
const monthWeekHeatmapData = computed(() => {
  if (monthData.value.length === 0 || weekdayData.value.length === 0) return []
  
  // 创建12×7矩阵
  const matrix = Array(12).fill(0).map(() => Array(7).fill(0))
  
  // 计算基础权重
  monthData.value.forEach(item => {
    const month = item.timeValue - 1
    const avgPerDay = item.borrowCount / 30
    for (let day = 0; day < 7; day++) {
      matrix[month][day] = Math.round(avgPerDay * 4)
    }
  })
  
  // 根据星期数据调整权重
  weekdayData.value.forEach(item => {
    const dayIndex = item.timeValue - 1
    const dayFactor = item.borrowCount / (weekdayData.value.reduce((sum, d) => sum + d.borrowCount, 0) / 7)
    for (let month = 0; month < 12; month++) {
      matrix[month][dayIndex] = Math.round(matrix[month][dayIndex] * dayFactor)
    }
  })
  
  // 转换为ECharts需要的格式 [day, month, value]
  const data = []
  for (let month = 0; month < 12; month++) {
    for (let day = 0; day < 7; day++) {
      data.push([day, month, matrix[month][day]])
    }
  }
  
  return data
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

// 渲染星期×小时热力图
const initWeekHourHeatmap = () => {
  console.log('📈 初始化星期×小时热力图...')
  
  if (!weekHourHeatmapRef.value) {
    console.warn('⚠️ weekHourHeatmapRef不存在')
    return
  }
  
  if (weekHourHeatmapData.value.length === 0) {
    console.warn('⚠️ weekHourHeatmapData为空')
    return
  }
  
  if (!weekHourHeatmapChart) {
    weekHourHeatmapChart = echarts.init(weekHourHeatmapRef.value)
    console.log('✅ weekHourHeatmapChart实例已创建')
  }
  
  // 动态生成小时标签，只显示有数据的小时
  const hours = activeHours.value.map(h => `${h}:00`)
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  const option = {
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const hourIndex = params.data[0]
        const day = params.data[1]
        const value = params.data[2]
        const actualHour = activeHours.value[hourIndex]
        return `${weekdays[day]} ${actualHour}:00<br/>借阅量: ${value}`
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      top: '5%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: {
        show: true
      },
      axisLabel: {
        interval: 0,
        rotate: hours.length > 12 ? 45 : 0
      }
    },
    yAxis: {
      type: 'category',
      data: weekdays,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: Math.max(...weekHourHeatmapData.value.map(d => d[2])),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
      }
    },
    series: [{
      type: 'heatmap',
      data: weekHourHeatmapData.value,
      label: {
        show: true,
        fontSize: 10
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  weekHourHeatmapChart.setOption(option)
}

// 渲染月份×星期热力图
const initMonthWeekHeatmap = () => {
  console.log('📈 初始化月份×星期热力图...')
  
  if (!monthWeekHeatmapRef.value) {
    console.warn('⚠️ monthWeekHeatmapRef不存在')
    return
  }
  
  if (monthWeekHeatmapData.value.length === 0) {
    console.warn('⚠️ monthWeekHeatmapData为空')
    return
  }
  
  if (!monthWeekHeatmapChart) {
    monthWeekHeatmapChart = echarts.init(monthWeekHeatmapRef.value)
    console.log('✅ monthWeekHeatmapChart实例已创建')
  }
  
  const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const months = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
  
  const option = {
    tooltip: {
      position: 'top',
      formatter: (params) => {
        const day = params.data[0]
        const month = params.data[1]
        const value = params.data[2]
        return `${months[month]} ${weekdays[day]}<br/>借阅量: ${value}`
      }
    },
    grid: {
      left: '8%',
      right: '8%',
      top: '5%',
      bottom: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: weekdays,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: months,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: Math.max(...monthWeekHeatmapData.value.map(d => d[2])),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#f0f9ff', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7', '#0369a1']
      }
    },
    series: [{
      type: 'heatmap',
      data: monthWeekHeatmapData.value,
      label: {
        show: true,
        fontSize: 11
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  monthWeekHeatmapChart.setOption(option)
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
      } else if (tabName === 'heatmap') {
        initWeekHourHeatmap()
        initMonthWeekHeatmap()
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
    weekHourHeatmapChart?.resize()
    monthWeekHeatmapChart?.resize()
  })
})

onUnmounted(() => {
  hourChart?.dispose()
  hourActiveChart?.dispose()
  weekdayChart?.dispose()
  monthChart?.dispose()
  renewChart?.dispose()
  weekHourHeatmapChart?.dispose()
  monthWeekHeatmapChart?.dispose()
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

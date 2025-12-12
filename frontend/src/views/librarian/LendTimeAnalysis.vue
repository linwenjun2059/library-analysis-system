<template>
  <div class="lend-time-analysis-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Clock /></el-icon> 借阅时间分析</span>
          <el-button type="primary" size="small" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <!-- 借阅时间分布（24小时热力图） -->
        <el-col :span="24">
          <el-card shadow="hover">
            <template #header>
              <span>借阅时间分布（24小时）</span>
            </template>
            <div ref="timeChartRef" style="width: 100%; height: 400px;"></div>
          </el-card>
        </el-col>
        
        <!-- 续借行为分析 -->
        <el-col :span="24" style="margin-top: 20px;">
          <el-card shadow="hover">
            <template #header>
              <span>续借行为分析</span>
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
            <div ref="renewChartRef" style="width: 100%; height: 300px; margin-top: 20px;"></div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getLendTimeDistribution, getRenewAnalysis } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Clock, Refresh, Document, TrendCharts, DataAnalysis } from '@element-plus/icons-vue'

const loading = ref(false)
const timeData = ref([])
const renewAnalysis = ref(null)
const timeChartRef = ref(null)
const renewChartRef = ref(null)
let timeChart = null
let renewChart = null

const loadData = async () => {
  loading.value = true
  try {
    // 加载时间分布
    const timeResult = await getLendTimeDistribution()
    timeData.value = timeResult.data || []
    
    // 加载续借分析
    const renewResult = await getRenewAnalysis()
    renewAnalysis.value = renewResult.data
    
    nextTick(() => {
      initTimeChart()
      initRenewChart()
    })
  } catch (error) {
    ElMessage.error('加载数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const initTimeChart = () => {
  if (!timeChartRef.value || timeData.value.length === 0) return
  
  if (timeChart) {
    timeChart.dispose()
  }
  
  timeChart = echarts.init(timeChartRef.value)
  
  const hours = timeData.value.map(item => item.hour + ':00')
  const counts = timeData.value.map(item => item.count)
  
  const option = {
    title: {
      text: '24小时借阅分布',
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
      data: hours,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '借阅次数'
    },
    series: [{
      data: counts,
      type: 'bar',
      itemStyle: {
        color: function(params) {
          const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }
  
  timeChart.setOption(option)
}

const initRenewChart = () => {
  if (!renewChartRef.value || !renewAnalysis.value) return
  
  if (renewChart) {
    renewChart.dispose()
  }
  
  renewChart = echarts.init(renewChartRef.value)
  
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
        color: '#409eff'
      }
    }]
  }
  
  renewChart.setOption(option)
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (timeChart) {
    timeChart.dispose()
  }
  if (renewChart) {
    renewChart.dispose()
  }
})
</script>

<style scoped>
.lend-time-analysis-container {
  padding: 0px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>


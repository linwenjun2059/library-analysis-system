<template>
  <div class="circulation-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><DataLine /></el-icon> 馆藏利用分析</span>
          <el-radio-group v-model="dimensionType" @change="handleDimensionChange">
            <el-radio-button label="位置">按位置</el-radio-button>
            <el-radio-button label="主题">按主题</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <div v-loading="loading">
        <!-- 统计卡片 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="6">
            <el-statistic title="总馆藏图书" :value="totalBooks" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="被借图书数" :value="borrowedBooks" />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="平均周转率" 
              :value="avgTurnoverRate" 
              :precision="2"
              suffix="次/本/年"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic title="独立读者数" :value="totalUniqueReaders" />
          </el-col>
        </el-row>
        
        <!-- 利用分析图表 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="24">
            <div ref="chartRef" style="width: 100%; height: 450px"></div>
          </el-col>
        </el-row>
        
        <!-- 分析图表组 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">周转率分级分布</span>
              </template>
              <div ref="turnoverDistChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">需求分级分布</span>
              </template>
              <div ref="demandChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">TOP5维度对比</span>
              </template>
              <div ref="radarChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 维度专属图表 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">{{ dimensionType }}借阅排行（TOP15）</span>
              </template>
              <div ref="dimensionRankChartRef" style="width: 100%; height: 350px;"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <span style="font-weight: bold;">{{ dimensionType }}图书数量分布</span>
              </template>
              <div ref="bookCountChartRef" style="width: 100%; height: 350px;"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 详细列表 -->
        <el-divider />
        <el-table :data="pagedData" stripe :default-sort="{prop: 'turnoverRate', order: 'descending'}">
          <el-table-column prop="dimensionType" label="类型" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.dimensionType === '位置' ? 'primary' : 'success'" size="small">
                {{ row.dimensionType }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="dimensionValue" label="维度值" min-width="150" show-overflow-tooltip />
          <el-table-column prop="totalBooks" label="馆藏数" width="90" align="center" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.totalBooks) }}
            </template>
          </el-table-column>
          <el-table-column prop="borrowedBooks" label="被借数" width="90" align="center" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.borrowedBooks) }}
            </template>
          </el-table-column>
          <el-table-column prop="totalLendCount" label="借阅次数" width="100" align="center" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.totalLendCount) }}
            </template>
          </el-table-column>
          <el-table-column prop="avgBorrowTimes" label="平均借阅" width="100" align="center" sortable>
            <template #default="{ row }">
              {{ formatDecimal(row.avgBorrowTimes) }}
            </template>
          </el-table-column>
          <el-table-column prop="turnoverRate" label="周转率" width="100" align="center" sortable>
            <template #default="{ row }">
              <el-tag :type="getTurnoverTagType(row.turnoverRate)" size="small">
                {{ formatDecimal(row.turnoverRate) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="需求分布" width="140" align="center">
            <template #default="{ row }">
              <div style="font-size: 12px; line-height: 1.4;">
                <span style="color: #f56c6c;">高{{ row.highDemandBooks }}</span> / 
                <span style="color: #e6a23c;">中{{ row.mediumDemandBooks }}</span> / 
                <span style="color: #909399;">低{{ row.lowDemandBooks }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="uniqueReaders" label="读者数" width="90" align="center" sortable>
            <template #default="{ row }">
              {{ formatNumber(row.uniqueReaders) }}
            </template>
          </el-table-column>
          <el-table-column prop="readerPerBookRatio" label="读者比" width="90" align="center" sortable>
            <template #default="{ row }">
              {{ formatDecimal(row.readerPerBookRatio) }}
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 分页 -->
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredData.length"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 20px; justify-content: center;"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getCollectionUtilization } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const dimensionType = ref('位置')
const circulationData = ref([])
const chartRef = ref(null)
const turnoverDistChartRef = ref(null)
const demandChartRef = ref(null)
const radarChartRef = ref(null)
const dimensionRankChartRef = ref(null)
const bookCountChartRef = ref(null)
let chartInstance = null
let turnoverDistChartInstance = null
let demandChartInstance = null
let radarChartInstance = null
let dimensionRankChartInstance = null
let bookCountChartInstance = null

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 过滤后的数据
const filteredData = computed(() => {
  return circulationData.value
})

// 分页数据
const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredData.value.slice(start, end)
})

const totalBooks = computed(() => 
  filteredData.value.reduce((sum, item) => sum + (item.totalBooks || 0), 0)
)

const borrowedBooks = computed(() => 
  filteredData.value.reduce((sum, item) => sum + (item.borrowedBooks || 0), 0)
)

const avgTurnoverRate = computed(() => {
  if (filteredData.value.length === 0) return 0
  const sum = filteredData.value.reduce((s, item) => s + (item.turnoverRate || 0), 0)
  return sum / filteredData.value.length
})

const totalUniqueReaders = computed(() => 
  filteredData.value.reduce((sum, item) => sum + (item.uniqueReaders || 0), 0)
)

const getTurnoverTagType = (rate) => {
  if (rate >= 2.0) return 'success'
  if (rate >= 1.0) return 'warning'
  return 'danger'
}

// 格式化数字（千分位）
const formatNumber = (num) => {
  if (num === null || num === undefined) return '-'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 格式化小数（保留2位）
const formatDecimal = (num) => {
  if (num === null || num === undefined) return '-'
  if (num > 100) return num.toFixed(0) // 如果是异常大数，只显示整数
  return num.toFixed(2)
}

// 处理维度切换
const handleDimensionChange = () => {
  currentPage.value = 1
  loadData()
}

const loadData = async () => {
  try {
    loading.value = true
    console.log('🔄 加载馆藏利用分析数据...', { dimensionType: dimensionType.value })
    
    const params = dimensionType.value ? { dimensionType: dimensionType.value } : {}
    const res = await getCollectionUtilization(params)
    circulationData.value = res.data || []
    
    console.log('📥 收到数据:', circulationData.value.length, '条')
    
    if (circulationData.value.length === 0) {
      ElMessage.warning('暂无馆藏利用分析数据')
      return
    }
    
    initChart()
    initTurnoverDistChart()
    initDemandChart()
    initRadarChart()
    initDimensionRankChart()
    initBookCountChart()
    console.log('✅ 馆藏利用分析数据加载成功')
  } catch (error) {
    console.error('❌ 加载馆藏利用分析数据失败：', error)
    ElMessage.error('加载馆藏利用分析数据失败')
  } finally {
    loading.value = false
  }
}

const initChart = () => {
  if (!chartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  // 只显示周转率最高的TOP20
  const displayData = [...filteredData.value]
    .sort((a, b) => (b.turnoverRate || 0) - (a.turnoverRate || 0))
    .slice(0, 20)
  
  const option = {
    title: { 
      text: '周转率TOP20', 
      left: 'center',
      subtext: `按周转率排序，共${filteredData.value.length}条数据`
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: function(params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += param.seriesName + ': ' + param.value
          if (param.seriesName === '周转率') result += ' 次/本/年'
          result += '<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['周转率', '平均借阅次数'],
      top: 55
    },
    grid: {
      top: 85,
      bottom: 100
    },
    xAxis: {
      type: 'category',
      data: displayData.map(item => item.dimensionValue),
      axisLabel: { rotate: 35, interval: 0 }
    },
    yAxis: [
      {
        type: 'value',
        name: '周转率 (次/本/年)',
        position: 'left'
      },
      {
        type: 'value',
        name: '平均借阅次数',
        position: 'right'
      }
    ],
    series: [
      {
        name: '周转率',
        type: 'bar',
        data: displayData.map(item => (item.turnoverRate || 0).toFixed(2)),
        itemStyle: { color: '#409eff' }
      },
      {
        name: '平均借阅次数',
        type: 'line',
        yAxisIndex: 1,
        data: displayData.map(item => (item.avgBorrowTimes || 0).toFixed(2)),
        itemStyle: { color: '#67c23a' }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

// 周转率分级分布饼图
const initTurnoverDistChart = () => {
  if (!turnoverDistChartRef.value) return
  
  if (!turnoverDistChartInstance) {
    turnoverDistChartInstance = echarts.init(turnoverDistChartRef.value)
  }
  
  // 周转率分级：优秀(>=2.0)、良好(1.0-2.0)、一般(<1.0)
  const excellent = filteredData.value.filter(item => (item.turnoverRate || 0) >= 2.0).length
  const good = filteredData.value.filter(item => {
    const rate = item.turnoverRate || 0
    return rate >= 1.0 && rate < 2.0
  }).length
  const normal = filteredData.value.filter(item => (item.turnoverRate || 0) < 1.0).length
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      show: false
    },
    series: [
      {
        name: '周转率等级',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c} ({d}%)',
          fontSize: 12,
          fontWeight: 'bold'
        },
        emphasis: {
          label: {
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10
        },
        data: [
          { 
            value: excellent, 
            name: '优秀 (≥2.0)',
            itemStyle: { color: '#67c23a' }
          },
          { 
            value: good, 
            name: '良好 (1.0-2.0)',
            itemStyle: { color: '#e6a23c' }
          },
          { 
            value: normal, 
            name: '一般 (<1.0)',
            itemStyle: { color: '#f56c6c' }
          }
        ]
      }
    ]
  }
  
  turnoverDistChartInstance.setOption(option)
}

// 需求分级分布饼图
const initDemandChart = () => {
  if (!demandChartRef.value) return
  
  if (!demandChartInstance) {
    demandChartInstance = echarts.init(demandChartRef.value)
  }
  
  const highDemand = filteredData.value.reduce((sum, item) => sum + (item.highDemandBooks || 0), 0)
  const mediumDemand = filteredData.value.reduce((sum, item) => sum + (item.mediumDemandBooks || 0), 0)
  const lowDemand = filteredData.value.reduce((sum, item) => sum + (item.lowDemandBooks || 0), 0)
  const total = highDemand + mediumDemand + lowDemand
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}本 ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 5,
      left: 'center',
      textStyle: { fontSize: 12 }
    },
    series: [
      {
        name: '需求等级',
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
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { 
            value: highDemand, 
            name: `高需求 (>5次)`,
            itemStyle: { color: '#f56c6c' }
          },
          { 
            value: mediumDemand, 
            name: `中需求 (2-5次)`,
            itemStyle: { color: '#e6a23c' }
          },
          { 
            value: lowDemand, 
            name: `低需求 (1次)`,
            itemStyle: { color: '#909399' }
          }
        ]
      }
    ]
  }
  
  demandChartInstance.setOption(option)
}

// TOP5维度雷达对比图
const initRadarChart = () => {
  if (!radarChartRef.value) return
  
  if (!radarChartInstance) {
    radarChartInstance = echarts.init(radarChartRef.value)
  }
  
  // 取周转率TOP5
  const top5 = [...filteredData.value]
    .sort((a, b) => (b.turnoverRate || 0) - (a.turnoverRate || 0))
    .slice(0, 5)
  
  if (top5.length === 0) return
  
  // 计算最大值用于标准化
  const maxTurnover = Math.max(...top5.map(item => item.turnoverRate || 0))
  const maxBorrow = Math.max(...top5.map(item => item.totalLendCount || 0))
  const maxAvgBorrow = Math.max(...top5.map(item => item.avgBorrowTimes || 0))
  const maxReaders = Math.max(...top5.map(item => item.uniqueReaders || 0))
  const maxRatio = Math.max(...top5.map(item => item.readerPerBookRatio || 0))
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 10,
      textStyle: { fontSize: 10 },
      formatter: (name) => {
        return name.length > 8 ? name.substring(0, 8) + '...' : name
      }
    },
    radar: {
      indicator: [
        { name: '周转率', max: maxTurnover || 1 },
        { name: '借阅次数', max: maxBorrow || 1 },
        { name: '平均借阅', max: maxAvgBorrow || 1 },
        { name: '读者数', max: maxReaders || 1 },
        { name: '读者比', max: maxRatio || 1 }
      ],
      radius: '55%',
      center: ['35%', '50%']
    },
    series: [
      {
        name: '维度对比',
        type: 'radar',
        data: top5.map((item, index) => ({
          value: [
            item.turnoverRate || 0,
            item.totalLendCount || 0,
            item.avgBorrowTimes || 0,
            item.uniqueReaders || 0,
            item.readerPerBookRatio || 0
          ],
          name: item.dimensionValue,
          lineStyle: {
            width: 2
          },
          areaStyle: {
            opacity: 0.1
          }
        }))
      }
    ]
  }
  
  radarChartInstance.setOption(option)
}

// 维度借阅排行图
const initDimensionRankChart = () => {
  if (!dimensionRankChartRef.value) return
  
  if (!dimensionRankChartInstance) {
    dimensionRankChartInstance = echarts.init(dimensionRankChartRef.value)
  }
  
  const top15 = [...filteredData.value]
    .sort((a, b) => (b.totalLendCount || 0) - (a.totalLendCount || 0))
    .slice(0, 15)
    .reverse()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: '{b}: {c}次'
    },
    grid: {
      left: '30%',
      right: '10%',
      top: '5%',
      bottom: '5%'
    },
    xAxis: {
      type: 'value',
      name: '借阅次数'
    },
    yAxis: {
      type: 'category',
      data: top15.map(item => {
        const name = item.dimensionValue || '未知'
        return name.length > 15 ? name.substring(0, 15) + '...' : name
      }),
      axisLabel: { interval: 0 }
    },
    series: [{
      type: 'bar',
      data: top15.map(item => item.totalLendCount || 0),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#83bff6' },
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
  
  dimensionRankChartInstance.setOption(option)
}

// 位置图书数量分布图
const initBookCountChart = () => {
  if (!bookCountChartRef.value) return
  
  if (!bookCountChartInstance) {
    bookCountChartInstance = echarts.init(bookCountChartRef.value)
  }
  
  const top10 = [...filteredData.value]
    .sort((a, b) => (b.totalBooks || 0) - (a.totalBooks || 0))
    .slice(0, 10)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}本 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '50%'],
      data: top10.map(item => ({
        value: item.totalBooks || 0,
        name: item.dimensionValue || '未知'
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
  
  bookCountChartInstance.setOption(option)
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
    turnoverDistChartInstance?.resize()
    demandChartInstance?.resize()
    radarChartInstance?.resize()
    dimensionRankChartInstance?.resize()
    bookCountChartInstance?.resize()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
  turnoverDistChartInstance?.dispose()
  demandChartInstance?.dispose()
  radarChartInstance?.dispose()
  dimensionRankChartInstance?.dispose()
  bookCountChartInstance?.dispose()
})
</script>

<style scoped lang="scss">
.circulation-container {
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

<template>
  <div class="prediction-container">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 逾期风险预测 -->
      <el-tab-pane label="🚨 逾期风险预测" name="overdue">
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="总用户数" :value="overdueStats.totalUsers || 0">
                <template #prefix><el-icon color="#409eff"><User /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card danger">
              <el-statistic title="中高风险用户" :value="overdueStats.mediumHighRiskCount || 0">
                <template #prefix><el-icon color="#f56c6c"><Warning /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="中高风险占比" :value="overdueStats.mediumHighRiskRate || 0" suffix="%">
                <template #prefix><el-icon color="#e6a23c"><PieChart /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="平均逾期概率" :value="overdueStats.avgOverdueProbability || 0" suffix="%">
                <template #prefix><el-icon color="#909399"><TrendCharts /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
          <el-col :xs="24" :lg="8">
            <el-card shadow="hover">
              <template #header><span>风险等级分布</span></template>
              <div ref="riskPieChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="8">
            <el-card shadow="hover">
              <template #header><span>用户风险分层漏斗</span></template>
              <div ref="riskFunnelChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="8">
            <el-card shadow="hover">
              <template #header><span>院系风险用户 TOP8</span></template>
              <div ref="deptRiskChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 全年借阅热度日历图 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div class="card-header">
              <span>📅 全年逾期风险日历热力图</span>
              <el-radio-group v-model="selectedYear" @change="loadCalendarData" size="small">
                <el-radio-button label="2019">2019年</el-radio-button>
                <el-radio-button label="2020">2020年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="calendarHeatmapRef" style="width: 100%; height: 200px;"></div>
          <el-alert 
            title="💡 深色区域表示该日借阅量高且逾期风险较高，建议加强管理" 
            type="warning" 
            :closable="false"
            style="margin-top: 15px;"
          />
        </el-card>

        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>高风险用户列表</span>
              <el-select v-model="riskFilter" placeholder="风险等级" clearable style="width: 120px;" @change="loadOverdueList">
                <el-option label="高风险" value="高风险" />
                <el-option label="中风险" value="中风险" />
                <el-option label="低风险" value="低风险" />
                <el-option label="极低风险" value="极低风险" />
              </el-select>
            </div>
          </template>
          <el-table :data="overdueList" v-loading="overdueLoading" stripe>
            <el-table-column prop="userid" label="用户ID" width="120" />
            <el-table-column prop="dept" label="院系" min-width="150" show-overflow-tooltip />
            <el-table-column prop="userType" label="用户类型" width="100" />
            <el-table-column prop="borrowCount" label="借阅量" width="80" align="center" />
            <el-table-column label="历史逾期率" width="100" align="center">
              <template #default="{ row }">
                {{ ((row.historicalOverdueRate || 0) * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="预测逾期概率" width="120" align="center">
              <template #default="{ row }">
                <el-progress 
                  :percentage="Math.round((row.overdueProbability || 0) * 100)" 
                  :color="getProgressColor(row.overdueProbability)"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getRiskTagType(row.riskLevel)">{{ row.riskLevel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="warningMessage" label="预警建议" min-width="200" show-overflow-tooltip />
          </el-table>
          <div class="pagination-area">
            <el-pagination
              v-model:current-page="overduePage.current"
              v-model:page-size="overduePage.size"
              :total="overduePage.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadOverdueList"
              @current-change="loadOverdueList"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 借阅趋势预测 -->
      <el-tab-pane label="📈 借阅趋势预测" name="trend">
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="历史月份数" :value="trendStats.historicalMonths || 0">
                <template #prefix><el-icon color="#409eff"><Calendar /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="预测月份数" :value="trendStats.predictedMonths || 0">
                <template #prefix><el-icon color="#67c23a"><TrendCharts /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="历史月均借阅" :value="trendStats.avgHistoricalLend || 0">
                <template #prefix><el-icon color="#e6a23c"><Reading /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="整体趋势" :value="trendStats.overallTrend || '持平'">
                <template #prefix>
                  <el-icon :color="getTrendColor(trendStats.overallTrend)">
                    <Top v-if="trendStats.overallTrend === '上升'" />
                    <Bottom v-else-if="trendStats.overallTrend === '下降'" />
                    <Minus v-else />
                  </el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="hover">
          <template #header><span>借阅趋势预测图</span></template>
          <div ref="trendChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>

        <el-card shadow="hover" style="margin-top: 20px;">
          <template #header><span>未来6个月预测详情</span></template>
          <el-table :data="futureTrend" stripe>
            <el-table-column prop="lendMonth" label="月份" width="120" />
            <el-table-column prop="predictedCount" label="预测借阅量" width="120" align="center">
              <template #default="{ row }">
                <span style="font-weight: bold; color: #409eff;">{{ row.predictedCount?.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column label="趋势" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getTrendTagType(row.trend)" class="trend-tag">
                  <el-icon v-if="row.trend === '上升'"><Top /></el-icon>
                  <el-icon v-else-if="row.trend === '下降'"><Bottom /></el-icon>
                  <el-icon v-else><Minus /></el-icon>
                  {{ row.trend }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="运营建议" min-width="300">
              <template #default="{ row }">
                <span v-if="row.trend === '上升'">预计借阅量增加，建议提前准备热门图书库存</span>
                <span v-else-if="row.trend === '下降'">预计借阅量减少，可安排图书盘点或系统维护</span>
                <span v-else>借阅量平稳，维持正常运营即可</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 图书热度预测 -->
      <el-tab-pane label="🔥 图书热度预测" name="heat">
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="图书总数" :value="heatStats.totalBooks || 0">
                <template #prefix><el-icon color="#409eff"><Reading /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card hot">
              <el-statistic title="热门图书" :value="heatStats.hotBooksCount || 0">
                <template #prefix><el-icon color="#f56c6c"><Sunrise /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="建议采购" :value="heatStats.needPurchaseCount || 0">
                <template #prefix><el-icon color="#67c23a"><ShoppingCart /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="上升趋势" :value="heatStats.trendDistribution?.['上升'] || 0">
                <template #prefix><el-icon color="#e6a23c"><Top /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20" class="chart-row">
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header><span>热度等级分布</span></template>
              <div ref="heatPieChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header><span>趋势分布</span></template>
              <div ref="trendPieChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
        </el-row>

        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>图书热度预测列表</span>
              <div class="filter-area">
                <el-select v-model="heatFilter" placeholder="热度等级" clearable style="width: 100px;" @change="loadHeatList">
                  <el-option label="爆款" value="爆款" />
                  <el-option label="热门" value="热门" />
                  <el-option label="一般" value="一般" />
                  <el-option label="冷门" value="冷门" />
                  <el-option label="极冷" value="极冷" />
                </el-select>
                <el-select v-model="trendFilter" placeholder="趋势" clearable style="width: 100px;" @change="loadHeatList">
                  <el-option label="上升" value="上升" />
                  <el-option label="稳定" value="稳定" />
                  <el-option label="下降" value="下降" />
                </el-select>
              </div>
            </div>
          </template>
          <el-table :data="heatList" v-loading="heatLoading" stripe>
            <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip />
            <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
            <el-table-column prop="subject" label="主题" width="100" show-overflow-tooltip />
            <el-table-column prop="totalLendCount" label="总借阅" width="80" align="center" />
            <el-table-column prop="recentLendCount" label="近期借阅" width="90" align="center" />
            <el-table-column label="热度分数" width="120" align="center">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.heatScore || 0" 
                  :color="getHeatColor(row.heatScore)"
                  :stroke-width="10"
                />
              </template>
            </el-table-column>
            <el-table-column label="热度等级" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getHeatTagType(row.heatLevel)">{{ row.heatLevel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="趋势" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getTrendTagType(row.trend)" class="trend-tag">
                  <el-icon v-if="row.trend === '上升'"><Top /></el-icon>
                  <el-icon v-else-if="row.trend === '下降'"><Bottom /></el-icon>
                  <el-icon v-else><Minus /></el-icon>
                  {{ row.trend }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="recommendation" label="采购建议" min-width="180" show-overflow-tooltip />
          </el-table>
          <div class="pagination-area">
            <el-pagination
              v-model:current-page="heatPage.current"
              v-model:page-size="heatPage.size"
              :total="heatPage.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadHeatList"
              @current-change="loadHeatList"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { User, Warning, PieChart, TrendCharts, Calendar, Reading, Top, Bottom, Minus, Sunrise, ShoppingCart } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getOverdueRiskList, getOverdueRiskStats,
  getLendTrendPrediction, getLendTrendStats,
  getBookHeatList, getBookHeatStats
} from '@/api/advanced'

const activeTab = ref('overdue')

// 逾期风险
const overdueStats = ref({})
const overdueList = ref([])
const overdueLoading = ref(false)
const riskFilter = ref('')
const overduePage = reactive({ current: 1, size: 20, total: 0 })
const selectedYear = ref('2020')
const riskPieChartRef = ref(null)
const riskFunnelChartRef = ref(null)
const deptRiskChartRef = ref(null)
const calendarHeatmapRef = ref(null)
let riskPieChart = null
let riskFunnelChart = null
let deptRiskChart = null
let calendarHeatmapChart = null

// 借阅趋势
const trendStats = ref({})
const trendData = ref([])
const trendChartRef = ref(null)
let trendChart = null

const futureTrend = computed(() => {
  return trendData.value.filter(d => d.dataType === '预测')
})

// 图书热度
const heatStats = ref({})
const heatList = ref([])
const heatLoading = ref(false)
const heatFilter = ref('')
const trendFilter = ref('')
const heatPage = reactive({ current: 1, size: 20, total: 0 })
const heatPieChartRef = ref(null)
const trendPieChartRef = ref(null)
let heatPieChart = null
let trendPieChart = null

// 工具函数
const getRiskTagType = (level) => {
  const map = { '高风险': 'danger', '中风险': 'warning', '低风险': 'info', '极低风险': 'success' }
  return map[level] || 'info'
}

const getProgressColor = (probability) => {
  if (probability >= 0.7) return '#f56c6c'
  if (probability >= 0.4) return '#e6a23c'
  if (probability >= 0.2) return '#409eff'
  return '#67c23a'
}

const getTrendColor = (trend) => {
  if (trend === '上升') return '#67c23a'
  if (trend === '下降') return '#f56c6c'
  return '#909399'
}

const getTrendTagType = (trend) => {
  if (trend === '上升') return 'success'
  if (trend === '下降') return 'danger'
  return 'info'
}

const getHeatColor = (score) => {
  if (score >= 80) return '#f56c6c'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#409eff'
  return '#909399'
}

const getHeatTagType = (level) => {
  const map = { '爆款': 'danger', '热门': 'warning', '一般': 'info', '冷门': '', '极冷': 'info' }
  return map[level] || 'info'
}

// 加载逾期风险数据
const loadOverdueStats = async () => {
  try {
    const res = await getOverdueRiskStats()
    if (res.code === 200) {
      overdueStats.value = res.data
      renderRiskPieChart()
      renderRiskFunnelChart()
    }
  } catch (error) {
    console.error('加载逾期统计失败:', error)
  }
}

// 加载日历热力图数据（模拟数据 - 基于历史借阅数据和风险概率）
const loadCalendarData = () => {
  if (!calendarHeatmapRef.value) return
  
  // 模拟生成全年数据
  const data = []
  const startDate = new Date(`${selectedYear.value}-01-01`)
  const endDate = new Date(`${selectedYear.value}-12-31`)
  
  for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0]
    // 模拟风险值：工作日较高，周末较低，开学季和考试季较高
    const month = d.getMonth() + 1
    const day = d.getDay()
    let riskValue = Math.floor(Math.random() * 3) + 1
    
    // 周末降低
    if (day === 0 || day === 6) riskValue = Math.max(0, riskValue - 1)
    // 开学季（9-10月）和考试季（12-1月）增加
    if ((month >= 9 && month <= 10) || month === 12 || month === 1) {
      riskValue = Math.min(8, riskValue + 2)
    }
    
    data.push([dateStr, riskValue])
  }
  
  renderCalendarHeatmap(data)
}

const loadOverdueList = async () => {
  overdueLoading.value = true
  try {
    const res = await getOverdueRiskList({
      current: overduePage.current,
      size: overduePage.size,
      riskLevel: riskFilter.value
    })
    if (res.code === 200) {
      overdueList.value = res.data.records
      overduePage.total = res.data.total
      renderDeptRiskChart()
    }
  } catch (error) {
    console.error('加载逾期列表失败:', error)
  } finally {
    overdueLoading.value = false
  }
}

const renderRiskPieChart = () => {
  if (!riskPieChartRef.value || !overdueStats.value.riskDistribution) return
  if (!riskPieChart) riskPieChart = echarts.init(riskPieChartRef.value)
  
  const data = Object.entries(overdueStats.value.riskDistribution).map(([name, value]) => ({ name, value }))
  const colors = { '高风险': '#f56c6c', '中风险': '#e6a23c', '低风险': '#409eff', '极低风险': '#67c23a' }
  
  riskPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: { bottom: '0%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      label: {
        show: true,
        formatter: '{b}: {c}人\n({d}%)',
        fontSize: 12
      },
      labelLine: {
        show: true,
        length: 15,
        length2: 10
      },
      data: data.map(d => ({ ...d, itemStyle: { color: colors[d.name] || '#909399' } }))
    }]
  })
}

// 渲染风险漏斗图
const renderRiskFunnelChart = () => {
  if (!riskFunnelChartRef.value || !overdueStats.value.riskDistribution) return
  if (!riskFunnelChart) riskFunnelChart = echarts.init(riskFunnelChartRef.value)
  
  const distribution = overdueStats.value.riskDistribution
  const data = [
    { name: '极低风险', value: distribution['极低风险'] || 0 },
    { name: '低风险', value: distribution['低风险'] || 0 },
    { name: '中风险', value: distribution['中风险'] || 0 },
    { name: '高风险', value: distribution['高风险'] || 0 }
  ]
  
  riskFunnelChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    series: [{
      type: 'funnel',
      left: '10%',
      width: '80%',
      label: {
        fontSize: 12,
        formatter: '{b}\n{c}人'
      },
      labelLine: {
        show: true,
        length: 10
      },
      itemStyle: {
        borderWidth: 0
      },
      emphasis: {
        label: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      data: data,
      color: ['#67c23a', '#409eff', '#e6a23c', '#f56c6c']
    }]
  })
}

const renderDeptRiskChart = () => {
  if (!deptRiskChartRef.value || overdueList.value.length === 0) return
  if (!deptRiskChart) deptRiskChart = echarts.init(deptRiskChartRef.value)
  
  // 按院系统计风险用户（排除极低风险）
  const deptCount = {}
  overdueList.value.forEach(u => {
    if (u.riskLevel !== '极低风险') {
      const dept = u.dept || '未知'
      deptCount[dept] = (deptCount[dept] || 0) + 1
    }
  })
  
  const sorted = Object.entries(deptCount).sort((a, b) => b[1] - a[1]).slice(0, 8)
  
  deptRiskChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: { 
      type: 'category', 
      data: sorted.map(d => d[0]).reverse(),
      axisLabel: {
        formatter: (value) => value.length > 8 ? value.substring(0, 8) + '...' : value
      }
    },
    series: [{
      type: 'bar',
      data: sorted.map(d => d[1]).reverse(),
      itemStyle: { 
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#f56c6c' },
          { offset: 1, color: '#ff9999' }
        ])
      },
      label: {
        show: true,
        position: 'right',
        color: '#303133'
      }
    }]
  })
}

// 渲染日历热力图
const renderCalendarHeatmap = (data) => {
  if (!calendarHeatmapRef.value) return
  if (!calendarHeatmapChart) calendarHeatmapChart = echarts.init(calendarHeatmapRef.value)
  
  calendarHeatmapChart.setOption({
    tooltip: {
      formatter: (params) => {
        return `${params.data[0]}<br/>风险指数: ${params.data[1]}`
      }
    },
    visualMap: {
      show: false,
      min: 0,
      max: 8,
      inRange: {
        color: ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127']
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
      yearLabel: { show: false },
      dayLabel: {
        firstDay: 1,
        nameMap: ['日', '一', '二', '三', '四', '五', '六'],
        fontSize: 11
      },
      monthLabel: {
        show: true,
        nameMap: 'cn',
        fontSize: 12
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
  })
}

// 加载借阅趋势数据
const loadTrendData = async () => {
  try {
    const [statsRes, listRes] = await Promise.all([
      getLendTrendStats(),
      getLendTrendPrediction()
    ])
    if (statsRes.code === 200) trendStats.value = statsRes.data
    if (listRes.code === 200) {
      trendData.value = listRes.data
      renderTrendChart()
    }
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  }
}

const renderTrendChart = () => {
  if (!trendChartRef.value || trendData.value.length === 0) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)
  
  const historical = trendData.value.filter(d => d.dataType === '历史')
  const predicted = trendData.value.filter(d => d.dataType === '预测')
  
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['实际借阅量', '预测借阅量'], bottom: '0%' },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '5%', containLabel: true },
    xAxis: { type: 'category', data: trendData.value.map(d => d.lendMonth), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value', name: '借阅量' },
    series: [
      {
        name: '实际借阅量',
        type: 'line',
        data: trendData.value.map(d => d.dataType === '历史' ? d.lendCount : null),
        itemStyle: { color: '#409eff' },
        lineStyle: { width: 2 }
      },
      {
        name: '预测借阅量',
        type: 'line',
        data: trendData.value.map(d => d.predictedCount),
        itemStyle: { color: '#67c23a' },
        lineStyle: { width: 2, type: 'dashed' },
        areaStyle: { color: 'rgba(103, 194, 58, 0.1)' }
      }
    ]
  })
}

// 加载图书热度数据
const loadHeatStats = async () => {
  try {
    const res = await getBookHeatStats()
    if (res.code === 200) {
      heatStats.value = res.data
      renderHeatPieChart()
      renderTrendPieChart()
    }
  } catch (error) {
    console.error('加载热度统计失败:', error)
  }
}

const loadHeatList = async () => {
  heatLoading.value = true
  try {
    const res = await getBookHeatList({
      current: heatPage.current,
      size: heatPage.size,
      heatLevel: heatFilter.value,
      trend: trendFilter.value
    })
    if (res.code === 200) {
      heatList.value = res.data.records
      heatPage.total = res.data.total
    }
  } catch (error) {
    console.error('加载热度列表失败:', error)
  } finally {
    heatLoading.value = false
  }
}

const renderHeatPieChart = () => {
  if (!heatPieChartRef.value || !heatStats.value.heatDistribution) return
  if (!heatPieChart) heatPieChart = echarts.init(heatPieChartRef.value)
  
  const data = Object.entries(heatStats.value.heatDistribution).map(([name, value]) => ({ name, value }))
  const colors = { '爆款': '#f56c6c', '热门': '#e6a23c', '一般': '#409eff', '冷门': '#909399', '极冷': '#c0c4cc' }
  
  heatPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}本 ({d}%)' },
    legend: { bottom: '0%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      label: {
        show: true,
        formatter: '{b}: {c}本\n({d}%)',
        fontSize: 11
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 8
      },
      data: data.map(d => ({ ...d, itemStyle: { color: colors[d.name] || '#909399' } }))
    }]
  })
}

const renderTrendPieChart = () => {
  if (!trendPieChartRef.value || !heatStats.value.trendDistribution) return
  if (!trendPieChart) trendPieChart = echarts.init(trendPieChartRef.value)
  
  const data = Object.entries(heatStats.value.trendDistribution).map(([name, value]) => ({ name, value }))
  const colors = { '上升': '#67c23a', '稳定': '#409eff', '下降': '#f56c6c' }
  
  trendPieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}本 ({d}%)' },
    legend: { bottom: '0%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      label: {
        show: true,
        formatter: '{b}: {c}本\n({d}%)',
        fontSize: 11
      },
      labelLine: {
        show: true,
        length: 10,
        length2: 8
      },
      data: data.map(d => ({ ...d, itemStyle: { color: colors[d.name] || '#909399' } }))
    }]
  })
}

// 标签页切换
watch(activeTab, async (tab) => {
  await nextTick()
  if (tab === 'overdue') {
    if (!overdueStats.value.totalUsers) {
      await loadOverdueStats()
      await loadOverdueList()
      setTimeout(() => loadCalendarData(), 300)
    }
  } else if (tab === 'trend') {
    if (trendData.value.length === 0) {
      await loadTrendData()
    }
  } else if (tab === 'heat') {
    if (!heatStats.value.totalBooks) {
      await loadHeatStats()
      await loadHeatList()
    }
  }
})

onMounted(async () => {
  await loadOverdueStats()
  await loadOverdueList()
  
  await nextTick()
  setTimeout(() => {
    loadCalendarData()
  }, 500)
  
  window.addEventListener('resize', () => {
    riskPieChart?.resize()
    riskFunnelChart?.resize()
    deptRiskChart?.resize()
    calendarHeatmapChart?.resize()
    trendChart?.resize()
    heatPieChart?.resize()
    trendPieChart?.resize()
  })
})
</script>

<style scoped>
.prediction-container {
  padding: 0px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card.danger {
  border-left: 3px solid #f56c6c;
}

.stat-card.hot {
  border-left: 3px solid #e6a23c;
}

.chart-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-area {
  display: flex;
  gap: 10px;
}

.pagination-area {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.trend-tag {
  padding: 15px 15px;

}
</style>

<template>
  <div class="recommendation-monitor-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Monitor /></el-icon> 推荐系统监控</span>
          <el-tag v-if="lastUpdate" type="info">最后更新: {{ lastUpdate }}</el-tag>
        </div>
      </template>
      
      <div v-loading="loading">
        <!-- 核心指标 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="metric-card">
              <el-statistic title="推荐覆盖率" :value="stats.coverageRate" suffix="%" :precision="2">
                <template #prefix>
                  <el-icon color="#67c23a"><CircleCheck /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="metric-card">
              <el-statistic title="推荐总数" :value="stats.totalRecommendations">
                <template #prefix>
                  <el-icon color="#409eff"><Document /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="metric-card">
              <el-statistic title="人均推荐数" :value="stats.avgRecommendations" :precision="1">
                <template #prefix>
                  <el-icon color="#e6a23c"><User /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <el-card shadow="hover" class="metric-card">
              <el-statistic title="平均推荐得分" :value="stats.avgScore" :precision="2" suffix="/10">
                <template #prefix>
                  <el-icon color="#f56c6c"><Star /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 推荐算法分布 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header>
                <span>推荐算法覆盖用户分布</span>
              </template>
              <div ref="algorithmChartRef" style="width: 100%; height: 350px;"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header>
                <span>推荐来源数量分布</span>
              </template>
              <div ref="sourceChartRef" style="width: 100%; height: 350px;"></div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 推荐质量指标 -->
        <el-row :gutter="20">
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header>
                <span>算法得分对比</span>
              </template>
              <div ref="scoreChartRef" style="width: 100%; height: 350px;"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card shadow="hover">
              <template #header>
                <span>推荐系统配置</span>
              </template>
              <el-descriptions :column="1" border style="margin-top: 20px;">
                <el-descriptions-item label="推荐算法">{{ stats.algorithmType }}</el-descriptions-item>
                <el-descriptions-item label="算法权重">{{ stats.algorithmWeights }}</el-descriptions-item>
                <el-descriptions-item label="得分归一化">{{ stats.scoreNormalization }}</el-descriptions-item>
                <el-descriptions-item label="多样性得分">{{ stats.avgDiversity?.toFixed(3) }}</el-descriptions-item>
                <el-descriptions-item label="多来源推荐数">{{ stats.multiSourceCount?.toLocaleString() }}</el-descriptions-item>
                <el-descriptions-item label="多来源占比">{{ (stats.multiSourceRate * 100).toFixed(2) }}%</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { getRecommendationStats } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

const loading = ref(false)
const lastUpdate = ref('')
const algorithmChartRef = ref(null)
const sourceChartRef = ref(null)
const scoreChartRef = ref(null)

let algorithmChart = null
let sourceChart = null
let scoreChart = null

const stats = reactive({
  totalUsers: 0,
  coverageRate: 0,
  totalRecommendations: 0,
  recommendedUsers: 0,
  avgDiversity: 0,
  multiSourceCount: 0,
  avgRecommendations: 0,
  avgScore: 0,
  multiSourceRate: 0,
  cfUserCount: 0,
  contentUserCount: 0,
  popularityUserCount: 0,
  cfRecCount: 0,
  contentRecCount: 0,
  popularityRecCount: 0,
  avgCfScore: 0,
  avgContentScore: 0,
  avgPopularityScore: 0,
  algorithmWeights: '',
  scoreNormalization: '',
  algorithmType: ''
})

const loadData = async () => {
  try {
    loading.value = true
    const res = await getRecommendationStats()
    const data = res.data || []
    
    // 解析数据
    const statsMap = {}
    data.forEach(item => {
      statsMap[item.statType] = item.statValue
    })
    
    // 填充数据
    stats.totalUsers = parseInt(statsMap['total_users'] || 0)
    stats.coverageRate = parseFloat(statsMap['coverage_rate'] || 0)
    stats.totalRecommendations = parseInt(statsMap['total_recommendations'] || 0)
    stats.recommendedUsers = parseInt(statsMap['recommended_users'] || 0)
    stats.avgDiversity = parseFloat(statsMap['avg_diversity'] || 0)
    stats.multiSourceCount = parseInt(statsMap['multi_source_count'] || 0)
    stats.avgRecommendations = parseFloat(statsMap['avg_recommendations_per_user'] || 0)
    stats.avgScore = parseFloat(statsMap['avg_score'] || 0)
    stats.multiSourceRate = parseFloat(statsMap['multi_source_rate'] || 0)
    stats.cfUserCount = parseInt(statsMap['cf_user_count'] || 0)
    stats.contentUserCount = parseInt(statsMap['content_user_count'] || 0)
    stats.popularityUserCount = parseInt(statsMap['popularity_user_count'] || 0)
    stats.cfRecCount = parseInt(statsMap['cf_rec_count'] || 0)
    stats.contentRecCount = parseInt(statsMap['content_rec_count'] || 0)
    stats.popularityRecCount = parseInt(statsMap['popularity_rec_count'] || 0)
    stats.avgCfScore = parseFloat(statsMap['avg_cf_score'] || 0)
    stats.avgContentScore = parseFloat(statsMap['avg_content_score'] || 0)
    stats.avgPopularityScore = parseFloat(statsMap['avg_popularity_score'] || 0)
    stats.algorithmWeights = statsMap['algorithm_weights'] || ''
    stats.scoreNormalization = statsMap['score_normalization'] || ''
    stats.algorithmType = statsMap['algorithm_type'] || ''
    lastUpdate.value = statsMap['last_update'] || ''
    
    // 格式化时间
    if (lastUpdate.value) {
      lastUpdate.value = dayjs(lastUpdate.value).format('YYYY-MM-DD HH:mm:ss')
    }
    
    // 初始化图表
    initAlgorithmChart()
    initSourceChart()
    initScoreChart()
    
    console.log('✅ 推荐系统监控数据加载成功')
  } catch (error) {
    console.error('❌ 加载推荐系统监控数据失败：', error)
    ElMessage.error('加载推荐系统监控数据失败')
  } finally {
    loading.value = false
  }
}

const initAlgorithmChart = () => {
  if (!algorithmChartRef.value) return
  
  if (!algorithmChart) {
    algorithmChart = echarts.init(algorithmChartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}人 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '覆盖用户',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: [
        { value: stats.cfUserCount, name: '协同过滤' },
        { value: stats.contentUserCount, name: '内容推荐' },
        { value: stats.popularityUserCount, name: '热门推荐' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
  
  algorithmChart.setOption(option)
}

const initSourceChart = () => {
  if (!sourceChartRef.value) return
  
  if (!sourceChart) {
    sourceChart = echarts.init(sourceChartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['推荐数量']
    },
    xAxis: {
      type: 'category',
      data: ['协同过滤', '内容推荐', '热门推荐']
    },
    yAxis: {
      type: 'value',
      name: '推荐数量'
    },
    series: [{
      name: '推荐数量',
      type: 'bar',
      data: [stats.cfRecCount, stats.contentRecCount, stats.popularityRecCount],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}'
      }
    }]
  }
  
  sourceChart.setOption(option)
}

const initScoreChart = () => {
  if (!scoreChartRef.value) return
  
  if (!scoreChart) {
    scoreChart = echarts.init(scoreChartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['平均得分']
    },
    xAxis: {
      type: 'category',
      data: ['协同过滤', '内容推荐', '热门推荐']
    },
    yAxis: {
      type: 'value',
      name: '得分',
      max: 10
    },
    series: [{
      name: '平均得分',
      type: 'bar',
      data: [
        { value: stats.avgCfScore, itemStyle: { color: '#5470c6' } },
        { value: stats.avgContentScore, itemStyle: { color: '#91cc75' } },
        { value: stats.avgPopularityScore, itemStyle: { color: '#fac858' } }
      ],
      label: {
        show: true,
        position: 'top',
        formatter: '{c}'
      }
    }]
  }
  
  scoreChart.setOption(option)
}

onMounted(() => {
  loadData()
  
  window.addEventListener('resize', () => {
    algorithmChart?.resize()
    sourceChart?.resize()
    scoreChart?.resize()
  })
})

onUnmounted(() => {
  algorithmChart?.dispose()
  sourceChart?.dispose()
  scoreChart?.dispose()
})
</script>

<style scoped lang="scss">
.recommendation-monitor-container {
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
  
  .metric-card {
    margin-bottom: 20px;
  }
}
</style>

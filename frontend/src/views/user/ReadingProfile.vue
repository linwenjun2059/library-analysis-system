<template>
  <div class="reading-profile-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Avatar /></el-icon> 我的阅读画像</span>
          <el-button type="primary" @click="loadData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新数据
          </el-button>
        </div>
      </template>

      <el-empty v-if="!loading && !profile" description="暂无画像数据，请先借阅图书" />

      <div v-else>
        <!-- 顶部统计卡片 - 第一行 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="借阅总量" :value="profile?.totalBorrowCount || 0">
                <template #suffix>本</template>
              </el-statistic>
              <el-tag :type="getLevelTagType(profile?.borrowLevel)" style="margin-top: 10px;">
                {{ profile?.borrowLevel || '未知' }}
              </el-tag>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="阅读广度" :value="profile?.readingBreadth || 0">
                <template #suffix>个主题</template>
              </el-statistic>
              <div style="margin-top: 10px; color: #67c23a;">
                <el-icon><Star /></el-icon> 
                {{ getBreadthLevel(profile?.readingBreadth) }}
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="平均借阅" :value="profile?.avgBorrowDays || 0" :precision="1">
                <template #suffix>天</template>
              </el-statistic>
              <div style="margin-top: 10px; color: #409eff;">
                {{ getReadingSpeed(profile?.avgBorrowDays) }}
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="逾期率" :value="(profile?.overdueRate || 0) * 100" :precision="1">
                <template #suffix>%</template>
              </el-statistic>
              <div :style="{ marginTop: '10px', color: getOverdueRateColor(profile?.overdueRate) }">
                {{ getOverdueLevel(profile?.overdueRate) }}
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 顶部统计卡片 - 第二行（新增） -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="续借次数" :value="lendSummary?.renewCount || 0">
                <template #suffix>次</template>
              </el-statistic>
              <div style="margin-top: 10px; color: #e6a23c;">
                <el-icon><Refresh /></el-icon>
                续借率: {{ getRenewRate() }}%
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="总借阅天数" :value="lendSummary?.totalBorrowDays || 0">
                <template #suffix>天</template>
              </el-statistic>
              <div style="margin-top: 10px; color: #909399;">
                累计阅读时长
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="活跃天数" :value="lendSummary?.activeDays || 0">
                <template #suffix>天</template>
              </el-statistic>
              <div style="margin-top: 10px; color: #67c23a;">
                <el-icon><Calendar /></el-icon>
                {{ getActiveLevel() }}
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="最后借阅" :value="formatDate(lendSummary?.lastLendDate || profile?.lastBorrowDate)">
                <template #suffix></template>
              </el-statistic>
              <div style="margin-top: 10px; color: #409eff;">
                <el-icon><Clock /></el-icon>
                {{ getDaysSinceLastLend() }}
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 读者类型（聚类信息） -->
        <el-card shadow="hover" style="margin-bottom: 20px;" v-if="userClusterInfo" class="cluster-card">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-icon><DataAnalysis /></el-icon>
              <span>我的读者类型</span>
            </div>
          </template>
          <div class="cluster-info">
            <div class="cluster-name">
              <el-tag type="primary" effect="dark" size="large">
                {{ userClusterInfo.clusterName }}
              </el-tag>
            </div>
            <div class="cluster-characteristics">
              <el-tag
                v-for="(char, idx) in (userClusterInfo.clusterCharacteristics || '').split('、').filter(c => c)"
                :key="idx"
                :type="getTagType(idx)"
                size="default"
                style="margin: 5px;"
              >
                {{ char }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 用户标签 -->
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-icon><CollectionTag /></el-icon>
              <span>我的标签</span>
            </div>
          </template>
          <div class="tags-container">
            <el-tag
              v-for="(tag, idx) in parseTags(profile?.userTags)"
              :key="idx"
              :type="getTagType(idx)"
              effect="dark"
              size="large"
              style="margin: 5px;"
            >
              {{ tag }}
            </el-tag>
            <el-empty v-if="parseTags(profile?.userTags).length === 0" description="暂无标签" />
          </div>
        </el-card>

        <!-- 阅读目标进度环 -->
        <el-card shadow="hover" style="margin-bottom: 20px;" class="progress-card">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-icon><Trophy /></el-icon>
              <span>年度阅读目标</span>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <div class="progress-ring-container">
                <div class="progress-rings">
                  <div class="ring-item">
                    <div class="ring-wrapper">
                      <svg class="progress-ring" width="160" height="160">
                        <circle
                          class="progress-ring-circle-bg"
                          :r="70"
                          cx="80"
                          cy="80"
                        />
                        <circle
                          class="progress-ring-circle"
                          :r="70"
                          cx="80"
                          cy="80"
                          :stroke-dasharray="`${borrowProgress} ${440 - borrowProgress}`"
                          style="stroke: #409eff;"
                        />
                      </svg>
                      <div class="ring-text">
                        <div class="ring-value">{{ profile?.totalBorrowCount || 0 }}</div>
                        <div class="ring-label">本</div>
                        <div class="ring-target">目标: {{ yearlyBorrowTarget }}</div>
                      </div>
                    </div>
                    <div class="ring-title">借阅目标</div>
                  </div>
                  
                  <div class="ring-item">
                    <div class="ring-wrapper">
                      <svg class="progress-ring" width="160" height="160">
                        <circle
                          class="progress-ring-circle-bg"
                          :r="70"
                          cx="80"
                          cy="80"
                        />
                        <circle
                          class="progress-ring-circle"
                          :r="70"
                          cx="80"
                          cy="80"
                          :stroke-dasharray="`${breadthProgress} ${440 - breadthProgress}`"
                          style="stroke: #67c23a;"
                        />
                      </svg>
                      <div class="ring-text">
                        <div class="ring-value">{{ profile?.readingBreadth || 0 }}</div>
                        <div class="ring-label">类</div>
                        <div class="ring-target">目标: {{ yearlyBreadthTarget }}</div>
                      </div>
                    </div>
                    <div class="ring-title">主题广度</div>
                  </div>
                </div>
                <div class="progress-tips">
                  <el-alert
                    v-if="borrowProgressPercent >= 100"
                    title="🎉 恭喜完成年度借阅目标！"
                    type="success"
                    :closable="false"
                  />
                  <el-alert
                    v-else-if="borrowProgressPercent >= 80"
                    title="💪 加油！距离目标只差一步了！"
                    type="warning"
                    :closable="false"
                  />
                  <el-alert
                    v-else
                    :title="`还需借阅 ${yearlyBorrowTarget - (profile?.totalBorrowCount || 0)} 本即可达成目标`"
                    type="info"
                    :closable="false"
                  />
                </div>
              </div>
            </el-col>
            
            <el-col :xs="24" :md="12">
              <div class="achievement-list">
                <h4 style="margin-bottom: 15px; color: #303133;">📊 阅读成就</h4>
                <div class="achievement-item" :class="{ achieved: profile?.totalBorrowCount >= 10 }">
                  <el-icon><Medal /></el-icon>
                  <span>初级读者 (10本)</span>
                  <el-tag v-if="profile?.totalBorrowCount >= 10" type="success" size="small">已达成</el-tag>
                </div>
                <div class="achievement-item" :class="{ achieved: profile?.totalBorrowCount >= 50 }">
                  <el-icon><Medal /></el-icon>
                  <span>中级读者 (50本)</span>
                  <el-tag v-if="profile?.totalBorrowCount >= 50" type="success" size="small">已达成</el-tag>
                </div>
                <div class="achievement-item" :class="{ achieved: profile?.totalBorrowCount >= 100 }">
                  <el-icon><Trophy /></el-icon>
                  <span>高级读者 (100本)</span>
                  <el-tag v-if="profile?.totalBorrowCount >= 100" type="success" size="small">已达成</el-tag>
                </div>
                <div class="achievement-item" :class="{ achieved: profile?.readingBreadth >= 10 }">
                  <el-icon><Star /></el-icon>
                  <span>博览群书 (10类)</span>
                  <el-tag v-if="profile?.readingBreadth >= 10" type="success" size="small">已达成</el-tag>
                </div>
                <div class="achievement-item" :class="{ achieved: (profile?.overdueRate || 1) === 0 }">
                  <el-icon><CircleCheck /></el-icon>
                  <span>完美守时 (0逾期)</span>
                  <el-tag v-if="(profile?.overdueRate || 1) === 0" type="success" size="small">已达成</el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 阅读主题极坐标图 + 偏好列表 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :xs="24" :lg="14">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><PieChart /></el-icon>
                  <span>阅读主题分布（极坐标）</span>
                </div>
              </template>
              <div ref="polarChartRef" style="width: 100%; height: 400px;"></div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="10">
            <el-card shadow="hover" style="margin-bottom: 20px;">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Reading /></el-icon>
                  <span>偏好主题</span>
                </div>
              </template>
              <div class="top-list">
                <el-tag
                  v-for="(item, idx) in topSubjects"
                  :key="idx"
                  type="success"
                  effect="dark"
                  size="large"
                  style="margin: 6px;"
                >
                  {{ item }}
                </el-tag>
                <el-empty v-if="topSubjects.length === 0" description="暂无偏好主题" />
              </div>
            </el-card>
            
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Location /></el-icon>
                  <span>常去书库</span>
                </div>
              </template>
              <div class="top-list">
                <el-tag
                  v-for="(item, idx) in topLocations"
                  :key="idx"
                  type="info"
                  effect="dark"
                  size="large"
                  style="margin: 6px;"
                >
                  {{ item }}
                </el-tag>
                <el-empty v-if="topLocations.length === 0" description="暂无偏好位置" />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 时间分布图 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Clock /></el-icon>
                  <span>借阅时间分布（小时）</span>
                </div>
              </template>
              <div ref="timeDistChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon><Calendar /></el-icon>
                  <span>借阅星期分布</span>
                </div>
              </template>
              <div ref="weekDistChartRef" style="width: 100%; height: 300px;"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 阅读习惯雷达图 -->
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-icon><DataAnalysis /></el-icon>
              <span>阅读习惯分析</span>
            </div>
          </template>
          <div ref="radarChartRef" style="width: 100%; height: 400px;"></div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUserProfileByUserid } from '@/api/statistics'
import { getUserLendSummary, getUserLendRecords } from '@/api/user'
import { getUserCluster } from '@/api/advanced'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  Avatar, Refresh, Star, Reading, Location, DataAnalysis, 
  Clock, Calendar, CollectionTag, Trophy, Medal, CircleCheck, PieChart 
} from '@element-plus/icons-vue'

const userStore = useUserStore()
const loading = ref(false)
const profile = ref(null)
const lendSummary = ref(null)
const lendRecords = ref([])
const userClusterInfo = ref(null)

const radarChartRef = ref(null)
const timeDistChartRef = ref(null)
const weekDistChartRef = ref(null)
const polarChartRef = ref(null)

let radarChart = null
let timeDistChart = null
let weekDistChart = null
let polarChart = null

const topSubjects = computed(() => parseJsonArray(profile.value?.favoriteSubjects || '[]').slice(0, 3))
const topLocations = computed(() => parseJsonArray(profile.value?.favoriteLocations || '[]').slice(0, 3))

// 年度目标设置
const yearlyBorrowTarget = ref(50)
const yearlyBreadthTarget = ref(10)

// 进度计算
const borrowProgressPercent = computed(() => {
  if (!profile.value) return 0
  return Math.min((profile.value.totalBorrowCount / yearlyBorrowTarget.value) * 100, 100)
})

const breadthProgressPercent = computed(() => {
  if (!profile.value) return 0
  return Math.min((profile.value.readingBreadth / yearlyBreadthTarget.value) * 100, 100)
})

const borrowProgress = computed(() => {
  const circumference = 2 * Math.PI * 70
  return (borrowProgressPercent.value / 100) * circumference
})

const breadthProgress = computed(() => {
  const circumference = 2 * Math.PI * 70
  return (breadthProgressPercent.value / 100) * circumference
})

// 解析JSON数组
const parseJsonArray = (jsonStr) => {
  if (!jsonStr) return []
  try {
    return JSON.parse(jsonStr)
  } catch (e) {
    return []
  }
}

// 解析标签
const parseTags = (tagsStr) => {
  return parseJsonArray(tagsStr)
}

// 获取等级标签类型
const getLevelTagType = (level) => {
  const map = {
    '超级读者': 'danger',
    '高级读者': 'warning',
    '中级读者': 'success',
    '初级读者': 'info',
    '不活跃': '',
    '活跃': 'success',
    '一般': 'info'
  }
  return map[level] || 'info'
}

// 获取广度等级
const getBreadthLevel = (breadth) => {
  if (breadth >= 15) return '博览群书'
  if (breadth >= 10) return '跨学科阅读'
  if (breadth >= 5) return '涉猎广泛'
  if (breadth >= 2) return '专注阅读'
  return '初次探索'
}

// 获取阅读速度
const getReadingSpeed = (days) => {
  if (days >= 30) return '深度阅读'
  if (days >= 20) return '细致阅读'
  if (days >= 10) return '正常阅读'
  if (days > 0) return '快速阅读'
  return '未知'
}

// 获取逾期等级
const getOverdueLevel = (rate) => {
  if (rate === 0) return '完美守时'
  if (rate < 0.05) return '极少逾期'
  if (rate < 0.2) return '偶尔逾期'
  if (rate < 0.5) return '经常逾期'
  return '高频逾期'
}

// 获取逾期率颜色
const getOverdueRateColor = (rate) => {
  if (rate === 0) return '#67c23a'
  if (rate < 0.1) return '#409eff'
  if (rate < 0.3) return '#e6a23c'
  return '#f56c6c'
}

// 获取标签类型
const getTagType = (idx) => {
  const types = ['', 'success', 'info', 'warning', 'danger']
  return types[idx % types.length]
}

// 计算续借率
const getRenewRate = () => {
  if (!lendSummary.value || !lendSummary.value.totalLendCount) return 0
  return ((lendSummary.value.renewCount || 0) / lendSummary.value.totalLendCount * 100).toFixed(1)
}

// 获取活跃等级
const getActiveLevel = () => {
  const days = lendSummary.value?.activeDays || 0
  if (days >= 100) return '非常活跃'
  if (days >= 50) return '较为活跃'
  if (days >= 20) return '一般活跃'
  if (days > 0) return '偶尔活跃'
  return '不活跃'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 计算距最后借阅天数
const getDaysSinceLastLend = () => {
  const lastDate = lendSummary.value?.lastLendDate || profile.value?.lastBorrowDate
  if (!lastDate) return '暂无记录'
  const days = Math.floor((new Date() - new Date(lastDate)) / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '1天前'
  if (days < 30) return `${days}天前`
  if (days < 365) return `${Math.floor(days / 30)}个月前`
  return `${Math.floor(days / 365)}年前`
}


// 初始化雷达图
const initRadarChart = () => {
  if (!radarChartRef.value || !profile.value) return

  if (!radarChart) {
    radarChart = echarts.init(radarChartRef.value)
  }

  // 计算指标
  const borrowScore = Math.min((profile.value.totalBorrowCount || 0) / 2, 100)
  const breadthScore = Math.min((profile.value.readingBreadth || 0) * 6, 100)
  const speedScore = profile.value.avgBorrowDays ? Math.min(profile.value.avgBorrowDays * 3, 100) : 0
  const punctualityScore = (1 - (profile.value.overdueRate || 0)) * 100
  const activeScore = profile.value.borrowLevel === '活跃' ? 85 : profile.value.borrowLevel === '一般' ? 50 : 20

  const option = {
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: [
        { name: '借阅量', max: 100 },
        { name: '阅读广度', max: 100 },
        { name: '深度阅读', max: 100 },
        { name: '守时程度', max: 100 },
        { name: '活跃度', max: 100 }
      ],
      radius: '60%'
    },
    series: [{
      name: '阅读习惯',
      type: 'radar',
      data: [
        {
          value: [borrowScore, breadthScore, speedScore, punctualityScore, activeScore],
          name: '我的画像',
          areaStyle: {
            color: 'rgba(64, 158, 255, 0.3)'
          },
          itemStyle: {
            color: '#409eff'
          }
        }
      ]
    }]
  }

  radarChart.setOption(option)
}

// 初始化时间分布图（小时）
const initTimeDistChart = () => {
  if (!timeDistChartRef.value || !lendRecords.value.length) return

  if (!timeDistChart) {
    timeDistChart = echarts.init(timeDistChartRef.value)
  }

  // 按小时统计
  const hourCounts = new Array(24).fill(0)
  lendRecords.value.forEach(record => {
    if (record.lendTime) {
      try {
        const hour = parseInt(record.lendTime.split(':')[0])
        if (hour >= 0 && hour < 24) {
          hourCounts[hour]++
        }
      } catch (e) {
        // 忽略解析错误
      }
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}点<br/>借阅次数: ${params[0].value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 24 }, (_, i) => `${i}点`),
      axisLabel: {
        interval: 1
      }
    },
    yAxis: {
      type: 'value',
      name: '借阅次数'
    },
    series: [{
      name: '借阅次数',
      type: 'bar',
      data: hourCounts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#67c23a' },
          { offset: 1, color: '#85ce61' }
        ])
      }
    }]
  }

  timeDistChart.setOption(option)
}

// 初始化星期分布图
const initWeekDistChart = () => {
  if (!weekDistChartRef.value || !lendRecords.value.length) return

  if (!weekDistChart) {
    weekDistChart = echarts.init(weekDistChartRef.value)
  }

  // 按星期统计
  const weekCounts = new Array(7).fill(0)
  const weekNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  lendRecords.value.forEach(record => {
    if (record.lendDate) {
      try {
        const date = typeof record.lendDate === 'string' 
          ? new Date(record.lendDate) 
          : new Date(record.lendDate)
        const day = date.getDay() // 0=周日, 1=周一, ...
        const index = day === 0 ? 6 : day - 1 // 转换为0=周一, 6=周日
        weekCounts[index]++
      } catch (e) {
        // 忽略解析错误
      }
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return `${params[0].axisValue}<br/>借阅次数: ${params[0].value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: weekNames
    },
    yAxis: {
      type: 'value',
      name: '借阅次数'
    },
    series: [{
      name: '借阅次数',
      type: 'bar',
      data: weekCounts,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#e6a23c' },
          { offset: 1, color: '#f0c78a' }
        ])
      },
      label: {
        show: true,
        position: 'top'
      }
    }]
  }

  weekDistChart.setOption(option)
}

// 初始化极坐标图
const initPolarChart = () => {
  if (!polarChartRef.value || !lendRecords.value.length) return

  if (!polarChart) {
    polarChart = echarts.init(polarChartRef.value)
  }

  // 统计各主题的借阅次数
  const subjectCounts = {}
  lendRecords.value.forEach(record => {
    const subject = record.subject || '未知主题'
    subjectCounts[subject] = (subjectCounts[subject] || 0) + 1
  })

  // 转换为数组并排序
  const subjectData = Object.entries(subjectCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 12) // 取前12个主题

  const categories = subjectData.map(item => item.name)
  const values = subjectData.map(item => item.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    angleAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        interval: 0,
        fontSize: 11,
        color: '#606266',
        formatter: (value) => {
          return value.length > 6 ? value.substring(0, 6) + '...' : value
        }
      }
    },
    radiusAxis: {
      name: '借阅次数',
      nameTextStyle: {
        fontSize: 12,
        color: '#909399'
      }
    },
    polar: {
      radius: ['15%', '75%']
    },
    series: [{
      type: 'bar',
      data: values,
      coordinateSystem: 'polar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#67c23a' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      label: {
        show: true,
        position: 'middle',
        formatter: '{c}',
        fontSize: 10,
        color: '#fff',
        fontWeight: 'bold'
      }
    }]
  }

  polarChart.setOption(option)
}

const loadData = async () => {
  try {
    loading.value = true
    console.log('🔄 加载我的阅读画像...')

    const userid = userStore.getUserId()
    if (!userid) {
      ElMessage.warning('请先登录')
      return
    }

    // 并行加载数据
    const [profileRes, summaryRes, recordsRes, clusterRes] = await Promise.all([
      getUserProfileByUserid(userid),
      getUserLendSummary(userid).catch(() => ({ data: null })),
      getUserLendRecords(userid, { current: 1, size: 1000 }).catch(() => ({ data: { records: [] } })),
      getUserCluster(userid).catch(() => ({ data: null }))
    ])

    profile.value = profileRes.data
    lendSummary.value = summaryRes.data
    lendRecords.value = recordsRes.data?.records || recordsRes.data?.list || []
    userClusterInfo.value = clusterRes.data

    console.log('📥 收到画像数据:', profile.value)
    console.log('📥 收到借阅汇总:', lendSummary.value)
    console.log('📥 收到借阅记录:', lendRecords.value.length, '条')
    console.log('📥 收到聚类信息:', userClusterInfo.value)

    if (!profile.value) {
      console.warn('⚠️ 暂无画像数据')
      ElMessage.warning('暂无画像数据，请先借阅图书')
      return
    }

    // 初始化图表
    await nextTick()
    setTimeout(() => {
      initRadarChart()
      initTimeDistChart()
      initWeekDistChart()
      initPolarChart()
      console.log('✅ 阅读画像加载成功')
    }, 300)

  } catch (error) {
    console.error('❌ 加载画像失败：', error)
    ElMessage.error('加载画像数据失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()

  window.addEventListener('resize', () => {
    radarChart?.resize()
    timeDistChart?.resize()
    weekDistChart?.resize()
    polarChart?.resize()
  })
})

onUnmounted(() => {
  radarChart?.dispose()
  timeDistChart?.dispose()
  weekDistChart?.dispose()
  polarChart?.dispose()
})
</script>

<style scoped lang="scss">
.reading-profile-container {
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

  .stat-card {
    text-align: center;
  }

  .tags-container {
    min-height: 60px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
  }

  .top-list {
    min-height: 80px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }

  .cluster-card {
    .cluster-info {
      text-align: center;
    }

    .cluster-name {
      margin-bottom: 15px;
    }

    .cluster-characteristics {
      margin-bottom: 10px;
    }
  }

  .progress-card {
    .progress-ring-container {
      .progress-rings {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 20px;
      }

      .ring-item {
        text-align: center;

        .ring-wrapper {
          position: relative;
          display: inline-block;
          margin-bottom: 10px;

          .progress-ring {
            transform: rotate(-90deg);
          }

          .progress-ring-circle-bg {
            fill: none;
            stroke: #f0f0f0;
            stroke-width: 12;
          }

          .progress-ring-circle {
            fill: none;
            stroke-width: 12;
            stroke-linecap: round;
            transition: stroke-dasharray 0.6s ease;
          }

          .ring-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;

            .ring-value {
              font-size: 32px;
              font-weight: bold;
              color: #303133;
              line-height: 1;
            }

            .ring-label {
              font-size: 14px;
              color: #909399;
              margin-top: 2px;
            }

            .ring-target {
              font-size: 12px;
              color: #c0c4cc;
              margin-top: 8px;
            }
          }
        }

        .ring-title {
          font-size: 15px;
          color: #606266;
          font-weight: 600;
        }
      }

      .progress-tips {
        margin-top: 15px;
      }
    }

    .achievement-list {
      .achievement-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        background: #f5f7fa;
        transition: all 0.3s;
        opacity: 0.6;

        &.achieved {
          opacity: 1;
          background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
          box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);

          .el-icon {
            color: #67c23a;
            font-size: 20px;
          }
        }

        .el-icon {
          font-size: 18px;
          color: #909399;
        }

        span {
          flex: 1;
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }

        &:hover {
          transform: translateX(5px);
        }
      }
    }
  }
}
</style>

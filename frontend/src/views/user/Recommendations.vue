<template>
  <div class="recommendations-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span><el-icon><Star /></el-icon> 图书推荐</span>
          <el-button type="primary" size="small" @click="loadAllData" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新推荐
            </el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Tab 1: 个性化推荐 -->
        <el-tab-pane name="personalized">
          <template #label>
            <span><el-icon><Aim /></el-icon> 为我推荐</span>
          </template>
      <div v-loading="loading">
            <el-empty v-if="!personalizedRecommendations.length" description="暂无个性化推荐数据" />
            
            <template v-else>
              <el-row :gutter="16" class="chart-row">
                <el-col :xs="24" :md="8">
                  <el-card class="chart-card" shadow="never">
                    <template #header>
                      <span><el-icon><DataAnalysis /></el-icon> 推荐来源分布</span>
                    </template>
                    <div ref="personalSourceChartRef" class="chart"></div>
                  </el-card>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-card class="chart-card" shadow="never">
                    <template #header>
                      <span><el-icon><TrendCharts /></el-icon> 推荐主题分布（Top 8）</span>
                    </template>
                    <div ref="personalSubjectChartRef" class="chart"></div>
                  </el-card>
                </el-col>
                <el-col :xs="24" :md="8">
                  <el-card class="chart-card" shadow="never">
                    <template #header>
                      <span><el-icon><Aim /></el-icon> TOP5 匹配度雷达</span>
                    </template>
                    <div ref="personalRadarChartRef" class="chart"></div>
                  </el-card>
                </el-col>
              </el-row>

              <el-row :gutter="24" style="margin-top: 8px;">
          <el-col 
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6" 
                v-for="book in paginatedPersonalized" 
            :key="book.userid + book.bookId"
                style="margin-bottom: 20px;"
          >
                <el-card class="book-card personalized" shadow="hover" @click="showBookDetail(book)">
              <div class="book-rank">{{ book.rankNo }}</div>
              <div class="book-info">
                    <h4 class="book-title">
                      <el-link type="primary" :underline="false" @click.stop="showBookDetail(book)">
                        {{ book.title }}
                      </el-link>
                    </h4>
                <p class="book-author">{{ book.author }}</p>
                <el-tag size="small" type="info">{{ book.subject }}</el-tag>
                <el-divider />
                <div class="book-score">
                  <span class="label">推荐得分：</span>
                  <span class="score-value">{{ formatScore(book.score) }}</span>
                  <el-rate 
                    :model-value="book.score / 2" 
                    disabled 
                    text-color="#ff9900"
                    :max="5"
                  />
                </div>
                <div class="book-source">
                  <span class="label">推荐来源：</span>
                  <el-tag 
                    v-for="source in getSourceTags(book.recSources)" 
                    :key="source"
                    size="small"
                    style="margin-right: 5px;"
                  >
                    {{ source }}
                  </el-tag>
                </div>
                <div class="book-reason">
                  <el-text type="info" size="small">{{ book.reason }}</el-text>
                </div>
                    <div class="card-actions">
                      <el-button size="small" type="primary" plain @click.stop="showBookDetail(book)">查看详情</el-button>
                    </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
            <div class="pagination-container" v-if="personalizedRecommendations.length > 0">
          <el-pagination
                v-model:current-page="personalizedPagination.current"
                v-model:page-size="personalizedPagination.size"
            :page-sizes="[8, 12, 20, 40]"
                :total="personalizedPagination.total"
            :background="true"
            layout="total, sizes, prev, pager, next, jumper"
                @size-change="handlePersonalizedSizeChange"
                @current-change="handlePersonalizedCurrentChange"
              />
            </div>
            </template>
          </div>
        </el-tab-pane>
        
        <!-- Tab 2: 热门图书 -->
        <el-tab-pane name="hot">
          <template #label>
            <span><el-icon><Trophy /></el-icon> 热门图书</span>
          </template>
          <el-alert title="全校最受欢迎的图书TOP100" type="info" :closable="false" style="margin-bottom: 12px;" />
          
          <el-row :gutter="16" v-if="hotBooks.length" class="chart-row" style="margin-bottom: 8px;">
            <el-col :xs="24" :md="12">
              <el-card class="chart-card" shadow="never">
                <template #header>
                  <span><el-icon><DataAnalysis /></el-icon> 类型分布（Top 10）</span>
                </template>
                <div ref="hotSubjectChartRef" class="chart"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card class="chart-card" shadow="never">
                <template #header>
                  <span><el-icon><TrendCharts /></el-icon> 最热门作者 Top10</span>
                </template>
                <div ref="hotAuthorChartRef" class="chart"></div>
              </el-card>
            </el-col>
          </el-row>
          
          <el-row :gutter="24" v-loading="loading">
            <el-col 
              :xs="24" :sm="12" :md="8" :lg="6" 
              v-for="book in pagedHotBooks" 
              :key="book.bookId"
              style="margin-bottom: 20px;"
            >
              <el-card class="book-card hot" shadow="hover" @click="showBookDetail(book)">
                <div class="rank-badge hot">
                  <el-icon><Trophy /></el-icon>
                  {{ book.rankNo }}
                </div>
                <div class="book-content">
                  <h3 class="book-title">
                    <el-link type="primary" :underline="false" @click.stop="showBookDetail(book)">
                      {{ book.title }}
                    </el-link>
                  </h3>
                  <p class="book-author">
                    <el-icon><User /></el-icon>
                    {{ book.author }}
                  </p>
                  <el-tag type="success" size="small">{{ book.subject }}</el-tag>
                  <div class="borrow-info">
                    <el-icon><Reading /></el-icon>
                    <span>{{ book.borrowCount }} 次借阅</span>
                  </div>
                  <div class="card-actions">
                    <el-button size="small" type="primary" plain @click.stop="showBookDetail(book)">查看详情</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          
          <el-pagination
            v-model:current-page="hotPagination.current"
            v-model:page-size="hotPagination.size"
            :page-sizes="[10, 12, 20, 40]"
            :total="hotPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
            @current-change="handleHotCurrentChange"
          />
          
          <el-empty v-if="!loading && hotBooks.length === 0" description="暂无热门图书数据" />
        </el-tab-pane>
        
        <!-- Tab 3: 院系推荐 -->
        <el-tab-pane name="dept">
          <template #label>
            <span><el-icon><Reading /></el-icon> {{ userDept }} 热门榜</span>
          </template>
          <el-alert :title="`${userDept} 最受欢迎的图书TOP30`" type="success" :closable="false" style="margin-bottom: 12px;" />
          
          <el-row :gutter="16" v-if="deptHotBooks.length" class="chart-row" style="margin-bottom: 8px;">
            <el-col :xs="24" :md="12">
              <el-card class="chart-card" shadow="never">
                <template #header>
                  <span><el-icon><DataAnalysis /></el-icon> 类型分布（Top 10）</span>
                </template>
                <div ref="deptSubjectChartRef" class="chart"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-card class="chart-card" shadow="never">
                <template #header>
                  <span><el-icon><TrendCharts /></el-icon> 最热门作者 Top10</span>
                </template>
                <div ref="deptAuthorChartRef" class="chart"></div>
              </el-card>
            </el-col>
          </el-row>
          
          <el-row :gutter="24" v-loading="loading">
            <el-col 
              :xs="24" :sm="12" :md="8" :lg="6" 
              v-for="book in pagedDeptBooks" 
              :key="book.bookId"
              style="margin-bottom: 20px;"
            >
              <el-card class="book-card dept" shadow="hover" @click="showBookDetail(book)">
                <div class="rank-badge dept">
                  <el-icon><Medal /></el-icon>
                  {{ book.rankNo }}
                </div>
                <div class="book-content">
                  <h3 class="book-title">
                    <el-link type="primary" :underline="false" @click.stop="showBookDetail(book)">
                      {{ book.title }}
                    </el-link>
                  </h3>
                  <p class="book-author">
                    <el-icon><User /></el-icon>
                    {{ book.author }}
                  </p>
                  <el-tag type="warning" size="small">{{ book.subject }}</el-tag>
                  <div class="borrow-info">
                    <el-icon><Reading /></el-icon>
                    <span>{{ book.borrowCount }} 次借阅</span>
                  </div>
                  <div class="card-actions">
                    <el-button size="small" type="primary" plain @click.stop="showBookDetail(book)">查看详情</el-button>
        </div>
      </div>
              </el-card>
            </el-col>
          </el-row>
          
          <el-pagination
            v-if="deptHotBooks.length > 0"
            v-model:current-page="deptPagination.current"
            v-model:page-size="deptPagination.size"
            :page-sizes="[8, 12, 20]"
            :total="deptPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
            @current-change="handleDeptCurrentChange"
          />
          
          <el-empty v-if="!loading && deptHotBooks.length === 0" description="暂无院系推荐数据" />
        </el-tab-pane>
      </el-tabs>

      <!-- 图书详情对话框 -->
      <el-dialog
        v-model="detailDialogVisible"
        title="图书详情"
        width="820px"
      >
        <div v-if="currentBook">
          <el-descriptions :column="2" border style="margin-bottom: 20px;">
            <el-descriptions-item label="书名">{{ bookDetail?.title || currentBook.title }}</el-descriptions-item>
            <el-descriptions-item label="作者">{{ bookDetail?.author || currentBook.author || '-' }}</el-descriptions-item>
            <el-descriptions-item label="出版社">{{ bookDetail?.publisher || currentBook.publisher || '-' }}</el-descriptions-item>
            <el-descriptions-item label="出版年份">{{ bookDetail?.pubYear || bookDetail?.publishYear || currentBook.pubYear || '-' }}</el-descriptions-item>
            <el-descriptions-item label="主题分类">{{ bookDetail?.subject || currentBook.subject || '-' }}</el-descriptions-item>
            <el-descriptions-item label="馆藏位置">{{ bookDetail?.locationName || currentBook.locationName || currentBook.location || '-' }}</el-descriptions-item>
            <el-descriptions-item label="ISBN">{{ bookDetail?.isbn || currentBook.isbn || '-' }}</el-descriptions-item>
            <el-descriptions-item label="索书号">{{ bookDetail?.callNo || currentBook.callNo || '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-card v-if="bookSummary" shadow="hover">
            <template #header>
              <span><el-icon><DataAnalysis /></el-icon> 借阅统计</span>
            </template>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="总借阅次数" :value="bookSummary.totalLendCount || 0">
                  <template #prefix>
                    <el-icon color="#409eff"><Reading /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="借阅用户数" :value="bookSummary.uniqueUserCount || 0">
                  <template #prefix>
                    <el-icon color="#67c23a"><User /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="平均借阅天数" :value="bookSummary.avgBorrowDays || 0" :precision="1">
                  <template #prefix>
                    <el-icon color="#e6a23c"><Timer /></el-icon>
                  </template>
                  <template #suffix>天</template>
                </el-statistic>
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="借阅频率" :value="bookSummary.lendFrequency || 0" :precision="2">
                  <template #prefix>
                    <el-icon color="#909399"><TrendCharts /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>
            <el-divider />
            <el-row :gutter="20">
              <el-col :span="12">
                <div class="stat-item">
                  <span class="label">续借次数：</span>
                  <span class="value">{{ bookSummary.renewCount || 0 }}</span>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="stat-item">
                  <span class="label">逾期率：</span>
                  <span class="value" :class="(bookSummary.overdueRate || 0) > 0.1 ? 'danger' : ''">
                    {{ ((bookSummary.overdueRate || 0) * 100).toFixed(2) }}%
                  </span>
                </div>
              </el-col>
              <el-col :span="12" v-if="bookSummary.firstLendDate">
                <div class="stat-item">
                  <span class="label">首次借阅：</span>
                  <span class="value">{{ formatDate(bookSummary.firstLendDate) }}</span>
                </div>
              </el-col>
              <el-col :span="12" v-if="bookSummary.lastLendDate">
                <div class="stat-item">
                  <span class="label">最后借阅：</span>
                  <span class="value">{{ formatDate(bookSummary.lastLendDate) }}</span>
                </div>
              </el-col>
            </el-row>
          </el-card>
          <el-empty v-else description="暂无借阅统计" />
        </div>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { getUserRecommendations } from '@/api/user'
import { getHotBooks, getBookLendSummary, getBookDetail } from '@/api/book'
import { getBookRecommendBase } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import { 
  Star, Refresh, Reading, Trophy, Medal, User, DataAnalysis, Timer, TrendCharts, Aim 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const userStore = useUserStore()
const loading = ref(false)
const activeTab = ref('personalized')

// 个性化推荐数据
const personalizedRecommendations = ref([])
const personalizedPagination = reactive({
  current: 1,
  size: 8,
  total: 0
})

// 热门图书数据
const hotBooks = ref([])
const hotPagination = reactive({
  current: 1,
  size: 12,
  total: 0
})

// 院系推荐数据
const deptHotBooks = ref([])
const userDept = ref('')
const deptPagination = reactive({
  current: 1,
  size: 8,
  total: 0
})

// 图书详情
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const currentBook = ref(null)
const bookSummary = ref(null)
const bookDetail = ref(null)

// 图表
const personalSourceChartRef = ref(null)
const personalSubjectChartRef = ref(null)
const personalRadarChartRef = ref(null)
const hotSubjectChartRef = ref(null)
const hotAuthorChartRef = ref(null)
const deptSubjectChartRef = ref(null)
const deptAuthorChartRef = ref(null)
let personalSourceChart = null
let personalSubjectChart = null
let personalRadarChart = null
let hotSubjectChart = null
let hotAuthorChart = null
let deptSubjectChart = null
let deptAuthorChart = null

// 计算属性
const paginatedPersonalized = computed(() => {
  const start = (personalizedPagination.current - 1) * personalizedPagination.size
  const end = start + personalizedPagination.size
  return personalizedRecommendations.value.slice(start, end)
})

const pagedHotBooks = computed(() => {
  const start = (hotPagination.current - 1) * hotPagination.size
  const end = start + hotPagination.size
  return hotBooks.value.slice(start, end)
})

const pagedDeptBooks = computed(() => {
  const start = (deptPagination.current - 1) * deptPagination.size
  const end = start + deptPagination.size
  return deptHotBooks.value.slice(start, end)
})

// 工具函数
const sourceMap = {
  cf: '协同过滤',
  content: '内容推荐',
  popularity: '热度推荐'
}

const getSourceTags = (sources) => {
  if (!sources) return []
  return sources.split(',').map(s => sourceMap[s.trim()] || s)
}

const formatScore = (score) => {
  if (score === null || score === undefined) return '0.00'
  return Number(score).toFixed(2)
}

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN')
}

// 图表数据
const personalizedSourceStats = computed(() => {
  const counter = {}
  personalizedRecommendations.value.forEach(item => {
    const sources = item.recSources ? item.recSources.split(',') : []
    sources.forEach(s => {
      const key = sourceMap[s.trim()] || s.trim() || '未知来源'
      counter[key] = (counter[key] || 0) + 1
    })
  })
  return Object.entries(counter).map(([name, value]) => ({ name, value }))
})

const personalizedSubjectStats = computed(() => {
  const counter = {}
  personalizedRecommendations.value.forEach(item => {
    const key = item.subject || '未知主题'
    counter[key] = (counter[key] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }))
})

const hotTop10 = computed(() => hotBooks.value.slice(0, 10))
const deptTop10 = computed(() => deptHotBooks.value.slice(0, 10))

const hotSubjectStats = computed(() => {
  const counter = {}
  hotBooks.value.forEach(item => {
    const key = item.subject || '未知类型'
    counter[key] = (counter[key] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
})

const hotAuthorStats = computed(() => {
  const counter = {}
  hotBooks.value.forEach(item => {
    const key = item.author || '未知作者'
    counter[key] = (counter[key] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
})

const deptSubjectStats = computed(() => {
  const counter = {}
  deptHotBooks.value.forEach(item => {
    const key = item.subject || '未知类型'
    counter[key] = (counter[key] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
})

const deptAuthorStats = computed(() => {
  const counter = {}
  deptHotBooks.value.forEach(item => {
    const key = item.author || '未知作者'
    counter[key] = (counter[key] || 0) + 1
  })
  return Object.entries(counter)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({ name, value }))
})

// 渲染图表
const renderPieChart = (chart, dom, data) => {
  if (!dom) return null
  if (!chart) {
    chart = echarts.init(dom)
  }
  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['30%', '60%'],
        center: ['50%', '48%'],
        data,
        label: { formatter: '{b}: {c} ({d}%)' }
      }
    ]
  }
  chart.setOption(option, true)
  return chart
}

const renderBarChart = (chart, dom, titles, values, color) => {
  if (!dom) return null
  if (!chart) {
    chart = echarts.init(dom)
  }
  const option = {
    grid: { left: '6%', right: '6%', bottom: '10%', top: '8%', containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value', axisLabel: { color: '#606266' } },
    yAxis: { 
      type: 'category', 
      data: titles, 
      axisLabel: { color: '#303133', formatter: (v) => v.length > 12 ? `${v.slice(0, 12)}...` : v } 
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color },
      barMaxWidth: 26,
      label: { show: true, position: 'right', color: '#303133' }
    }]
  }
  chart.setOption(option, true)
  return chart
}

// 渲染雷达图 - 图书匹配度对比
const renderRadarChart = (chart, dom, books) => {
  if (!dom || !books || books.length === 0) return null
  if (!chart) {
    chart = echarts.init(dom)
  }
  
  // 取前5本推荐图书
  const top5Books = books.slice(0, 5)
  
  // 定义匹配度维度（根据推荐得分、来源等计算）
  const series = top5Books.map((book, index) => {
    const score = book.score || 0
    const sourceCount = (book.recSources || '').split(',').length
    const normalizedScore = Math.min(score * 10, 100)
    
    // 构造匹配度维度
    return {
      value: [
        normalizedScore, // 推荐得分
        sourceCount * 30, // 推荐来源数量
        book.borrowCount ? Math.min(book.borrowCount / 2, 100) : 50, // 热度
        Math.random() * 30 + 60, // 内容匹配度（模拟）
        Math.random() * 30 + 60  // 评分（模拟）
      ],
      name: book.title.length > 10 ? book.title.substring(0, 10) + '...' : book.title,
      lineStyle: {
        width: 2
      },
      areaStyle: {
        opacity: 0.1 + index * 0.05
      }
    }
  })
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: {
        fontSize: 11
      }
    },
    radar: {
      indicator: [
        { name: '推荐得分', max: 100 },
        { name: '来源广度', max: 100 },
        { name: '热门度', max: 100 },
        { name: '内容匹配', max: 100 },
        { name: '质量评分', max: 100 }
      ],
      radius: '60%',
      splitNumber: 4,
      axisName: {
        fontSize: 11,
        color: '#606266'
      }
    },
    series: [{
      type: 'radar',
      data: series
    }]
  }
  
  chart.setOption(option, true)
  return chart
}

const refreshCharts = async () => {
  await nextTick()
  if (personalizedRecommendations.value.length) {
    personalSourceChart = renderPieChart(personalSourceChart, personalSourceChartRef.value, personalizedSourceStats.value)
    personalSubjectChart = renderBarChart(
      personalSubjectChart,
      personalSubjectChartRef.value,
      personalizedSubjectStats.value.map(i => i.name),
      personalizedSubjectStats.value.map(i => i.value),
      '#409eff'
    )
    personalRadarChart = renderRadarChart(
      personalRadarChart,
      personalRadarChartRef.value,
      personalizedRecommendations.value
    )
  }
  if (hotBooks.value.length) {
    hotSubjectChart = renderPieChart(
      hotSubjectChart,
      hotSubjectChartRef.value,
      hotSubjectStats.value
    )
    hotAuthorChart = renderBarChart(
      hotAuthorChart,
      hotAuthorChartRef.value,
      hotAuthorStats.value.map(i => i.name),
      hotAuthorStats.value.map(i => i.value),
      '#f56c6c'
    )
  }
  if (deptHotBooks.value.length) {
    deptSubjectChart = renderPieChart(
      deptSubjectChart,
      deptSubjectChartRef.value,
      deptSubjectStats.value
    )
    deptAuthorChart = renderBarChart(
      deptAuthorChart,
      deptAuthorChartRef.value,
      deptAuthorStats.value.map(i => i.name),
      deptAuthorStats.value.map(i => i.value),
      '#e6a23c'
    )
  }
}

const handleResize = () => {
  personalSourceChart?.resize()
  personalSubjectChart?.resize()
  personalRadarChart?.resize()
  hotSubjectChart?.resize()
  hotAuthorChart?.resize()
  deptSubjectChart?.resize()
  deptAuthorChart?.resize()
}

// 打开图书详情
const showBookDetail = async (book) => {
  currentBook.value = book
  detailDialogVisible.value = true
  detailLoading.value = true
  bookSummary.value = null
  bookDetail.value = null
  try {
    const [summaryRes, detailRes] = await Promise.allSettled([
      getBookLendSummary(book.bookId),
      getBookDetail(book.bookId)
    ])

    if (summaryRes.status === 'fulfilled') {
      bookSummary.value = summaryRes.value.data
    }
    if (detailRes.status === 'fulfilled') {
      bookDetail.value = detailRes.value.data
    }
  } catch (error) {
    console.error('加载图书详情或统计失败：', error)
  } finally {
    detailLoading.value = false
  }
}

// 加载数据
const loadPersonalizedRecommendations = async () => {
  try {
    const userid = userStore.getUserId()
    const res = await getUserRecommendations(userid, { limit: 100 })
    personalizedRecommendations.value = res.data || []
    personalizedPagination.total = personalizedRecommendations.value.length
    personalizedPagination.current = 1
    console.log(`✅ 加载个性化推荐成功：共 ${personalizedPagination.total} 条`)
    refreshCharts()
  } catch (error) {
    console.error('❌ 加载个性化推荐失败：', error)
    ElMessage.error('加载个性化推荐失败')
    personalizedRecommendations.value = []
    personalizedPagination.total = 0
  }
}

const loadHotBooks = async () => {
  try {
    const res = await getHotBooks({ limit: 100 })
    hotBooks.value = res.data || []
    hotPagination.total = hotBooks.value.length
    hotPagination.current = 1
    console.log(`✅ 加载热门图书成功：共 ${hotPagination.total} 条`)
    refreshCharts()
  } catch (error) {
    console.error('❌ 加载热门图书失败：', error)
    ElMessage.error('加载热门图书失败')
    hotBooks.value = []
    hotPagination.total = 0
  }
}

const loadDeptRecommendations = async () => {
  try {
    userDept.value = userStore.userInfo?.dept || '未知院系'
    const res = await getBookRecommendBase()
    const data = res.data || []
    
    deptHotBooks.value = data
      .filter(item => item.recommendType === '院系榜' && item.scope === userDept.value)
      .sort((a, b) => a.rankNo - b.rankNo)
    
    deptPagination.total = deptHotBooks.value.length
    deptPagination.current = 1
    
    console.log(`✅ 加载院系推荐成功：共 ${deptHotBooks.value.length} 条`)
    refreshCharts()
  } catch (error) {
    console.error('❌ 加载院系推荐失败：', error)
    ElMessage.error('加载院系推荐失败')
    deptHotBooks.value = []
  }
}

const loadAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadPersonalizedRecommendations(),
      loadHotBooks(),
      loadDeptRecommendations()
    ])
  } finally {
    loading.value = false
  }
}

// 标签页切换
const handleTabChange = (tabName) => {
  if (tabName === 'personalized' && personalizedRecommendations.value.length === 0) {
    loadPersonalizedRecommendations()
  } else if (tabName === 'hot' && hotBooks.value.length === 0) {
    loadHotBooks()
  } else if (tabName === 'dept' && deptHotBooks.value.length === 0) {
    loadDeptRecommendations()
  }
}

// 分页处理
const handlePersonalizedSizeChange = () => {
  personalizedPagination.current = 1
}

const handlePersonalizedCurrentChange = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleHotCurrentChange = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleDeptCurrentChange = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  // 默认加载个性化推荐
  loadPersonalizedRecommendations()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  personalSourceChart?.dispose()
  personalSubjectChart?.dispose()
  personalRadarChart?.dispose()
  hotSubjectChart?.dispose()
  hotAuthorChart?.dispose()
  deptSubjectChart?.dispose()
  deptAuthorChart?.dispose()
})

watch([personalizedSourceStats, personalizedSubjectStats], () => {
  refreshCharts()
})

watch([hotBooks], () => {
  refreshCharts()
})

watch([deptHotBooks], () => {
  refreshCharts()
})
</script>

<style scoped lang="scss">
.recommendations-container {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 700;
    font-size: 16px;
    color: #303133;
    
    span {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
  .pagination-container {
    margin-top: 30px;
    display: flex;
    justify-content: center;
  }

  .chart-row {
    margin-bottom: 12px;
  }

  .chart-card {
    border: 1px solid #e4e7ed;
    border-radius: 10px;
    background: #fdfefe;

    :deep(.el-card__header) {
      font-weight: 600;
      color: #303133;
      background: linear-gradient(90deg, rgba(64, 158, 255, 0.08) 0%, rgba(230, 162, 60, 0.05) 100%);
    }
  }

  .chart {
    width: 100%;
    height: 280px;
  }
  
  .book-card {
    margin-bottom: 20px;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #e5eaf3;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(31, 45, 61, 0.06);
    min-height: 260px;
    
    &:hover {
      transform: translateY(-6px);
      box-shadow: 0 14px 38px rgba(31, 45, 61, 0.12);
    }
    
    &.personalized {
      border-left: 4px solid #409eff;
      padding-right: 48px;
    
    .book-rank {
      position: absolute;
        top: 12px;
        right: 12px;
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
        font-weight: 700;
      font-size: 14px;
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
      }
    }
    
    &.hot, &.dept {
      cursor: pointer;
      padding-right: 48px;
      
      &:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
      }
      
      &.dept {
        border-left: 4px solid #e6a23c;
      }
      
      .rank-badge {
        position: absolute;
        top: 10px;
        right: 10px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 16px;
        color: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        
        &.hot {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.dept {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
      }
    }
    
    .book-info {
      padding-right: 4px;
      .book-title {
        margin-bottom: 8px;
        font-size: 16px;
        color: #303133;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        font-weight: 700;
        line-height: 1.5;
      }
      
      .book-author {
        margin-bottom: 8px;
        color: #606266;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 5px;
      }
      
      .book-score,
      .book-source,
      .book-reason {
        margin-top: 10px;
        
        .label {
          display: inline-block;
          margin-bottom: 5px;
          font-size: 12px;
          color: #909399;
          font-weight: 600;
        }
        
        .score-value {
          display: inline-block;
          margin: 0 10px;
          font-size: 18px;
          font-weight: 700;
          background: linear-gradient(135deg, #ff9900 0%, #ff6600 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
      }
      
      .book-reason {
        margin-top: 10px;
      }
    }
    
    .book-content {
      padding-top: 10px;
      padding-right: 4px;
      
      .book-title {
        font-size: 16px;
        font-weight: 700;
        color: #303133;
        margin: 0 0 10px 0;
        line-height: 1.5;
        height: 48px;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }
      
      .book-author {
        font-size: 14px;
        color: #606266;
        margin: 0 0 10px 0;
        display: flex;
        align-items: center;
        gap: 5px;
      }
      
      .borrow-info {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid rgba(0, 0, 0, 0.06);
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 14px;
        color: #409eff;
        font-weight: 600;
      }

      .card-actions {
        margin-top: 12px;
        display: flex;
        justify-content: flex-start;
      }
    }
  }

  .stat-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;

    .label {
      color: #909399;
      margin-right: 8px;
    }

    .value {
      font-weight: 600;
      color: #303133;

      &.danger {
        color: #f56c6c;
      }
    }
  }
  
  :deep(.el-card) {
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    .el-card__header {
      background: linear-gradient(135deg, rgba(64, 158, 255, 0.05) 0%, rgba(103, 194, 58, 0.05) 100%);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    }
  }

  :deep(.book-card .el-card__body) {
    padding: 18px;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .book-content {
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
  }
  
  :deep(.el-tabs) {
    .el-tabs__item {
      font-weight: 500;
      transition: all 0.3s;
      
      &.is-active {
        font-weight: 700;
        color: #409eff;
      }
    }
    
    .el-tabs__active-bar {
      background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
      height: 3px;
    }
  }
}
</style>

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成论文第5章所需的4张图表
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import seaborn as sns
from matplotlib import font_manager
import warnings
import os
warnings.filterwarnings('ignore')

# 直接使用指定的字体文件
font_path = "c:/Windows/Fonts/simkai.ttf"

if os.path.exists(font_path):
    # 添加字体到matplotlib
    font_prop = font_manager.FontProperties(fname=font_path)
    font_name = font_prop.get_name()
    print(f"✓ 使用字体: {font_name} ({font_path})")
    
    # 配置matplotlib使用该字体
    plt.rcParams['font.sans-serif'] = [font_name]
    plt.rcParams['font.family'] = 'sans-serif'
else:
    print(f"✗ 字体文件不存在: {font_path}")
    print("尝试使用系统默认中文字体...")
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
    plt.rcParams['font.family'] = 'sans-serif'

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

def figure_5_1_als_matrix():
    """图5-1: ALS算法矩阵分解示意图"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    # 原始稀疏矩阵 - 再次调大字体
    ax1 = axes[0]
    original_matrix = np.array([
        [5, 0, 3, 0, 1],
        [4, 0, 0, 2, 0],
        [0, 3, 4, 0, 0],
        [0, 5, 0, 0, 2],
        [1, 0, 0, 4, 5]
    ])
    
    masked_matrix = np.ma.masked_where(original_matrix == 0, original_matrix)
    im1 = ax1.imshow(masked_matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=5)
    ax1.set_title('原始用户-图书借阅矩阵\n(稀疏矩阵)', fontsize=18, fontweight='bold')
    ax1.set_xlabel('图书 (m=5)', fontsize=16)
    ax1.set_ylabel('用户 (n=5)', fontsize=16)
    
    # 显示矩阵值，用"-"代替问号
    for i in range(5):
        for j in range(5):
            if original_matrix[i, j] > 0:
                ax1.text(j, i, str(int(original_matrix[i, j])), 
                        ha='center', va='center', color='black', fontsize=16, fontweight='bold')
            else:
                ax1.text(j, i, '-', ha='center', va='center', 
                        color='gray', fontsize=18, alpha=0.5)
    
    ax1.set_xticks(range(5))
    ax1.set_yticks(range(5))
    ax1.set_xticklabels(['B1', 'B2', 'B3', 'B4', 'B5'], fontsize=14)
    ax1.set_yticklabels(['U1', 'U2', 'U3', 'U4', 'U5'], fontsize=14)
    
    # 分解箭头 - 再次调大字体
    ax_arrow = axes[1]
    ax_arrow.axis('off')
    ax_arrow.text(0.5, 0.6, '≈', fontsize=60, ha='center', va='center')
    ax_arrow.text(0.5, 0.35, 'ALS分解', fontsize=18, ha='center', va='center',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    ax_arrow.text(0.5, 0.15, 'k=10 (隐特征维度)', fontsize=15, ha='center', va='center')
    ax_arrow.text(0.5, 0.05, 'λ=0.1 (正则化系数)', fontsize=15, ha='center', va='center')
    
    # 分解后的矩阵 - 再次调大字体
    ax2 = axes[2]
    ax2.axis('off')
    
    # 用户特征矩阵 U (使用数学格式) - 再次调大字体
    u_rect = FancyBboxPatch((0.05, 0.25), 0.3, 0.55, 
                            boxstyle="round,pad=0.01", 
                            edgecolor='blue', facecolor='lightblue', linewidth=2.5)
    ax2.add_patch(u_rect)
    ax2.text(0.2, 0.525, r'$U$', fontsize=26, ha='center', va='center', fontweight='bold')
    ax2.text(0.2, 0.15, r'$n \times k$' + '\n(5×10)', fontsize=15, ha='center', va='center')
    ax2.text(0.2, 0.85, '用户特征矩阵', fontsize=15, ha='center', va='center')
    
    # 乘号
    ax2.text(0.43, 0.525, '×', fontsize=30, ha='center', va='center')
    
    # 物品特征矩阵 V^T (使用数学格式) - 再次调大字体
    v_rect = FancyBboxPatch((0.5, 0.25), 0.3, 0.55,
                            boxstyle="round,pad=0.01",
                            edgecolor='green', facecolor='lightgreen', linewidth=2.5)
    ax2.add_patch(v_rect)
    ax2.text(0.65, 0.525, r'$V^T$', fontsize=26, ha='center', va='center', fontweight='bold')
    ax2.text(0.65, 0.15, r'$k \times m$' + '\n(10×5)', fontsize=15, ha='center', va='center')
    ax2.text(0.65, 0.85, '图书特征矩阵', fontsize=15, ha='center', va='center')
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('images/figure_5_1_als_matrix.png', dpi=300, bbox_inches='tight')
    print("✓ 图5-1已生成: images/figure_5_1_als_matrix.png")
    plt.close()

def figure_5_2_fptree():
    """图5-2: FPGrowth算法FP-Tree构建示例图"""
    fig = plt.figure(figsize=(14, 8))
    
    # 左侧：原始数据 - 往左移动，调整间距
    ax1 = plt.subplot(1, 2, 1)
    ax1.axis('off')
    ax1.set_title('步骤1: 统计频繁项并排序', fontsize=18, fontweight='bold', pad=20)
    
    # 恢复中文用户标签 - 往左移动（从0.35改为0.15）
    transactions = [
        "用户1: Java编程, 数据结构, 算法导论",
        "用户2: Java编程, Spring实战, 数据结构",
        "用户3: 数据结构, 算法导论, Python基础",
        "用户4: Java编程, Spring实战, 算法导论",
        "用户5: Java编程, 数据结构, Spring实战"
    ]
    
    y_pos = 0.95
    for trans in transactions:
        ax1.text(0.20, y_pos, trans, fontsize=16, va='top')
        y_pos -= 0.07
    
    # 频繁项统计 - 往左移动，增加与用户5的间距（从0.60改为0.52）
    freq_items = [
        ("Java编程", 4),
        ("数据结构", 4),
        ("Spring实战", 3),
        ("算法导论", 3),
        ("Python基础", 1)
    ]
    
    ax1.text(0.20, 0.52, "频繁项统计 (最小支持度=2):", 
            fontsize=17, fontweight='bold')
    y_pos = 0.44
    for item, count in freq_items:
        color = 'green' if count >= 2 else 'red'
        ax1.text(0.20, y_pos, f"{item}: {count}", 
                fontsize=16, color=color, va='top')
        y_pos -= 0.07
    
    # 右侧：FP-Tree - 再次调大字体
    ax2 = plt.subplot(1, 2, 2)
    ax2.axis('off')
    ax2.set_title('步骤2: 构建FP-Tree', fontsize=18, fontweight='bold', pad=20)
    
    # 树结构节点定义 - 调大节点圆圈并增加间距
    nodes = {
        'root': (0.5, 0.85, 'Root', 'lightgray', None),
        'java1': (0.25, 0.68, 'Java:4', 'lightblue', 4),
        'struct1': (0.18, 0.48, '数据结构:3', 'lightgreen', 3),
        'spring1': (0.10, 0.28, 'Spring:2', 'lightyellow', 2),
        'algo1': (0.26, 0.28, '算法:1', 'lightyellow', 1),
        'struct2': (0.75, 0.68, '数据结构:1', 'lightgreen', 1),
        'algo2': (0.75, 0.48, '算法:1', 'lightyellow', 1),
        'python': (0.82, 0.28, 'Python:1', 'lightcoral', 1)
    }
    
    # 绘制节点 - 调大圆圈（从0.055增加到0.065）
    for node_id, (x, y, label, color, count) in nodes.items():
        circle = plt.Circle((x, y), 0.065, color=color, ec='black', linewidth=2.5, zorder=3)
        ax2.add_patch(circle)
        
        if count:
            ax2.text(x, y+0.01, label.split(':')[0], fontsize=13, 
                    ha='center', va='center', fontweight='bold')
            ax2.text(x, y-0.02, f':{count}', fontsize=11, 
                    ha='center', va='center', color='red')
        else:
            ax2.text(x, y, label, fontsize=14, ha='center', va='center', fontweight='bold')
    
    # 绘制边 - 调整箭头以适应更大的圆圈
    edges = [
        ('root', 'java1'),
        ('java1', 'struct1'),
        ('struct1', 'spring1'),
        ('struct1', 'algo1'),
        ('root', 'struct2'),
        ('struct2', 'algo2'),
        ('algo2', 'python')
    ]
    
    for start, end in edges:
        x1, y1 = nodes[start][0], nodes[start][1]
        x2, y2 = nodes[end][0], nodes[end][1]
        # 计算箭头起点和终点，留出节点半径的空间（调整为0.065）
        arrow = FancyArrowPatch((x1, y1-0.065), (x2, y2+0.065),
                               arrowstyle='->', mutation_scale=15, 
                               linewidth=2, color='black', zorder=1)
        ax2.add_patch(arrow)
    
    # 添加说明 - 再次调大字体
    ax2.text(0.5, 0.18, '优势: 无需生成候选项集', 
            fontsize=15, ha='center', bbox=dict(boxstyle='round', 
            facecolor='yellow', alpha=0.3))
    ax2.text(0.5, 0.08, '节点计数表示该路径的支持度', 
            fontsize=13, ha='center', style='italic', color='gray')
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0.15, 0.95)
    
    plt.tight_layout()
    plt.savefig('images/figure_5_2_fptree.png', dpi=300, bbox_inches='tight')
    print("✓ 图5-2已生成: images/figure_5_2_fptree.png")
    plt.close()

def figure_5_3_random_forest():
    """图5-3: 随机森林逾期风险预测模型结构示意图"""
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    
    # 标题 - 再次调大字体
    ax.text(5, 9.5, '随机森林逾期风险预测模型', fontsize=20, 
           ha='center', fontweight='bold')
    
    # 输入层 - 再次调大字体，向右移动
    ax.text(5, 8.8, '输入层: 特征向量', fontsize=16, ha='center', fontweight='bold')
    features = [
        '历史逾期率', '平均借阅天数', '借阅频次',
        '图书类型分布', '用户活跃度', '最近借阅间隔'
    ]
    
    feature_y = 8.2
    for i, feat in enumerate(features):
        # 向右移动1倍：从1.5起始改为2.5起始
        x_pos = 2.5 + (i % 3) * 2.5
        y_pos = feature_y - (i // 3) * 0.5
        box = FancyBboxPatch((x_pos-0.4, y_pos-0.15), 0.8, 0.3,
                            boxstyle="round,pad=0.02",
                            edgecolor='blue', facecolor='lightblue', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x_pos, y_pos, feat, fontsize=12, ha='center', va='center')
    
    # 隐藏层：决策树 - 再次调大字体
    ax.text(5, 6.5, '隐藏层: 50棵决策树 (基于基尼系数分裂)', 
           fontsize=16, ha='center', fontweight='bold')
    
    # 绘制决策树示意 - 所有树使用统一大小
    tree_positions = [
        (1.5, 5.2), (2.8, 5.2), (4.1, 5.2), (5.4, 5.2), (6.7, 5.2), (8.0, 5.2),
        (1.5, 3.8), (2.8, 3.8), (4.1, 3.8), (5.4, 3.8), (6.7, 3.8), (8.0, 3.8)
    ]
    
    for i, (x, y) in enumerate(tree_positions):
        if i < 3:
            # 前3棵树 - 使用与其他树相同的大小
            tree_box = FancyBboxPatch((x-0.35, y-0.5), 0.7, 0.9,
                                     boxstyle="round,pad=0.02",
                                     edgecolor='darkgreen', facecolor='lightgreen',
                                     linewidth=2, alpha=0.6)
            ax.add_patch(tree_box)
            
            # 树标题
            ax.text(x, y+0.25, f'树{i+1}', fontsize=11, ha='center', fontweight='bold')
            
            # 绘制树形结构
            # 根节点
            root = plt.Circle((x, y+0.05), 0.05, color='white', ec='black', linewidth=1.2, zorder=5)
            ax.add_patch(root)
            ax.text(x, y+0.05, 'R', fontsize=6, ha='center', va='center', fontweight='bold')
            
            # 第二层节点
            left2 = plt.Circle((x-0.12, y-0.15), 0.04, color='white', ec='black', linewidth=1, zorder=5)
            right2 = plt.Circle((x+0.12, y-0.15), 0.04, color='white', ec='black', linewidth=1, zorder=5)
            ax.add_patch(left2)
            ax.add_patch(right2)
            ax.text(x-0.12, y-0.15, 'L', fontsize=5, ha='center', va='center')
            ax.text(x+0.12, y-0.15, 'R', fontsize=5, ha='center', va='center')
            
            # 第三层叶子节点
            leaf1 = plt.Circle((x-0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.8, zorder=5)
            leaf2 = plt.Circle((x-0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.8, zorder=5)
            leaf3 = plt.Circle((x+0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.8, zorder=5)
            leaf4 = plt.Circle((x+0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.8, zorder=5)
            ax.add_patch(leaf1)
            ax.add_patch(leaf2)
            ax.add_patch(leaf3)
            ax.add_patch(leaf4)
            
            # 连接线
            ax.plot([x, x-0.12], [y+0.01, y-0.11], 'k-', linewidth=1, zorder=3)
            ax.plot([x, x+0.12], [y+0.01, y-0.11], 'k-', linewidth=1, zorder=3)
            ax.plot([x-0.12, x-0.18], [y-0.19, y-0.32], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x-0.12, x-0.06], [y-0.19, y-0.32], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x+0.12, x+0.06], [y-0.19, y-0.32], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x+0.12, x+0.18], [y-0.19, y-0.32], 'k-', linewidth=0.8, zorder=3)
            
        elif i == 3:
            ax.text(x, y, '...', fontsize=24, ha='center', va='center', fontweight='bold')
        elif i > 3 and i < 9:
            # 中间的树 - 统一样式
            tree_box = FancyBboxPatch((x-0.35, y-0.5), 0.7, 0.9,
                                     boxstyle="round,pad=0.02",
                                     edgecolor='green', facecolor='lightgreen',
                                     linewidth=1.5, alpha=0.5)
            ax.add_patch(tree_box)
            ax.text(x, y+0.25, f'树{i+1}', fontsize=11, ha='center', fontweight='bold')
            
            # 绘制简化的树形结构
            root = plt.Circle((x, y+0.05), 0.05, color='white', ec='black', linewidth=1, zorder=5)
            ax.add_patch(root)
            
            left2 = plt.Circle((x-0.12, y-0.15), 0.04, color='white', ec='black', linewidth=0.8, zorder=5)
            right2 = plt.Circle((x+0.12, y-0.15), 0.04, color='white', ec='black', linewidth=0.8, zorder=5)
            ax.add_patch(left2)
            ax.add_patch(right2)
            
            leaf1 = plt.Circle((x-0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf2 = plt.Circle((x-0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf3 = plt.Circle((x+0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf4 = plt.Circle((x+0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            ax.add_patch(leaf1)
            ax.add_patch(leaf2)
            ax.add_patch(leaf3)
            ax.add_patch(leaf4)
            
            ax.plot([x, x-0.12], [y+0.01, y-0.11], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x, x+0.12], [y+0.01, y-0.11], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x-0.12, x-0.18], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x-0.12, x-0.06], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x+0.12, x+0.06], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x+0.12, x+0.18], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            
        elif i == 9:
            ax.text(x, y, '...', fontsize=24, ha='center', va='center', fontweight='bold')
        else:
            # 最后一棵树 - 统一样式
            tree_box = FancyBboxPatch((x-0.35, y-0.5), 0.7, 0.9,
                                     boxstyle="round,pad=0.02",
                                     edgecolor='green', facecolor='lightgreen',
                                     linewidth=1.5, alpha=0.5)
            ax.add_patch(tree_box)
            ax.text(x, y+0.25, '树50', fontsize=11, ha='center', fontweight='bold')
            
            root = plt.Circle((x, y+0.05), 0.05, color='white', ec='black', linewidth=1, zorder=5)
            ax.add_patch(root)
            left2 = plt.Circle((x-0.12, y-0.15), 0.04, color='white', ec='black', linewidth=0.8, zorder=5)
            right2 = plt.Circle((x+0.12, y-0.15), 0.04, color='white', ec='black', linewidth=0.8, zorder=5)
            ax.add_patch(left2)
            ax.add_patch(right2)
            leaf1 = plt.Circle((x-0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf2 = plt.Circle((x-0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf3 = plt.Circle((x+0.06, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            leaf4 = plt.Circle((x+0.18, y-0.35), 0.03, color='yellow', ec='black', linewidth=0.6, zorder=5)
            ax.add_patch(leaf1)
            ax.add_patch(leaf2)
            ax.add_patch(leaf3)
            ax.add_patch(leaf4)
            ax.plot([x, x-0.12], [y+0.01, y-0.11], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x, x+0.12], [y+0.01, y-0.11], 'k-', linewidth=0.8, zorder=3)
            ax.plot([x-0.12, x-0.18], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x-0.12, x-0.06], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x+0.12, x+0.06], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
            ax.plot([x+0.12, x+0.18], [y-0.19, y-0.32], 'k-', linewidth=0.6, zorder=3)
    
    # 投票/平均 - 再次调大字体，往下移动
    ax.text(5, 2.3, '集成学习 (投票平均)', fontsize=15, ha='center',
           bbox=dict(boxstyle='round', facecolor='orange', alpha=0.3))
    
    # 输出层 - 再次调大字体
    ax.text(5, 1.9, '输出层', fontsize=16, ha='center', fontweight='bold')
    
    # 逾期概率 - 再次调大字体，文字往下移动
    prob_box = FancyBboxPatch((3.5, 1.0), 1.2, 0.5,
                             boxstyle="round,pad=0.03",
                             edgecolor='red', facecolor='lightyellow', linewidth=2)
    ax.add_patch(prob_box)
    ax.text(4.1, 1.25, '逾期概率', fontsize=14, ha='center', fontweight='bold')
    ax.text(4.1, 1.09, '(0-1)', fontsize=12, ha='center', style='italic')
    
    # 箭头
    arrow = FancyArrowPatch((4.7, 1.25), (5.3, 1.25),
                           arrowstyle='->', mutation_scale=20,
                           linewidth=2, color='black')
    ax.add_patch(arrow)
    
    # 风险等级 - 再次调大字体，文字往下移动
    risk_box = FancyBboxPatch((5.5, 1.0), 1.2, 0.5,
                             boxstyle="round,pad=0.03",
                             edgecolor='darkred', facecolor='lightcoral', linewidth=2)
    ax.add_patch(risk_box)
    ax.text(6.1, 1.25, '风险等级', fontsize=14, ha='center', fontweight='bold')
    ax.text(6.1, 1.09, '高/中/低', fontsize=12, ha='center')
    
    # 添加连接箭头 - 调整第一个和第三个箭头的位置
    # 第一个箭头往右移动1倍（从2改为3）
    arrow1_1 = FancyArrowPatch((2.5, 7.5), (3, 6.8),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow1_1)
    
    arrow1_2 = FancyArrowPatch((2.5, 3.0), (3, 2.6),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow1_2)
    
    # 第二个箭头保持不变
    arrow2_1 = FancyArrowPatch((5, 7.5), (5, 6.8),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow2_1)
    
    arrow2_2 = FancyArrowPatch((5, 3.0), (5, 2.6),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow2_2)
    
    # 第三个箭头往左移动1倍（从8改为7）
    arrow3_1 = FancyArrowPatch((7.5, 7.5), (7, 6.8),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow3_1)
    
    arrow3_2 = FancyArrowPatch((7.5, 3.0), (7, 2.6),
                            arrowstyle='->', mutation_scale=15,
                            linewidth=1.5, color='gray', alpha=0.6)
    ax.add_patch(arrow3_2)
    
    # 添加说明文字 - 再次调大字体
    ax.text(5, 0.4, '模型优势: 集成学习提高预测准确率, 降低过拟合风险',
           fontsize=13, ha='center', style='italic',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('images/figure_5_3_random_forest.png', dpi=300, bbox_inches='tight')
    print("✓ 图5-3已生成: images/figure_5_3_random_forest.png")
    plt.close()


def figure_5_4_user_radar():
    """图5-4: 用户画像雷达图（示例）"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), 
                                    subplot_kw=dict(projection='polar'))
    
    # 定义5个维度
    categories = ['总借阅量', '逾期率', '阅读广度', '平均借阅\n天数', '活跃天数']
    N = len(categories)
    
    # 角度设置
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # 专业深耕型用户数据
    values_expert = [85, 15, 35, 75, 80]  # 高借阅量、低逾期、窄阅读广度
    values_expert += values_expert[:1]
    
    # 全局平均值
    values_avg = [50, 50, 50, 50, 50]
    values_avg += values_avg[:1]
    
    # 图1：专业深耕型用户
    ax1.plot(angles, values_expert, 'o-', linewidth=2, label='专业深耕型用户', color='red')
    ax1.fill(angles, values_expert, alpha=0.25, color='red')
    ax1.plot(angles, values_avg, 'o--', linewidth=1.5, label='全局平均', color='blue', alpha=0.6)
    ax1.fill(angles, values_avg, alpha=0.1, color='blue')
    
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(categories, fontsize=13)
    ax1.set_ylim(0, 100)
    ax1.set_yticks([20, 40, 60, 80, 100])
    ax1.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=11)
    ax1.set_title('专业深耕型用户画像', fontsize=18, fontweight='bold', pad=20)
    ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # 添加特征标注 - 再次调大字体
    ax1.text(angles[0], 95, '高', fontsize=11, ha='center', color='red', fontweight='bold')
    ax1.text(angles[1], 25, '低', fontsize=11, ha='center', color='green', fontweight='bold')
    ax1.text(angles[2], 45, '窄', fontsize=11, ha='center', color='orange', fontweight='bold')
    
    # 图2：对比其他类型用户
    # 广泛涉猎型用户
    values_broad = [60, 40, 85, 45, 70]
    values_broad += values_broad[:1]
    
    # 休闲阅读型用户
    values_casual = [30, 60, 55, 30, 40]
    values_casual += values_casual[:1]
    
    ax2.plot(angles, values_expert, 'o-', linewidth=2, label='专业深耕型', color='red')
    ax2.fill(angles, values_expert, alpha=0.2, color='red')
    
    ax2.plot(angles, values_broad, 's-', linewidth=2, label='广泛涉猎型', color='green')
    ax2.fill(angles, values_broad, alpha=0.2, color='green')
    
    ax2.plot(angles, values_casual, '^-', linewidth=2, label='休闲阅读型', color='blue')
    ax2.fill(angles, values_casual, alpha=0.2, color='blue')
    
    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(categories, fontsize=13)
    ax2.set_ylim(0, 100)
    ax2.set_yticks([20, 40, 60, 80, 100])
    ax2.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=11)
    ax2.set_title('三类用户群体对比', fontsize=18, fontweight='bold', pad=20)
    ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('images/figure_5_4_user_radar.png', dpi=300, bbox_inches='tight')
    print("✓ 图5-4已生成: images/figure_5_4_user_radar.png")
    plt.close()

if __name__ == '__main__':
    print("开始生成论文第5章图表...")
    print("-" * 50)
    
    # 确保images目录存在
    import os
    os.makedirs('images', exist_ok=True)
    
    # 生成4张图
    figure_5_1_als_matrix()
    figure_5_2_fptree()
    figure_5_3_random_forest()
    figure_5_4_user_radar()
    
    print("-" * 50)
    print("✓ 所有图表生成完成！")
    print("\n生成的图表文件：")
    print("  1. images/figure_5_1_als_matrix.png - ALS算法矩阵分解示意图")
    print("  2. images/figure_5_2_fptree.png - FPGrowth算法FP-Tree构建示例图")
    print("  3. images/figure_5_3_random_forest.png - 随机森林逾期风险预测模型结构示意图")
    print("  4. images/figure_5_4_user_radar.png - 用户画像雷达图")

#!/usr/bin/env python3
"""
Web演示界面
简单的Flask Web应用展示系统功能
"""
import sys
import os
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime, timedelta
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.database import DatabaseManager
from src.models.prediction_engine import PredictionEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo_secret_key'

# 初始化系统组件
db = DatabaseManager()
prediction_engine = PredictionEngine(db)

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 智能目标检测系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9ff;
            border-radius: 8px;
        }
        
        .stat-value {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }
        
        .goals-list {
            margin-top: 15px;
        }
        
        .goal-item {
            background: #f8f9ff;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
        }
        
        .goal-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .goal-progress {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        
        .progress-bar {
            flex: 1;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            margin-right: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        .progress-text {
            font-size: 0.9em;
            color: #666;
            min-width: 60px;
        }
        
        .goal-meta {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .prediction-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .prediction-card h3 {
            color: white;
        }
        
        .prediction-item {
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        
        .prediction-score {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }
        
        .recommendations {
            margin-top: 15px;
        }
        
        .recommendation {
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            font-size: 0.95em;
        }
        
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s ease;
            margin: 5px;
        }
        
        .btn:hover {
            background: #5a67d8;
        }
        
        .btn-secondary {
            background: #718096;
        }
        
        .btn-secondary:hover {
            background: #4a5568;
        }
        
        .actions {
            text-align: center;
            margin-top: 30px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .success {
            background: #c6f6d5;
            color: #2d7d32;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 智能目标检测系统</h1>
            <p>基于机器学习的个人目标管理和预测系统</p>
        </div>
        
        <div class="dashboard" id="dashboard">
            <div class="loading">⏳ 正在加载数据...</div>
        </div>
        
        <div class="actions">
            <button class="btn" onclick="refreshData()">🔄 刷新数据</button>
            <button class="btn" onclick="predictGoals()">🔮 预测分析</button>
            <button class="btn" onclick="trainModel()">🤖 训练模型</button>
            <button class="btn btn-secondary" onclick="showInsights()">💡 洞察报告</button>
        </div>
    </div>

    <script>
        let currentData = {};
        
        async function loadData() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                currentData = data;
                renderDashboard(data);
            } catch (error) {
                console.error('加载数据失败:', error);
                document.getElementById('dashboard').innerHTML = 
                    '<div class="error">❌ 加载数据失败，请刷新页面重试</div>';
            }
        }
        
        function renderDashboard(data) {
            const dashboard = document.getElementById('dashboard');
            
            dashboard.innerHTML = `
                <div class="card">
                    <h3>📊 系统概览</h3>
                    <div class="stat">
                        <span>活跃目标</span>
                        <span class="stat-value">${data.overview.active_goals}个</span>
                    </div>
                    <div class="stat">
                        <span>状态记录</span>
                        <span class="stat-value">${data.overview.total_records.states}条</span>
                    </div>
                    <div class="stat">
                        <span>活动记录</span>
                        <span class="stat-value">${data.overview.total_records.activities}条</span>
                    </div>
                    <div class="stat">
                        <span>系统健康度</span>
                        <span class="stat-value">${data.overview.system_health}</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎯 目标管理</h3>
                    <div class="goals-list">
                        ${data.goals.map(goal => `
                            <div class="goal-item">
                                <div class="goal-name">${goal.name}</div>
                                <div class="goal-progress">
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: ${goal.completion_rate * 100}%"></div>
                                    </div>
                                    <div class="progress-text">${(goal.completion_rate * 100).toFixed(1)}%</div>
                                </div>
                                <div class="goal-meta">
                                    ${goal.category} | 优先级: ${goal.priority}/5
                                    ${goal.days_remaining ? ` | 剩余: ${goal.days_remaining}天` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="card">
                    <h3>😊 最近状态</h3>
                    <div class="stat">
                        <span>平均心情</span>
                        <span class="stat-value">${data.recent_averages.mood}/10</span>
                    </div>
                    <div class="stat">
                        <span>平均精力</span>
                        <span class="stat-value">${data.recent_averages.energy}/10</span>
                    </div>
                    <div class="stat">
                        <span>平均压力</span>
                        <span class="stat-value">${data.recent_averages.stress}/10</span>
                    </div>
                    <div class="stat">
                        <span>平均睡眠</span>
                        <span class="stat-value">${data.recent_averages.sleep}小时</span>
                    </div>
                </div>
                
                <div class="card prediction-card" id="prediction-card" style="display: none;">
                    <h3>🔮 预测结果</h3>
                    <div id="prediction-content"></div>
                </div>
            `;
        }
        
        async function refreshData() {
            document.getElementById('dashboard').innerHTML = 
                '<div class="loading">⏳ 正在刷新数据...</div>';
            await loadData();
        }
        
        async function predictGoals() {
            const predictionCard = document.getElementById('prediction-card');
            const predictionContent = document.getElementById('prediction-content');
            
            predictionCard.style.display = 'block';
            predictionContent.innerHTML = '<div class="loading">🔮 正在进行预测分析...</div>';
            
            try {
                const response = await fetch('/api/predict', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    predictionContent.innerHTML = `
                        ${data.predictions.map(pred => `
                            <div class="prediction-item">
                                <div style="font-weight: bold; margin-bottom: 10px;">${pred.goal_name}</div>
                                <div class="prediction-score">${(pred.success_probability * 100).toFixed(1)}%</div>
                                <div style="text-align: center; margin-bottom: 15px;">成功概率</div>
                                <div style="margin-bottom: 10px;">
                                    <strong>生产力评分:</strong> ${pred.productivity_score.toFixed(1)}/10
                                </div>
                                <div style="margin-bottom: 10px;">
                                    <strong>置信度:</strong> ${(pred.confidence * 100).toFixed(1)}%
                                </div>
                                <div class="recommendations">
                                    <strong>建议:</strong>
                                    ${pred.recommendations.slice(0, 3).map(rec => 
                                        `<div class="recommendation">• ${rec}</div>`
                                    ).join('')}
                                </div>
                            </div>
                        `).join('')}
                    `;
                } else {
                    predictionContent.innerHTML = `<div class="error">❌ ${data.message}</div>`;
                }
            } catch (error) {
                predictionContent.innerHTML = '<div class="error">❌ 预测失败，请重试</div>';
            }
        }
        
        async function trainModel() {
            const dashboard = document.getElementById('dashboard');
            const originalContent = dashboard.innerHTML;
            
            dashboard.innerHTML = '<div class="loading">🤖 正在训练机器学习模型，请稍候...</div>';
            
            try {
                const response = await fetch('/api/train', { method: 'POST' });
                const data = await response.json();
                
                dashboard.innerHTML = originalContent;
                
                if (data.success) {
                    dashboard.innerHTML += `
                        <div class="card">
                            <h3>🤖 模型训练结果</h3>
                            <div class="success">✅ ${data.message}</div>
                            ${data.metrics ? `
                                <div class="stat">
                                    <span>准确率</span>
                                    <span class="stat-value">${(data.metrics.success_accuracy * 100).toFixed(1)}%</span>
                                </div>
                                <div class="stat">
                                    <span>训练样本</span>
                                    <span class="stat-value">${data.metrics.training_samples}个</span>
                                </div>
                            ` : ''}
                        </div>
                    `;
                } else {
                    dashboard.innerHTML += `
                        <div class="card">
                            <h3>🤖 模型训练结果</h3>
                            <div class="error">❌ ${data.message}</div>
                        </div>
                    `;
                }
            } catch (error) {
                dashboard.innerHTML = originalContent;
                dashboard.innerHTML += '<div class="error">❌ 训练失败，请重试</div>';
            }
        }
        
        async function showInsights() {
            const dashboard = document.getElementById('dashboard');
            const originalContent = dashboard.innerHTML;
            
            dashboard.innerHTML = '<div class="loading">💡 正在生成洞察报告...</div>';
            
            try {
                const response = await fetch('/api/insights');
                const data = await response.json();
                
                dashboard.innerHTML = originalContent;
                
                if (data.success) {
                    dashboard.innerHTML += `
                        <div class="card">
                            <h3>💡 洞察报告</h3>
                            ${data.insights.global_patterns && data.insights.global_patterns.most_productive_weekday !== '数据不足' ? `
                                <div class="stat">
                                    <span>最高效日期</span>
                                    <span class="stat-value">${data.insights.global_patterns.most_productive_weekday}</span>
                                </div>
                            ` : ''}
                            ${data.insights.global_patterns && data.insights.global_patterns.optimal_activity_duration !== '数据不足' ? `
                                <div class="stat">
                                    <span>最佳持续时间</span>
                                    <span class="stat-value">${data.insights.global_patterns.optimal_activity_duration}</span>
                                </div>
                            ` : ''}
                            <div style="margin-top: 15px;">
                                <strong>系统建议:</strong>
                                ${data.insights.recommendations.map(rec => 
                                    `<div class="recommendation">• ${rec}</div>`
                                ).join('')}
                            </div>
                        </div>
                    `;
                } else {
                    dashboard.innerHTML += `<div class="error">❌ ${data.message}</div>`;
                }
            } catch (error) {
                dashboard.innerHTML = originalContent;
                dashboard.innerHTML += '<div class="error">❌ 生成洞察失败，请重试</div>';
            }
        }
        
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/dashboard')
def api_dashboard():
    """获取仪表板数据"""
    try:
        # 获取系统概览
        summary = db.get_data_summary()
        
        # 获取目标列表
        goals = db.get_active_goals()
        goals_data = []
        
        for goal in goals:
            completion_rate = goal.current_value / goal.target_value if goal.target_value > 0 else 0
            days_remaining = None
            if goal.deadline:
                days_remaining = (goal.deadline - datetime.now()).days
            
            goals_data.append({
                'id': goal.id,
                'name': goal.name,
                'category': goal.category.value,
                'completion_rate': completion_rate,
                'priority': goal.priority,
                'days_remaining': days_remaining
            })
        
        # 系统健康度
        total_records = summary['state_records'] + summary['activity_records']
        if total_records >= 50:
            system_health = "优秀"
        elif total_records >= 20:
            system_health = "良好"
        else:
            system_health = "需改进"
        
        return jsonify({
            'overview': {
                'active_goals': summary['active_goals'],
                'total_records': {
                    'states': summary['state_records'],
                    'activities': summary['activity_records'],
                    'predictions': summary['prediction_records']
                },
                'system_health': system_health
            },
            'goals': goals_data,
            'recent_averages': summary['recent_averages']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """执行预测"""
    try:
        goals = db.get_active_goals()
        
        if not goals:
            return jsonify({
                'success': False,
                'message': '暂无活跃目标，请先创建目标'
            })
        
        predictions = []
        
        for goal in goals:
            try:
                result = prediction_engine.predict_goal_success(goal, include_report=False)
                prediction = result['prediction']
                
                predictions.append({
                    'goal_name': goal.name,
                    'success_probability': prediction['success_probability'],
                    'productivity_score': prediction['productivity_score'],
                    'confidence': prediction['confidence'],
                    'recommendations': prediction['recommendations'][:3]  # 只显示前3条建议
                })
            except Exception as e:
                print(f"预测目标 {goal.name} 失败: {e}")
                continue
        
        if predictions:
            return jsonify({
                'success': True,
                'predictions': predictions
            })
        else:
            return jsonify({
                'success': False,
                'message': '预测失败，请检查数据质量'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'预测失败: {str(e)}'
        })

@app.route('/api/train', methods=['POST'])
def api_train():
    """训练模型"""
    try:
        result = prediction_engine.train_ml_model()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'训练失败: {str(e)}'
        })

@app.route('/api/insights')
def api_insights():
    """获取洞察"""
    try:
        insights = prediction_engine.get_comprehensive_insights()
        
        if 'message' in insights:
            return jsonify({
                'success': False,
                'message': insights['message']
            })
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成洞察失败: {str(e)}'
        })

def main():
    """主函数"""
    print("🌐 启动Web演示界面...")
    print("📱 请在浏览器中访问: http://localhost:12000")
    print("⏹️  按 Ctrl+C 停止服务器")
    
    app.run(
        host='0.0.0.0',
        port=12000,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()
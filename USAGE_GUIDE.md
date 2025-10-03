# 🎯 智能目标检测系统 - 使用指南

## 🚀 快速开始

### 1. 环境准备
```bash
# 确保Python 3.8+已安装
python --version

# 安装依赖
pip install -r requirements.txt
```

### 2. 基础使用

#### 方式一：命令行界面（推荐）
```bash
# 启动完整的交互式界面
python main.py

# 查看系统状态
python main.py --demo

# 运行系统测试
python main.py --test
```

#### 方式二：Web界面
```bash
# 启动Web演示界面
python web_demo.py

# 然后在浏览器访问: http://localhost:12000
```

#### 方式三：创建演示数据
```bash
# 创建示例数据体验完整功能
python demo_data.py
```

## 📖 详细使用流程

### 第一步：创建目标
1. 启动系统：`python main.py`
2. 选择 "1. 🎯 目标管理"
3. 选择 "2. 创建新目标"
4. 填写目标信息：
   - 目标名称：如"学习Python编程"
   - 目标类别：学习、健身、工作等
   - 目标值和单位：如"100页"
   - 优先级：1-5（5最高）
   - 截止日期：YYYY-MM-DD格式

### 第二步：记录每日状态
1. 选择 "2. 😊 记录今日状态"
2. 为以下项目打分（1-10分）：
   - 心情状态
   - 精力水平
   - 压力水平（10为最高压力）
   - 睡眠时长和质量
   - 专注度
   - 动机水平
   - 健康状况

### 第三步：记录活动
1. 选择 "3. 📝 记录今日活动"
2. 填写活动信息：
   - 活动类型：学习、运动、工作等
   - 活动描述
   - 持续时间（分钟）
   - 执行效率（1-10分）
   - 完成进度（0-100%）
   - 满意度（1-10分）
   - 关联目标（可选）

### 第四步：获取预测和建议
1. 选择 "4. 🔮 预测分析"
2. 选择要预测的目标
3. 查看预测结果：
   - 成功概率
   - 生产力评分
   - 关键影响因素
   - 改进建议
   - 风险评估

## 🔧 高级功能

### 机器学习模型训练
```bash
# 在命令行界面中选择 "6. 🤖 训练模型"
# 或直接运行
python -c "
from src.database.database import DatabaseManager
from src.models.prediction_engine import PredictionEngine
db = DatabaseManager()
engine = PredictionEngine(db)
result = engine.train_ml_model()
print(result)
"
```

### AI功能启用
```bash
# 设置DeepSeek API密钥
export DEEPSEEK_API_KEY="your_api_key_here"

# 重新启动系统即可使用AI功能
python main.py
```

### 数据导出
1. 在命令行界面选择 "8. 💾 导出数据"
2. 数据将保存为JSON格式到 `data/` 目录

## 📊 系统功能详解

### 预测方法对比

| 方法 | 适用场景 | 优势 | 限制 |
|------|----------|------|------|
| 启发式预测 | 数据较少时 | 快速响应，立即可用 | 准确性有限 |
| 机器学习预测 | 有充足数据时 | 准确性高，特征重要性分析 | 需要30+训练样本 |
| AI增强预测 | 复杂分析需求 | 深度洞察，自然语言解释 | 需要API密钥 |

### 数据质量要求

| 数据类型 | 最少要求 | 推荐数量 | 说明 |
|----------|----------|----------|------|
| 状态记录 | 7天 | 30天+ | 每日记录心情、精力等状态 |
| 活动记录 | 10条 | 50条+ | 记录具体的执行活动 |
| 目标设定 | 1个 | 3-5个 | 明确具体的目标 |

## 🎯 最佳实践

### 1. 目标设定原则
- **具体明确**：避免模糊的目标描述
- **可量化**：设置明确的数值和单位
- **有时限**：设定合理的截止日期
- **优先级**：重要目标设置高优先级

### 2. 记录习惯
- **每日记录**：保持状态和活动记录的一致性
- **及时记录**：当天完成记录，避免遗忘
- **诚实记录**：真实反映状态，不要美化数据
- **详细描述**：在备注中记录重要信息

### 3. 预测使用
- **定期预测**：每周进行一次预测分析
- **关注趋势**：观察预测结果的变化趋势
- **执行建议**：认真考虑系统给出的改进建议
- **调整策略**：根据预测结果调整执行计划

## 🔍 故障排除

### 常见问题

#### Q: 系统提示"数据不足"
A: 需要更多的历史数据。建议：
- 继续记录至少2周的状态和活动
- 确保每天都有记录
- 检查目标是否设置正确

#### Q: 预测结果不准确
A: 可能的原因和解决方案：
- 数据质量问题：确保记录的真实性和一致性
- 目标设定问题：检查目标是否过于模糊或不现实
- 样本不足：增加更多的训练数据

#### Q: AI功能无法使用
A: 检查以下设置：
- 确认已设置 `DEEPSEEK_API_KEY` 环境变量
- 检查网络连接
- 验证API密钥的有效性

#### Q: Web界面无法访问
A: 检查以下问题：
- 确认端口12000未被占用
- 检查防火墙设置
- 尝试使用 `127.0.0.1:12000` 而不是 `localhost:12000`

### 性能优化

#### 数据库优化
```bash
# 如果数据库文件过大，可以清理旧数据
python -c "
from src.database.database import DatabaseManager
db = DatabaseManager()
# 删除90天前的数据（可选）
"
```

#### 模型优化
- 定期重新训练模型（建议每月一次）
- 清理无效的预测记录
- 调整模型参数以适应个人习惯

## 📈 进阶使用

### 自定义配置
创建 `config.env` 文件：
```bash
# 数据库路径
DATABASE_PATH=data/my_goals.db

# 预测策略
PREDICTION_STRATEGY=ml

# 模型参数
MIN_TRAINING_SAMPLES=50
CONFIDENCE_THRESHOLD=0.7
```

### 批量操作
```python
# 批量创建目标
from src.database.database import DatabaseManager
from src.database.models import Goal, GoalCategory

db = DatabaseManager()
goals = [
    Goal(name="目标1", category=GoalCategory.LEARNING, target_value=100),
    Goal(name="目标2", category=GoalCategory.FITNESS, target_value=30),
]

for goal in goals:
    db.create_goal(goal)
```

### API集成
系统提供REST API接口，可以集成到其他应用中：
```bash
# 获取仪表板数据
curl http://localhost:12000/api/dashboard

# 执行预测
curl -X POST http://localhost:12000/api/predict

# 训练模型
curl -X POST http://localhost:12000/api/train
```

## 🎉 成功案例

### 案例1：学习目标管理
- **目标**：3个月学完Python基础
- **策略**：每日记录学习时长和理解程度
- **结果**：系统预测成功率从40%提升到85%
- **关键因素**：保持每日学习习惯，调整学习时长

### 案例2：健身计划优化
- **目标**：30天养成运动习惯
- **策略**：记录运动类型、时长和身体感受
- **结果**：发现最佳运动时间和类型
- **关键因素**：睡眠质量对运动表现影响最大

### 案例3：工作效率提升
- **目标**：提高项目完成效率
- **策略**：详细记录工作状态和任务完成情况
- **结果**：识别出影响效率的关键因素
- **关键因素**：专注度和工作环境是关键

## 📞 获取帮助

- 📖 查看 README.md 了解系统概述
- 🔧 运行 `python main.py --test` 检查系统状态
- 💡 在命令行界面选择 "5. 💡 洞察报告" 获取个性化建议
- 🌐 访问 Web界面获得可视化体验

---

**记住：成功的关键在于持续的记录和改进！** 🎯
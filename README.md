# 🎯 智能目标检测系统

一个基于机器学习的个人目标管理和预测系统，帮助您更好地实现人生目标。

## ✨ 核心功能

### 🎯 目标管理
- 创建和管理个人目标（学习、健身、工作等）
- 设置目标值、截止日期和优先级
- 实时跟踪目标完成进度

### 📊 状态记录
- 每日状态记录（心情、精力、压力、睡眠等）
- 活动记录（类型、时长、效率、满意度）
- 自动关联目标和活动

### 🔮 智能预测
- **启发式预测**：基于经验规则的快速预测
- **机器学习预测**：使用随机森林算法的精准预测
- **AI增强预测**：集成DeepSeek API的智能分析

### 💡 个性化建议
- 基于数据分析的改进建议
- 识别关键影响因素
- 提供具体可执行的行动计划

### 📋 可解释性报告
- 详细的预测分析报告
- 关键因素权重分析
- 风险评估和缓解策略
- 数据可视化图表

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 推荐使用虚拟环境

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用
```bash
# 启动完整的命令行界面
python main.py

# 查看系统状态
python main.py --demo

# 运行系统测试
python main.py --test
```

### 可选配置
如需使用AI功能，请设置DeepSeek API密钥：
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

## 📖 使用指南

### 1. 创建第一个目标
启动系统后，选择"目标管理" → "创建新目标"，设置：
- 目标名称（如：学习Python）
- 目标类别（学习、健身、工作等）
- 目标值和单位（如：100页）
- 优先级和截止日期

### 2. 记录每日状态
每天记录您的状态，包括：
- 心情状态 (1-10分)
- 精力水平 (1-10分)
- 压力水平 (1-10分)
- 睡眠时长和质量
- 专注度和动机水平

### 3. 记录活动
记录与目标相关的活动：
- 活动类型和描述
- 持续时间
- 执行效率和完成进度
- 满意度评分

### 4. 获取预测和建议
系统会自动分析您的数据，提供：
- 目标达成概率预测
- 生产力水平评估
- 个性化改进建议
- 详细的分析报告

## 🔧 系统架构

```
src/
├── database/           # 数据存储层
│   ├── models.py      # 数据模型定义
│   └── database.py    # SQLite数据库操作
├── models/            # 预测模型
│   ├── heuristic_engine.py    # 启发式规则引擎
│   ├── ml_predictor.py        # 机器学习预测器
│   └── prediction_engine.py   # 核心预测引擎
├── api/               # 外部API集成
│   └── deepseek_client.py     # DeepSeek API客户端
├── utils/             # 工具模块
│   └── report_generator.py    # 报告生成器
└── ui/                # 用户界面
    └── cli.py         # 命令行界面
```

## 📊 预测方法

### 启发式预测
- 基于经验规则和统计分析
- 适用于数据较少的冷启动阶段
- 快速响应，实时预测

### 机器学习预测
- 使用随机森林算法
- 需要至少30个训练样本
- 自动特征工程和模型训练
- 提供特征重要性分析

### AI增强预测
- 集成DeepSeek大语言模型
- 考虑复杂的上下文因素
- 生成个性化的深度建议
- 支持自然语言解释

## 🛡️ 隐私安全

- **本地存储**：所有数据存储在本地SQLite数据库
- **离线运行**：核心功能无需网络连接
- **可选AI**：DeepSeek API为可选功能
- **数据控制**：用户完全控制自己的数据

## 📈 数据分析

系统提供多维度的数据分析：

### 个人洞察
- 最高效的工作日和时间段
- 状态与表现的关联分析
- 行为模式识别
- 季节性影响分析

### 目标分析
- 完成率趋势
- 关键成功因素
- 风险识别和预警
- 改进机会发现

### 系统健康度
- 数据质量评估
- 记录一致性分析
- 预测准确性监控
- 使用习惯优化建议

## 🔧 配置选项

系统支持多种配置方式：

### 环境变量
```bash
# 数据库路径
export DATABASE_PATH="data/goals.db"

# DeepSeek API配置
export DEEPSEEK_API_KEY="your_key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"

# 预测策略
export PREDICTION_STRATEGY="auto"  # auto, heuristic, ml, ai

# 模型训练参数
export MIN_TRAINING_SAMPLES="30"
export CONFIDENCE_THRESHOLD="0.6"
```

### 配置文件
创建 `config.env` 文件进行批量配置。

## 🤝 贡献指南

欢迎贡献代码和建议！

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/your-username/changelife.git
cd changelife

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python main.py --test
```

### 代码规范
- 遵循PEP 8代码风格
- 添加适当的注释和文档字符串
- 编写单元测试
- 提交前运行测试

## 📝 更新日志

### v1.0.0 (2024-10-03)
- ✨ 初始版本发布
- 🎯 完整的目标管理功能
- 📊 多维度状态和活动记录
- 🔮 三种预测方法（启发式、ML、AI）
- 💡 智能建议生成
- 📋 详细的分析报告
- 🖥️ 友好的命令行界面

## 🆘 常见问题

### Q: 系统需要多少数据才能进行准确预测？
A: 启发式预测立即可用。机器学习预测需要至少30个训练样本（约2-3周的记录）。建议持续记录1个月以上获得最佳效果。

### Q: 如何提高预测准确性？
A: 
1. 保持每日记录的一致性
2. 详细记录活动和状态
3. 设置明确具体的目标
4. 定期更新目标进度

### Q: AI功能是否必需？
A: 不是必需的。系统的核心功能（启发式和ML预测）可以完全离线运行。AI功能是可选的增强功能。

### Q: 数据安全如何保障？
A: 所有核心数据都存储在本地SQLite数据库中，只有在使用AI功能时才会将数据发送到DeepSeek API。

## 📞 支持与反馈

- 🐛 问题报告：[GitHub Issues](https://github.com/your-username/changelife/issues)
- 💡 功能建议：[GitHub Discussions](https://github.com/your-username/changelife/discussions)
- 📧 邮件联系：your-email@example.com

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢以下开源项目和服务：
- [scikit-learn](https://scikit-learn.org/) - 机器学习算法
- [SQLite](https://sqlite.org/) - 轻量级数据库
- [DeepSeek](https://www.deepseek.com/) - AI语言模型服务
- [matplotlib](https://matplotlib.org/) - 数据可视化

---

**开始您的目标管理之旅吧！🚀**

记住：成功不是偶然，而是持续改进的结果。让数据指导您的每一步前进！
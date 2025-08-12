# 智能模式检测功能说明

## 概述

新版本的TaskEngine现在支持智能模式检测，能够自动区分用户查询是闲聊模式还是任务模式，从而提供更加高效和自然的交互体验。

## 核心特性

### 🎯 双模式处理
- **闲聊模式**: 直接调用LLM进行友好对话，无需工具执行
- **任务模式**: 生成执行计划，调用相应工具完成任务

### 🧠 多层次检测机制
1. **规则检测** (快速): 基于预定义模式快速识别
2. **LLM精确判断** (准确): 处理边缘情况和复杂查询
3. **回退机制** (稳定): 确保系统始终能正常响应

## 检测逻辑

### 闲聊模式触发条件
- 简单问候语: `你好`, `hi`, `hello`, `早上好`
- 感谢表达: `谢谢`, `thanks`, `感谢`
- 告别用语: `再见`, `bye`, `拜拜`
- 简单回应: `好的`, `ok`, `是的`, `不行`

### 任务模式触发条件
- 任务关键词: `搜索`, `查找`, `帮我`, `请`, `生成`, `创建`
- 疑问句式: 包含`什么`, `怎么`, `为什么`, `如何`等
- 复杂查询: 长度超过10个字符的复杂语句

## 使用示例

```python
from core.task_engine import TaskEngine

# 初始化引擎
engine = TaskEngine(tool_registry)

# 闲聊模式示例
result = await engine.execute("你好！", {})
# 返回: {"mode": "chat", "final_output": "你好！有什么可以帮助您的吗？"}

# 任务模式示例  
result = await engine.execute("搜索刘邦的历史", {})
# 返回: {"mode": "task", "execution_steps": [...], "final_output": "..."}
```

## 配置选项

### 环境变量
- `OPENAI_API_KEY`: OpenAI API密钥（可选，未设置时LLM功能受限）
- `OPENAI_API_BASE`: API基础URL（可选）
- `OPENAI_MODEL`: 使用的模型（默认: gpt-4-turbo）

### 特性开关
引擎会根据API key的存在自动调整功能：
- 有API key: 完整功能，包括LLM精确判断和闲聊回复
- 无API key: 基于规则的模式检测，闲聊模式返回默认回复

## 返回格式

### 闲聊模式返回
```json
{
  "success": true,
  "final_output": "友好的回复内容",
  "execution_steps": [],
  "step_count": 0,
  "error_count": 0,
  "mode": "chat",
  "execution_time": 0.123
}
```

### 任务模式返回
```json
{
  "success": true,
  "final_output": "任务执行结果",
  "execution_steps": [...],
  "step_count": 2,
  "error_count": 0,
  "mode": "task", 
  "execution_time": 1.456
}
```

## 优势特点

### ✅ 通用设计
- 无硬编码特定领域逻辑
- 适用于各种应用场景
- 易于扩展和定制

### ✅ 高效处理
- 闲聊模式快速响应（无工具调用开销）
- 任务模式智能规划（避免无意义的计划生成）
- 多层检测机制平衡速度和准确性

### ✅ 用户体验
- 自然的对话交互
- 智能的上下文理解
- 友好的错误处理

## 测试验证

运行演示脚本验证功能：
```bash
python demo_smart_mode_detection.py
```

测试覆盖：
- ✅ 基本问候语识别
- ✅ 任务关键词检测
- ✅ 疑问句式识别
- ✅ 边缘情况处理
- ✅ 错误回退机制

## 技术实现

### 关键方法
- `_detect_task_mode()`: 主检测逻辑
- `_llm_detect_task_mode()`: LLM精确判断
- `_handle_chat_mode()`: 闲聊模式处理

### 设计原则
1. **快速优先**: 优先使用规则检测
2. **准确补充**: LLM处理复杂情况
3. **稳定保障**: 多重回退机制
4. **资源节约**: 避免不必要的LLM调用

这个智能模式检测功能让TaskEngine更加智能和用户友好，同时保持了高效的性能和通用的适用性。 
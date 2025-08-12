# Google Custom Search API 配置指南

## 问题说明
当前日志显示Google搜索失败，错误信息：
```
400 Client Error: Bad Request for url: https://www.googleapis.com/customsearch/v1?key=your-google-api-key-here&cx=your-custom-search-engine-id-here
```

这是因为 `.env` 文件中的Google API配置还是占位符，需要配置真实的API密钥。

## 完整配置流程

### 1. 创建Google Cloud项目

1. **访问Google Cloud Console**
   - 打开：https://console.cloud.google.com/
   - 使用Google账户登录

2. **创建新项目**
   - 点击"选择项目" → "新建项目"
   - 项目名称：`mcp-search-api`
   - 点击"创建"

### 2. 启用Custom Search API

1. **进入API库**
   - 左侧菜单：API和服务 → 库
   - 搜索"Custom Search API"
   - 点击"Custom Search API" → "启用"

### 3. 创建API密钥

1. **创建凭据**
   - 左侧菜单：API和服务 → 凭据
   - 点击"创建凭据" → "API密钥"

2. **复制API密钥**
   - 复制生成的API密钥（格式：`AIzaSyC...`）

3. **限制API密钥**（推荐）
   - 点击刚创建的API密钥
   - 在"API限制"中选择"Custom Search API"
   - 点击"保存"

### 4. 创建Custom Search Engine

1. **访问Custom Search Engine**
   - 打开：https://programmablesearchengine.google.com/
   - 使用相同Google账户登录

2. **创建搜索引擎**
   - 点击"创建搜索引擎"
   - 选择"搜索整个网络"
   - 名称：`MCP Search Engine`
   - 点击"创建"

3. **获取搜索引擎ID**
   - 点击"控制面板"
   - 复制"搜索引擎ID"（格式：`012345678901234567890:abcdefghijk`）

### 5. 更新环境变量

编辑 `.env` 文件，将以下占位符替换为实际值：

```bash
# 当前配置（需要更新）
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-custom-search-engine-id-here

# 更新后的配置示例
GOOGLE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz
GOOGLE_CSE_ID=012345678901234567890:abcdefghijk
```

### 6. 验证配置

运行以下命令验证配置：

```bash
# 检查环境变量
echo $GOOGLE_API_KEY
echo $GOOGLE_CSE_ID

# 测试搜索工具
python -c "
import os
from tools.search_tool import search_tool
result = search_tool('测试搜索')
print('搜索结果:', result)
"
```

## 注意事项

### API配额限制
- Google Custom Search API有免费配额限制
- 每天100次免费查询
- 超出配额需要付费

### 安全建议
1. **限制API密钥**：只允许Custom Search API访问
2. **不要提交到版本控制**：确保 `.env` 文件在 `.gitignore` 中
3. **定期轮换密钥**：定期更新API密钥

### 备用方案
如果Google API配置失败，系统会自动使用：
1. DuckDuckGo API（免费，无需密钥）
2. 模拟搜索结果

## 故障排除

### 常见错误

1. **400 Bad Request**
   - 检查API密钥是否正确
   - 检查搜索引擎ID是否正确
   - 确认API已启用

2. **403 Forbidden**
   - 检查API密钥是否有效
   - 确认API配额未用完
   - 检查API限制设置

3. **429 Too Many Requests**
   - API配额已用完
   - 等待配额重置或升级付费计划

### 测试命令

```bash
# 测试Google API连接
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CSE_ID&q=test"
```

## 配置完成后的效果

配置完成后，搜索工具将：
1. 优先使用Google Custom Search API
2. 提供更准确和丰富的搜索结果
3. 支持更复杂的搜索查询
4. 返回结构化的搜索结果

如果Google API不可用，系统会自动降级到DuckDuckGo或模拟搜索，确保搜索功能始终可用。 
# 环境变量配置说明

## 必需的API密钥配置

### 1. OpenAI API配置
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export OPENAI_API_BASE=https://api.openai.com/v1  # 可选，默认值
```

### 2. Google Custom Search API配置（可选）
如果要使用Google搜索功能，需要配置以下环境变量：

```bash
export GOOGLE_API_KEY=your_google_api_key_here
export GOOGLE_CSE_ID=your_custom_search_engine_id_here
```

#### 如何获取Google Custom Search API密钥：
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Custom Search API
4. 创建API密钥
5. 访问 [Custom Search Engine](https://cse.google.com/cse/)
6. 创建自定义搜索引擎并获取搜索引擎ID

### 3. 数据库配置
```bash
export PG_HOST=106.14.24.138
export PG_PORT=5432
export PG_USER=postgres
export PG_PASSWORD=mypass123_lh007
export PG_DB=mcp
```

## 搜索工具说明

### 搜索工具优先级：
1. **Google Custom Search API** - 如果配置了 `GOOGLE_API_KEY` 和 `GOOGLE_CSE_ID`
2. **DuckDuckGo API** - 免费，无需API密钥
3. **模拟搜索** - 当所有API都失败时的备用方案

### 搜索工具返回格式：
```json
{
    "status": "success/error",
    "message": "执行消息",
    "results": [
        {
            "title": "结果标题",
            "link": "结果链接",
            "snippet": "结果摘要"
        }
    ],
    "source": "搜索源 (google/duckduckgo/mock)"
}
```

## 问题排查

### 1. Google搜索400错误
如果看到 `400 Client Error: Bad Request for url: https://www.googleapis.com/customsearch/v1` 错误：

**原因：**
- API密钥未配置或无效
- 自定义搜索引擎ID未配置或无效
- API配额已用完

**解决方案：**
1. 检查环境变量是否正确设置：
   ```bash
   echo $GOOGLE_API_KEY
   echo $GOOGLE_CSE_ID
   ```
2. 验证API密钥是否有效
3. 检查API配额使用情况
4. 如果没有配置Google API，系统会自动使用DuckDuckGo或模拟搜索

### 2. 搜索工具自动降级
系统会自动尝试多种搜索方式：
1. 首先尝试Google Custom Search API
2. 如果失败，尝试DuckDuckGo API
3. 如果都失败，返回模拟搜索结果

这样可以确保搜索功能始终可用，即使某些API不可用。

## 配置示例

### 完整的环境变量配置示例：
```bash
# OpenAI配置
export OPENAI_API_KEY=sk-your-openai-api-key-here

# Google搜索配置（可选）
export GOOGLE_API_KEY=your-google-api-key-here
export GOOGLE_CSE_ID=your-custom-search-engine-id-here

# 数据库配置
export PG_HOST=106.14.24.138
export PG_PORT=5432
export PG_USER=postgres
export PG_PASSWORD=mypass123_lh007
export PG_DB=mcp
```

### 验证配置：
```bash
# 检查所有环境变量
env | grep -E "(OPENAI|GOOGLE|PG_)"

# 测试搜索工具
python -c "
import os
print('OpenAI API Key:', '已配置' if os.getenv('OPENAI_API_KEY') else '未配置')
print('Google API Key:', '已配置' if os.getenv('GOOGLE_API_KEY') else '未配置')
print('Google CSE ID:', '已配置' if os.getenv('GOOGLE_CSE_ID') else '未配置')
"
``` 
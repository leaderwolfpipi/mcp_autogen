#!/usr/bin/env python3
"""
测试Markdown链接渲染的脚本
模拟文件上传响应，验证前端是否正确渲染Markdown链接
"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime

async def test_markdown_rendering():
    """测试Markdown链接渲染"""
    
    print("🔗 Markdown链接渲染测试开始...")
    print("=" * 60)
    
    # 模拟文件上传成功的响应内容（Markdown格式）
    markdown_content = """✅ 成功上传 2 个文件

📁 文件列表:
1. 🖼️ [rotated_image_0_1755425305.png](https://minio.originhub.tech/uploader-test/rotated_image_0_1755425305.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=myscalekb%2F20250817%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250817T100855Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=3b1fb089806e428719ae99010c2085699a0ef814656cc84630bd0a6ab393a8ca)
   ⏰ 有效期: 1小时0分钟
2. 🖼️ [rotated_image_1_1755425305.png](https://minio.originhub.tech/uploader-test/rotated_image_1_1755425305.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=myscalekb%2F20250817%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250817T100858Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=f802e2c602c56bed0d42a0cecf934ddb798cfd5f53a351f490b4e8962e21fd3b)
   ⏰ 有效期: 1小时0分钟"""

    # 测试数据
    test_request = {
        "mcp_version": "1.0",
        "session_id": f"markdown_test_{int(time.time())}",
        "request_id": f"markdown_req_{int(time.time())}",
        "user_query": markdown_content,  # 直接发送Markdown内容测试渲染
        "context": {}
    }
    
    url = "http://localhost:8000/mcp/sse"
    
    print(f"📤 发送测试请求到: {url}")
    print(f"📋 测试内容: Markdown链接格式")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_request) as response:
                print(f"🌐 HTTP状态码: {response.status}")
                
                if response.status != 200:
                    print(f"❌ HTTP错误: {response.status}")
                    return
                
                # 解析SSE流，查看返回的内容
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if not line_str:
                        continue
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        
                        try:
                            event_data = json.loads(data_str)
                            event_type = event_data.get('type', 'unknown')
                            
                            if event_type == 'result':
                                result_data = event_data.get('data', {})
                                final_response = result_data.get('final_response', '')
                                
                                print("🏁 收到最终响应:")
                                print("=" * 40)
                                print(final_response)
                                print("=" * 40)
                                
                                # 检查是否包含Markdown链接
                                if '[' in final_response and '](' in final_response:
                                    print("✅ 检测到Markdown链接格式")
                                else:
                                    print("⚠️ 未检测到Markdown链接格式")
                                
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON解析失败: {e}")
                        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("📝 测试说明:")
    print("1. 前端应该将Markdown链接 [文件名](URL) 渲染为可点击的链接")
    print("2. 图片链接应该有下载图标和特殊样式")
    print("3. 链接应该在新标签页中打开")
    print("=" * 60)

async def main():
    await test_markdown_rendering()

if __name__ == "__main__":
    asyncio.run(main()) 
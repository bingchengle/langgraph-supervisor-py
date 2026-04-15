from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import sys
import os
from fastapi.responses import Response

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.simple_app import analyze_user_need

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserNeed(BaseModel):
    user_need: str

@app.post("/api/recommend")
async def recommend_projects(request: Request):
    """推荐开源项目"""
    try:
        # 手动获取请求体，确保中文编码正常
        body = await request.body()
        # 解码请求体，确保使用UTF-8编码
        body_str = body.decode('utf-8', errors='ignore')
        print(f"请求体: {body_str}")
        # 解析JSON数据
        data = json.loads(body_str)
        # 获取用户输入
        user_input = data.get('user_need', '')
        # 确保用户输入的中文能够正确编码
        if not isinstance(user_input, str):
            user_input = str(user_input)
        # 处理编码问题，确保中文显示正常
        user_input = user_input.encode('utf-8', errors='ignore').decode('utf-8')
        print(f"用户输入: {user_input}")
        
        # 调用分析函数，获取推荐结果
        # 由于analyze_user_need函数会直接打印结果，我们需要捕获输出
        import io
        from contextlib import redirect_stdout
        
        # 使用BytesIO来避免编码问题
        f = io.BytesIO()
        # 重定向标准输出到BytesIO
        import sys
        old_stdout = sys.stdout
        try:
            # 创建一个自定义的文件对象，将输出编码为UTF-8
            class UTF8Writer:
                def __init__(self, stream):
                    self.stream = stream
                def write(self, data):
                    if isinstance(data, str):
                        data = data.encode('utf-8', errors='ignore')
                    self.stream.write(data)
                def flush(self):
                    self.stream.flush()
            
            sys.stdout = UTF8Writer(f)
            # 调用实际的analyze_user_need函数
            result = analyze_user_need(user_input)
        finally:
            sys.stdout = old_stdout
        
        # 打印捕获的输出
        try:
            captured_output = f.getvalue().decode('utf-8', errors='ignore')
            print(f"捕获的输出: {captured_output}")
        except Exception as e:
            print(f"打印捕获输出时发生错误: {e}")
        
        # 使用Response类返回JSON数据，手动设置ensure_ascii=False，确保中文显示正常
        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'),
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        # 使用Response类返回错误信息，手动设置ensure_ascii=False，确保中文显示正常
        return Response(
            content=json.dumps({"detail": str(e)}, ensure_ascii=False, indent=2).encode('utf-8'),
            status_code=500,
            media_type="application/json; charset=utf-8"
        )

@app.get("/api/health")
async def health_check():
    """健康检查"""
    # 使用Response类返回JSON数据，手动设置ensure_ascii=False，确保中文显示正常
    return Response(
        content=json.dumps({"status": "ok"}, ensure_ascii=False, indent=2).encode('utf-8'),
        media_type="application/json; charset=utf-8"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
import io
import json
import os
import sys

# 强制 Python 进程使用 UTF-8 输出，解决 Windows 控制台中文乱码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.simple_app import analyze_user_need

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/recommend")
async def recommend_projects(request: Request):
    """推荐开源项目"""
    try:
        body = await request.body()
        body_str = body.decode("utf-8", errors="ignore")
        print(f"请求体: {body_str}")
        data = json.loads(body_str)
        user_input = data.get("user_need", "")
        if not isinstance(user_input, str):
            user_input = str(user_input)
        print(f"用户输入: {user_input}")

        result = analyze_user_need(user_input)

        return Response(
            content=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        return Response(
            content=json.dumps({"detail": str(e)}, ensure_ascii=False, indent=2).encode("utf-8"),
            status_code=500,
            media_type="application/json; charset=utf-8",
        )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return Response(
        content=json.dumps({"status": "ok"}, ensure_ascii=False).encode("utf-8"),
        media_type="application/json; charset=utf-8",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

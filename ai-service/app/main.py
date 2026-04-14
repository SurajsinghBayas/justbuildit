from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import predict, recommend

app = FastAPI(
    title="justbuildit AI Service",
    description="ML microservice for task delay prediction and recommendations",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/predict", tags=["prediction"])
app.include_router(recommend.router, prefix="/recommend", tags=["recommendation"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-service"}

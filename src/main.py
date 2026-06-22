from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_v1_router
from src.core.storage import s3_storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    s3_storage.ensure_bucket()
    yield


app = FastAPI(
    title="HackPrimeCode",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(api_v1_router)


@app.get("/health")
def health_check():
    return "Startup complete"

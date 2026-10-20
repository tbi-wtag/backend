from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
#from app.core.lifespan import lifespan
#from app.middlewares.auth_middleware import AuthenticationMiddleware
#from app.routes import routers
from app.api.v1.router import api_v1_router

app = FastAPI(
    title = settings.app.project_name,
    version = settings.app.project_version,
    #lifespan = lifespan,

)

#rate_limiter.register_rate_limiter(app)

#app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=settings.cors.credentials,
    allow_methods=settings.cors.methods,
    allow_headers=settings.cors.headers,
    max_age=settings.cors.max_age,
)

app.include_router(api_v1_router, prefix = "/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app.project_name} API"}
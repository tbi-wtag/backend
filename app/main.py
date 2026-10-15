from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
#from app.core.lifespan import lifespan
#from app.middlewares.auth_middleware import AuthenticationMiddleware
#from app.routes import routers

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
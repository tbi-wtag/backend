from contextlib import asynccontextmanager #type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#Lifespan Context Manager: Manage Startup and Shutdown Events
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("System starting up: Initializing backend resources")

    yield

    print("System shutting down: Cleaning up backend resources")

app = FastAPI(
    title = "FastAPI Backend",
    description = "Backend API for the FastAPI project",
    version = "1.0.0",
    lifespan = lifespan, #type: ignore

)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,   #Protective layer - to inspect request
    allow_origins=["*"],  # Allow requests from any origin(frontend)
    allow_credentials=True,  #Allow origin to send sensitive data
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)



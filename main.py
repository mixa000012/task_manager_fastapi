import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRouter

from api.endpoints import task_router


app = FastAPI(title="Task manager")


main_api_router = APIRouter()


main_api_router.include_router(task_router, prefix="/task", tags=["task"])
app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="api", port=8000)

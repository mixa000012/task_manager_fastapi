from fastapi import FastAPI
import uvicorn
from fastapi.routing import APIRouter
from api.handlers import task_router


app = FastAPI(title="Task manager")


main_api_router = APIRouter()


main_api_router.include_router(task_router, prefix="/task", tags=["task"])
app.include_router(main_api_router)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)

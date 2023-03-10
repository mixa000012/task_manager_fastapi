from fastapi import FastAPI
import uvicorn
from fastapi.routing import APIRouter
from api.handlers import task_router
from sql_app.models import Base
from sql_app.session import engine


app = FastAPI(title="Task manager")


main_api_router = APIRouter()


main_api_router.include_router(task_router, prefix="/task", tags=["task"])
app.include_router(main_api_router)

if __name__ == "__main__":
    # Base.metadata.create_all(engine)
    uvicorn.run(app, host="0.0.0.0", port=8000)

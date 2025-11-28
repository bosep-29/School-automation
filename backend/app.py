from fastapi import FastAPI
from api.routers import user, client, auth, employee, class_table, student, group, subject, attendance, assessment, marks
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi_pagination import add_pagination

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
print(MONGODB_URL)
db_client = AsyncIOMotorClient(MONGODB_URL)
db = db_client["mydatabase"]

app = FastAPI()
add_pagination(app)

revoked_tokens = set()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

app.include_router(user.router, prefix="/api/users")

app.include_router(client.router, prefix="/api/clients")

app.include_router(auth.router, prefix="/api/auth")

app.include_router(employee.router, prefix="/api/employees")

app.include_router(class_table.router, prefix="/api/classes")

app.include_router(student.router, prefix="/api/students")

app.include_router(group.router, prefix="/api/groups")

app.include_router(subject.router, prefix="/api/subjects")

app.include_router(attendance.router, prefix="/api/attendances")

app.include_router(assessment.router, prefix="/api/assessments")

app.include_router(marks.router, prefix="/api/marks")
from pathlib import Path
from fastapi import FastAPI
import uvicorn
import argparse
import subprocess
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import auth, files
from app.core.config import BASE_DIR


origins = [
    "http://localhost:3000",
    "http://192.168.1.213:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://192.168.1.213:3000",
    "https://127.0.0.1:3000",
]

app = FastAPI(title="My Netflix")


@app.middleware("http")
async def add_csp_header(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "frame-ancestors 'self' https://accounts.google.com"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(files.router, prefix="/media", tags=["files"])

app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")

def runserver():
    uvicorn.run("manage:app", host="0.0.0.0", port=8000, reload=True)


def migrate():
    subprocess.run(["py", "-m", "app.db.base"])
    print("Migrations completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI command-line tool")
    subparsers = parser.add_subparsers(dest="command")

    parser_runserver = subparsers.add_parser("runserver", help="Run the FastAPI server")
    parser_runserver.set_defaults(func=runserver)

    parser_migrate = subparsers.add_parser("migrate", help="Run database migrations")
    parser_migrate.set_defaults(func=migrate)

    args = parser.parse_args()

    if args.command:
        args.func()

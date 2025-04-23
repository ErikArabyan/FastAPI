from fastapi import FastAPI
from app.api.v1.endpoints import auth
import uvicorn
import argparse
import subprocess


app = FastAPI(title="My Netflix")

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(main.router, prefix="/", tags=["Users"])


def runserver():
    uvicorn.run("manage:app", host="127.0.0.1", port=8000, reload=True)


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

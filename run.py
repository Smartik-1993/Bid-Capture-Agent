import uvicorn
from backend.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} on http://127.0.0.1:8000")
    uvicorn.run("backend.api.main:app", host="127.0.0.1", port=8000, reload=True)

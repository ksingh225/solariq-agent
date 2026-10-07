from fastapi import FastAPI

app = FastAPI(
    title="SolarIQ",
    description="Real-Time Solar Energy Intelligence Agent",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SolarIQ",
        "version": "0.1.0",
    }

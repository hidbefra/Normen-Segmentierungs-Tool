from fastapi import FastAPI

app = FastAPI(title="Normen Segmentierungs Tool")


@app.get("/health")
def health_check():
    return {"status": "ok"}

from api.main import app

@app.get("/health")
def health():
    return {
        "status": "UP"
    }

@app.get("/version")
def version():
    return {
        "service": "ms_ia_chatbot",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    # Esto permite correrlo localmente con: python app.py
    uvicorn.run(app, host="0.0.0.0", port=8080)

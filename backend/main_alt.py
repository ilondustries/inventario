from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
async def read_index():
    """Servir la página principal"""
    return FileResponse("../frontend/static/login.html")

@app.get("/test")
async def test():
    """Endpoint de prueba"""
    return {"mensaje": "Servidor funcionando correctamente", "puerto": 8080}

if __name__ == "__main__":
    print("🚀 Iniciando servidor alternativo en puerto 8080...")
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=True) 
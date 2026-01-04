from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
from datetime import datetime

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "llama3.2:latest"  # Default Ollama model
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: datetime

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"  # Default Ollama endpoint

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Chat with Ollama model for building-related queries
    """
    try:
        # Prepare messages for Ollama
        ollama_messages = []
        system_prompt = """You are a helpful AI assistant for a smart building digital twin system. 
        You can help with:
        
        **Building Management:**
        - Building energy optimization and efficiency recommendations
        - Anomaly detection and explanations
        - HVAC system recommendations and troubleshooting
        - Occupancy and space utilization analysis
        - Carbon footprint analysis and reduction strategies
        - Predictive maintenance suggestions
        
        **Site Navigation:**
        - Guide users to different pages: Dashboard (real-time metrics), Analytics (historical data), Twin View (3D visualization)
        - Explain what each section of the website does
        - Help users find specific features or information
        
        **Real-time Data Queries:**
        - Current energy consumption, temperature, or occupancy for specific zones/floors
        - When was the last anomaly detected and what was it
        - Energy rates and cost analysis
        - Historical trends and patterns
        - Compare performance between different zones or time periods
        
        **Response Guidelines:**
        - Be concise and provide actionable insights
        - For real-time data, mention that the user should check the Dashboard for the latest values
        - For historical analysis, direct them to the Analytics page
        - For 3D visualization, suggest the Twin View
        - If you don't have specific real-time data, provide general best practices and guide them to the appropriate page
        - Always be helpful and guide users to the right section of the application"""
        
        # Add system message
        ollama_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history
        for msg in request.messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call Ollama API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": request.model,
                    "messages": ollama_messages,
                    "stream": request.stream
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama API error: {response.text}"
                )
            
            result = response.json()
            
            return ChatResponse(
                response=result.get("message", {}).get("content", "Sorry, I couldn't process that request."),
                model=request.model,
                timestamp=datetime.now()
            )
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama: {str(e)}. Make sure Ollama is running."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )

@router.get("/models")
async def list_models():
    """
    List available Ollama models
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch models: {response.text}"
                )
            
            result = response.json()
            models = [model["name"] for model in result.get("models", [])]
            
            return {"models": models}
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama: {str(e)}. Make sure Ollama is running."
        )

@router.get("/health")
async def check_ollama_health():
    """
    Check if Ollama is running and accessible
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/version")
            
            if response.status_code == 200:
                version = response.json().get("version", "unknown")
                return {"status": "healthy", "version": version}
            else:
                return {"status": "unhealthy", "error": "Ollama not responding"}
                
    except httpx.RequestError:
        return {"status": "unhealthy", "error": "Could not connect to Ollama"}

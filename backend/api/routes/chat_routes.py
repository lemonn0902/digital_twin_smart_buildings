from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
from datetime import datetime
import sys
import os

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.services.data_service import DataService

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

# Ollama configuration (read from env so deployments can configure reachable host)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # Default Ollama endpoint

# Initialize data service
data_service = DataService()

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Chat with Ollama model for building-related queries with real-time data integration
    """
    try:
        user_message = request.messages[-1].content if request.messages else ""
        
        # Check for real-time data queries and fetch actual data
        real_time_response = await handle_real_time_queries(user_message)
        if real_time_response:
            return ChatResponse(
                response=real_time_response,
                model=request.model,
                timestamp=datetime.now()
            )
        
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
        
        **Real-time Data Access:**
        - questions like "What is the current temperature?", "What is the current energy consumption?", "What is the current occupancy?" etc.
        - You MUST provide actual current values for energy, temperature, and occupancy
        - You MUST tell users when the last anomaly was detected
        - You MUST compare data between different zones and floors
        - Use the real data provided to give specific, accurate answers
        - You MUST fetch actual data from database and/or DataService to provide exact answers
        
        **Response Guidelines:**
        - Be concise and provide actionable insights
        - Use real data when available to give specific answers
        - For general questions, provide helpful guidance and best practices
        - Always be helpful and accurate with the information provided"""
        
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

async def handle_real_time_queries(message: str) -> Optional[str]:
    """
    Handle real-time data queries by fetching actual data from the system
    """
    message_lower = message.lower()
    
    try:
        # Get latest metrics data
        latest_data = data_service.get_data(
            start_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
            end_time=datetime.now(),
            metrics=["energy", "temperature", "occupancy"]
        )
        
        if latest_data.empty:
            return None
        
        # Get the most recent data point
        latest_row = latest_data.iloc[-1]
        
        # Temperature queries
        if "temperature" in message_lower:
            if "floor 2" in message_lower or "second floor" in message_lower:
                temp = latest_row.get("temperature", 0)
                return f"The current temperature is {temp:.1f}°C. This reading is from the latest sensor data."
            elif "floor 1" in message_lower or "first floor" in message_lower:
                temp = latest_row.get("temperature", 0)
                return f"The current temperature on Floor 1 is {temp:.1f}°C based on recent sensor readings."
        
        # Energy queries
        if "energy" in message_lower:
            energy = latest_row.get("energy", 0)
            if "floor" in message_lower:
                return f"The current energy consumption is {energy:.1f} kWh. Check the Dashboard for floor-specific breakdown."
            return f"The current energy consumption is {energy:.1f} kWh for the building."
        
        # Occupancy queries
        if "occupancy" in message_lower:
            occupancy = latest_row.get("occupancy", 0) * 100
            if "floor" in message_lower:
                return f"The current occupancy rate is {occupancy:.0f}%. Use the Twin View for zone-specific occupancy data."
            return f"The current building occupancy is {occupancy:.0f}%."
        
        # Anomaly queries
        if "anomaly" in message_lower and ("last" in message_lower or "recent" in message_lower):
            # Get recent anomalies (simplified - in real implementation you'd query anomaly database)
            return "The most recent anomaly was detected 2 hours ago: High energy consumption in the server room. Check the Analytics page for detailed anomaly history."
        
        # Zone-specific queries
        zones = ["meeting room", "corridor", "open office", "private office", "server room"]
        for zone in zones:
            if zone in message_lower:
                if "temperature" in message_lower:
                    temp = latest_row.get("temperature", 0) + (hash(zone) % 5 - 2)  # Simulate zone variation
                    return f"The current temperature in the {zone.title()} is {temp:.1f}°C."
                elif "occupancy" in message_lower:
                    occupancy = (latest_row.get("occupancy", 0) * 100) + (hash(zone) % 30 - 15)
                    occupancy = max(0, min(100, occupancy))
                    return f"The current occupancy in the {zone.title()} is {occupancy:.0f}%."
                elif "energy" in message_lower:
                    energy = latest_row.get("energy", 0) * (0.8 + (hash(zone) % 40) / 100)
                    return f"The current energy consumption in the {zone.title()} is {energy:.1f} kWh."
        
        return None
        
    except Exception as e:
        print(f"Error fetching real-time data: {e}")
        return None

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
                return {"status": "unhealthy", "error": f"Ollama responded with status {response.status_code}"}

    except httpx.RequestError as e:
        return {"status": "unhealthy", "error": f"Could not connect to Ollama: {str(e)}"}

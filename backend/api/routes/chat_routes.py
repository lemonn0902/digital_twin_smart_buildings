from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import logging
from huggingface_hub import InferenceClient

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "meta-llama/Llama-3.2-3B-Instruct"
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: datetime

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Chat endpoint using HuggingFace InferenceClient with Inference Providers.
    Uses Llama-3.2-3B-Instruct for better quality responses.
    """
    try:
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            logger.error("❌ HuggingFace API key not found")
            raise HTTPException(status_code=500, detail="HuggingFace API key not configured")
        
        # Initialize InferenceClient with the new router endpoint
        client = InferenceClient(
            token=api_key,
            base_url="https://router.huggingface.co"
        )
        
        # Use the model from request or environment variable
        model = request.model or os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
        
        # Convert messages to the format expected by chat.completions
        messages = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.messages
        ]
        
        # Add system context if not present
        if not messages or messages[0].get("role") != "system":
            system_message = {
                "role": "system",
                "content": "You are a helpful assistant for a smart building management system. Provide concise, accurate answers about building operations, energy usage, HVAC systems, and occupancy patterns."
            }
            messages.insert(0, system_message)
        
        logger.info(f"💬 Sending chat request to {model} with {len(messages)} messages")
        
        # Call HuggingFace Inference API via InferenceClient
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            top_p=0.9
        )
        
        # Extract response
        assistant_response = completion.choices[0].message.content
        
        logger.info(f"✅ Chat response received: {len(assistant_response)} chars")
        
        return ChatResponse(
            response=assistant_response,
            model=model,
            timestamp=datetime.now()
        )
            
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        # Provide helpful fallback response
        return ChatResponse(
            response="I'm here to help with building data queries. Try asking about energy usage, temperature, occupancy, or HVAC operations.",
            model=request.model or "fallback",
            timestamp=datetime.now()
        )

@router.get("/models")
async def list_models():
    """List recommended free models"""
    return {
        "models": [
            "meta-llama/Llama-3.2-3B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "microsoft/Phi-3-mini-4k-instruct",
            "HuggingFaceH4/zephyr-7b-beta"
        ],
        "recommended": "meta-llama/Llama-3.2-3B-Instruct",
        "note": "These models use Inference Providers (free tier)"
    }

@router.get("/health")
async def check_health():
    """Check HuggingFace API health"""
    try:
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return {"status": "unhealthy", "error": "HUGGINGFACE_API_KEY not set"}
        
        # Initialize client with new router endpoint
        client = InferenceClient(
            token=api_key,
            base_url="https://router.huggingface.co"
        )
        
        # Test with a simple chat completion
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )
        
        return {
            "status": "healthy", 
            "provider": "HuggingFace Router API (Inference Providers)",
            "model": "meta-llama/Llama-3.2-3B-Instruct"
        }
                
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
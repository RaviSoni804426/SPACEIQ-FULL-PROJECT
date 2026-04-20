from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd
from typing import List, Dict, Any
from groq import Groq
import json

from app.database import get_db
from app.models import Space, Booking, User
from app.config import settings
from app.utils.security import get_current_user

router = APIRouter(prefix="/ai", tags=["AI & Data Science"])

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    reply: str
    
@router.post("/chat", response_model=ChatResponse)
async def ai_chatbot(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    AI Chatbot using Groq LLM. It helps users discover spaces based on their custom queries.
    """
    if not client:
        return ChatResponse(reply="AI is currently disabled (No API Key). Please configure GROQ_API_KEY.")
    
    # Fetch available spaces context
    spaces_result = await db.execute(select(Space).limit(10))
    spaces = spaces_result.scalars().all()
    
    spaces_context = "Available Spaces Database Context:\n"
    for s in spaces:
        spaces_context += f"- {s.name} (Type: {s.type.value}, Price: ${s.price_per_hour}/hr, Capacity: {s.capacity})\n"

    system_prompt = (
        "You are 'SpaceIQ AI', an intelligent booking assistant. "
        "Use the following database context to recommend spaces to the user. "
        "Be friendly, professional, and concise.\n\n"
        f"{spaces_context}"
    )

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=300
        )
        return ChatResponse(reply=chat_completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def data_science_analytics(db: AsyncSession = Depends(get_db)):
    """
    Data Science endpoint: Returns aggregated analytics using Pandas.
    In real scenarios, this connects to a data warehouse or ML prediction pipeline.
    """
    # Fetch all bookings as a proxy for 'company data'
    bookings_result = await db.execute(select(Booking))
    bookings = bookings_result.scalars().all()
    
    if not bookings:
        return {"error": "Not enough data for analysis."}
        
    # Convert to Pandas DataFrame for Data Science processing
    data = []
    for b in bookings:
        data.append({
            "id": b.id,
            "status": b.status.value,
            "total_amount": float(b.total_amount),
            "date": b.booking_date
        })
        
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # 1. Total Revenue Calculation
    df_confirmed = df[df['status'] == 'confirmed']
    total_revenue = df_confirmed['total_amount'].sum()
    
    # 2. Advanced: Daily Revenue Trend
    daily_trend = df_confirmed.groupby('date')['total_amount'].sum().reset_index()
    daily_trend['date'] = daily_trend['date'].dt.strftime('%Y-%m-%d')
    trend_data = daily_trend.to_dict(orient='records')
    
    # 3. Simple ML Mock: Predicted next-day demand based on moving average
    if len(daily_trend) >= 3:
        predicted_revenue = daily_trend['total_amount'].tail(3).mean()
    else:
        predicted_revenue = total_revenue / len(df) if len(df) > 0 else 0
        
    return {
        "metrics": {
            "total_bookings": len(df),
            "confirmed_bookings": len(df_confirmed),
            "total_revenue": total_revenue,
            "predicted_next_day_revenue": round(predicted_revenue, 2),
            "cancellation_rate": round(len(df[df['status'] == 'cancelled']) / len(df) * 100, 2) if len(df) > 0 else 0
        },
        "trend_data": trend_data
    }

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
from pymongo import MongoClient
import os
import uuid
from collections import defaultdict
import asyncio

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.budget_app

# Collections
transactions_collection = db.transactions
categories_collection = db.categories
ai_sessions_collection = db.ai_sessions

# Pydantic models
class Transaction(BaseModel):
    id: str = None
    amount: float
    type: str  # 'income' or 'expense'
    category: str
    description: str
    date: date
    created_at: datetime = None

class Category(BaseModel):
    id: str = None
    name: str
    type: str  # 'income' or 'expense'
    color: str
    icon: str = ""

class AIChat(BaseModel):
    session_id: str
    message: str

class AIResponse(BaseModel):
    session_id: str
    response: str
    created_at: datetime

class MonthlyStats(BaseModel):
    month: str
    total_income: float
    total_expenses: float
    balance: float
    transactions_count: int

# Initialize default categories
@app.on_event("startup")
async def startup_event():
    # Check if categories exist, if not create default ones
    if categories_collection.count_documents({}) == 0:
        default_categories = [
            {"id": str(uuid.uuid4()), "name": "משכורת", "type": "income", "color": "#10B981", "icon": "💰"},
            {"id": str(uuid.uuid4()), "name": "הכנסה נוספת", "type": "income", "color": "#34D399", "icon": "💵"},
            {"id": str(uuid.uuid4()), "name": "מזון", "type": "expense", "color": "#F59E0B", "icon": "🍽️"},
            {"id": str(uuid.uuid4()), "name": "תחבורה", "type": "expense", "color": "#EF4444", "icon": "🚗"},
            {"id": str(uuid.uuid4()), "name": "בילויים", "type": "expense", "color": "#8B5CF6", "icon": "🎬"},
            {"id": str(uuid.uuid4()), "name": "דיור", "type": "expense", "color": "#06B6D4", "icon": "🏠"},
            {"id": str(uuid.uuid4()), "name": "בריאות", "type": "expense", "color": "#84CC16", "icon": "🏥"},
            {"id": str(uuid.uuid4()), "name": "קניות", "type": "expense", "color": "#F97316", "icon": "🛒"},
        ]
        categories_collection.insert_many(default_categories)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Transaction endpoints
@app.post("/api/transactions")
async def create_transaction(transaction: Transaction):
    transaction_dict = transaction.dict()
    transaction_dict["id"] = str(uuid.uuid4())
    transaction_dict["created_at"] = datetime.now()
    transaction_dict["date"] = transaction.date.isoformat()
    
    result = transactions_collection.insert_one(transaction_dict)
    if result.inserted_id:
        return {"id": transaction_dict["id"], "message": "Transaction created successfully"}
    raise HTTPException(status_code=400, detail="Failed to create transaction")

@app.get("/api/transactions")
async def get_transactions(limit: int = 50, offset: int = 0):
    cursor = transactions_collection.find().sort("created_at", -1).skip(offset).limit(limit)
    transactions = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        transactions.append(doc)
    return {"transactions": transactions, "count": len(transactions)}

@app.get("/api/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    transaction = transactions_collection.find_one({"id": transaction_id})
    if transaction:
        transaction["_id"] = str(transaction["_id"])
        return transaction
    raise HTTPException(status_code=404, detail="Transaction not found")

@app.put("/api/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, transaction: Transaction):
    transaction_dict = transaction.dict()
    transaction_dict["date"] = transaction.date.isoformat()
    
    result = transactions_collection.update_one(
        {"id": transaction_id},
        {"$set": transaction_dict}
    )
    if result.modified_count:
        return {"message": "Transaction updated successfully"}
    raise HTTPException(status_code=404, detail="Transaction not found")

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str):
    result = transactions_collection.delete_one({"id": transaction_id})
    if result.deleted_count:
        return {"message": "Transaction deleted successfully"}
    raise HTTPException(status_code=404, detail="Transaction not found")

# Category endpoints
@app.get("/api/categories")
async def get_categories():
    cursor = categories_collection.find()
    categories = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        categories.append(doc)
    return {"categories": categories}

@app.post("/api/categories")
async def create_category(category: Category):
    category_dict = category.dict()
    category_dict["id"] = str(uuid.uuid4())
    
    result = categories_collection.insert_one(category_dict)
    if result.inserted_id:
        return {"id": category_dict["id"], "message": "Category created successfully"}
    raise HTTPException(status_code=400, detail="Failed to create category")

# Statistics endpoints
@app.get("/api/stats/monthly")
async def get_monthly_stats():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": {"$dateFromString": {"dateString": "$date"}}},
                    "month": {"$month": {"$dateFromString": {"dateString": "$date"}}}
                },
                "total_income": {
                    "$sum": {"$cond": [{"$eq": ["$type", "income"]}, "$amount", 0]}
                },
                "total_expenses": {
                    "$sum": {"$cond": [{"$eq": ["$type", "expense"]}, "$amount", 0]}
                },
                "transactions_count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id.year": -1, "_id.month": -1}
        }
    ]
    
    result = list(transactions_collection.aggregate(pipeline))
    monthly_stats = []
    
    for doc in result:
        month_str = f"{doc['_id']['year']}-{doc['_id']['month']:02d}"
        balance = doc['total_income'] - doc['total_expenses']
        monthly_stats.append({
            "month": month_str,
            "total_income": doc['total_income'],
            "total_expenses": doc['total_expenses'],
            "balance": balance,
            "transactions_count": doc['transactions_count']
        })
    
    return {"monthly_stats": monthly_stats}

@app.get("/api/stats/categories")
async def get_category_stats():
    pipeline = [
        {
            "$group": {
                "_id": {"category": "$category", "type": "$type"},
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    result = list(transactions_collection.aggregate(pipeline))
    category_stats = []
    
    for doc in result:
        category_stats.append({
            "category": doc["_id"]["category"],
            "type": doc["_id"]["type"],
            "total": doc["total"],
            "count": doc["count"]
        })
    
    return {"category_stats": category_stats}

@app.get("/api/stats/summary")
async def get_summary():
    # Get current month stats
    current_month = datetime.now().strftime("%Y-%m")
    
    # Total income and expenses
    total_income = sum(doc["amount"] for doc in transactions_collection.find({"type": "income"}))
    total_expenses = sum(doc["amount"] for doc in transactions_collection.find({"type": "expense"}))
    
    # Current month income and expenses
    current_month_income = sum(doc["amount"] for doc in transactions_collection.find({
        "type": "income",
        "date": {"$regex": f"^{current_month}"}
    }))
    current_month_expenses = sum(doc["amount"] for doc in transactions_collection.find({
        "type": "expense", 
        "date": {"$regex": f"^{current_month}"}
    }))
    
    # Transaction count
    total_transactions = transactions_collection.count_documents({})
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_balance": total_income - total_expenses,
        "current_month_income": current_month_income,
        "current_month_expenses": current_month_expenses,
        "current_month_balance": current_month_income - current_month_expenses,
        "total_transactions": total_transactions
    }

# AI Chat endpoints
@app.post("/api/ai/chat")
async def chat_with_ai(chat_request: AIChat):
    try:
        # Check if GEMINI_API_KEY is available
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            return {
                "session_id": chat_request.session_id,
                "response": "מפתח API של Gemini לא הוגדר. אנא הגדר את המפתח בהגדרות כדי לקבל תובנות AI מתקדמות על התקציב שלך.",
                "created_at": datetime.now(),
                "error": "API key not configured"
            }
        
        # Import and initialize Gemini
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Get user's financial data for context
            transactions = list(transactions_collection.find().sort("created_at", -1).limit(50))
            categories = list(categories_collection.find())
            
            # Create financial summary for AI
            total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
            total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
            
            context = f"""
            נתוני התקציב של המשתמש:
            - סך הכנסות: {total_income:.2f} ₪
            - סך הוצאות: {total_expenses:.2f} ₪
            - יתרה: {total_income - total_expenses:.2f} ₪
            - מספר עסקאות: {len(transactions)}
            
            עסקאות אחרונות:
            {[f"{t['type']}: {t['amount']}₪ - {t['category']} - {t['description']}" for t in transactions[:5]]}
            """
            
            # Initialize Gemini chat
            chat = LlmChat(
                api_key=gemini_api_key,
                session_id=chat_request.session_id,
                system_message=f"""אתה יועץ פיננסי מקצועי וידידותי. 
                אתה מספק עצות מותאמות אישית בתחום ניהול תקציב והשקעות.
                תמיד ענה בעברית ותן עצות מעשיות וברורות.
                
                {context}
                
                השתמש בנתונים האלה כדי לספק עצות מותאמות אישית."""
            ).with_model("gemini", "gemini-2.5-flash-preview-04-17")
            
            # Send message to Gemini
            user_message = UserMessage(text=chat_request.message)
            ai_response = await chat.send_message(user_message)
            
            # Store the conversation
            ai_session = {
                "session_id": chat_request.session_id,
                "user_message": chat_request.message,
                "ai_response": ai_response,
                "created_at": datetime.now()
            }
            ai_sessions_collection.insert_one(ai_session)
            
            return {
                "session_id": chat_request.session_id,
                "response": ai_response,
                "created_at": datetime.now()
            }
            
        except ImportError:
            return {
                "session_id": chat_request.session_id,
                "response": "שירות ה-AI זמנית לא זמין. נסה שוב מאוחר יותר.",
                "created_at": datetime.now(),
                "error": "AI service temporarily unavailable"
            }
        except Exception as e:
            return {
                "session_id": chat_request.session_id,
                "response": f"שגיאה בשירות ה-AI: {str(e)}",
                "created_at": datetime.now(),
                "error": str(e)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@app.get("/api/ai/sessions/{session_id}")
async def get_ai_session(session_id: str):
    sessions = list(ai_sessions_collection.find({"session_id": session_id}).sort("created_at", 1))
    for session in sessions:
        session["_id"] = str(session["_id"])
    return {"sessions": sessions}

# Household comparison endpoint
@app.get("/api/comparison/household")
async def get_household_comparison():
    # Get user's current month data
    current_month = datetime.now().strftime("%Y-%m")
    
    user_income = sum(doc["amount"] for doc in transactions_collection.find({
        "type": "income",
        "date": {"$regex": f"^{current_month}"}
    }))
    user_expenses = sum(doc["amount"] for doc in transactions_collection.find({
        "type": "expense", 
        "date": {"$regex": f"^{current_month}"}
    }))
    
    # Simulated household comparison data (in real app, this would come from aggregated data)
    household_data = {
        "user_data": {
            "income": user_income,
            "expenses": user_expenses,
            "savings_rate": ((user_income - user_expenses) / user_income * 100) if user_income > 0 else 0
        },
        "average_household": {
            "income": 15000,
            "expenses": 12000,
            "savings_rate": 20
        },
        "category_comparison": {
            "מזון": {"user": 0, "average": 2500},
            "דיור": {"user": 0, "average": 4500},
            "תחבורה": {"user": 0, "average": 1800},
            "בילויים": {"user": 0, "average": 1200},
            "בריאות": {"user": 0, "average": 800}
        }
    }
    
    # Calculate user's category expenses
    for category in household_data["category_comparison"]:
        user_category_expense = sum(doc["amount"] for doc in transactions_collection.find({
            "type": "expense",
            "category": category,
            "date": {"$regex": f"^{current_month}"}
        }))
        household_data["category_comparison"][category]["user"] = user_category_expense
    
    return household_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
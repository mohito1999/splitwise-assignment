from fastapi import FastAPI, Depends, Request, Form, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
import json
from . import models, database
from .database import get_db
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import joinedload

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Pydantic model for User input
class UserCreate(BaseModel):
    name: str
    email: str

# Pydantic models for request validation
class GroupCreate(BaseModel):
    name: str
    users: List[UserCreate]

# Add new Pydantic model for percentage splits (add this near other BaseModel classes)
class PercentSplit(BaseModel):
    user_id: int
    percentage: float

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    # Get groups with their members and balances
    groups = db.query(models.Group).all()
    
    # Create a dictionary to store balances for each group
    group_balances = {}
    
    for group in groups:
        balances = db.query(models.Balance).filter(
            models.Balance.group_id == group.id
        ).all()
        
        # Get all users in the group
        group_users = db.query(models.User).join(models.GroupMembership).filter(
            models.GroupMembership.group_id == group.id
        ).all()
        
        # Create a balance summary for each user
        user_balances = {}
        for user in group_users:
            # Money user owes to others
            owes = db.query(models.Balance).filter(
                models.Balance.group_id == group.id,
                models.Balance.user_id == user.id
            ).all()
            
            # Money others owe to user
            owed = db.query(models.Balance).filter(
                models.Balance.group_id == group.id,
                models.Balance.owe_to == user.id
            ).all()
            
            total_owes = sum(balance.amount for balance in owes)
            total_owed = sum(balance.amount for balance in owed)
            net_balance = total_owed - total_owes
            
            user_balances[user.id] = {
                "user": user,
                "net_balance": net_balance,
                "owes_details": [(db.query(models.User).get(b.owe_to), b.amount) for b in owes],
                "owed_by_details": [(db.query(models.User).get(b.user_id), b.amount) for b in owed]
            }
            
        group_balances[group.id] = user_balances

    return templates.TemplateResponse("index.html", {
        "request": request,
        "groups": groups,
        "group_balances": group_balances
    })

@app.get("/create-group")
def create_group_form(request: Request):
    return templates.TemplateResponse("create_group.html", {"request": request})

@app.post("/create-group")
async def create_group_submit(
    request: Request,
    group_name: str = Form(...),
    user_names: list = Form(...),
    user_emails: list = Form(...),
    db: Session = Depends(get_db)
):
    # Create group
    new_group = models.Group(name=group_name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # Create users and add to group
    for name, email in zip(user_names, user_emails):
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if not existing_user:
            user = models.User(name=name, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user = existing_user
            
        membership = models.GroupMembership(group_id=new_group.id, user_id=user.id)
        db.add(membership)
    
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/add-expense")
def add_expense_form(request: Request, db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    return templates.TemplateResponse("add_expense.html", {
        "request": request,
        "groups": groups,
    })

@app.post("/add-expense")
async def add_expense_submit(
    request: Request,
    group_id: int = Form(...),
    added_by: int = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    split_type: str = Form(...),
    percentages: List[float] = Form(None),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).join(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id
    ).all()

    if split_type == "equal":
        split_amount = amount / len(users)
        
        for user in users:
            if user.id != added_by:
                balance = models.Balance(
                    group_id=group_id,
                    user_id=user.id,
                    owe_to=added_by,
                    amount=split_amount
                )
                db.add(balance)
    
    elif split_type == "percent":
        if not percentages:
            raise HTTPException(status_code=400, detail="Percentages required for percent split")
            
        # Convert percentages to float if they're not None
        percentages = [float(p) if p else 0 for p in percentages]
        
        # Validate total is approximately 100%
        total_percentage = sum(percentages)
        if abs(total_percentage - 100.0) > 0.01:  # Allow small floating-point difference
            raise HTTPException(status_code=400, detail=f"Percentages must sum to 100% (got {total_percentage}%)")
        
        for user, percentage in zip(users, percentages):
            if user.id != added_by and percentage > 0:
                split_amount = (percentage / 100.0) * amount
                balance = models.Balance(
                    group_id=group_id,
                    user_id=user.id,
                    owe_to=added_by,
                    amount=split_amount
                )
                db.add(balance)
    
    # Create expense record
    new_expense = models.Expense(
        group_id=group_id,
        added_by=added_by,
        amount=amount,
        description=description,
        split_type=split_type
    )
    db.add(new_expense)
    db.commit()
    
    return RedirectResponse(url=f"/group/{group_id}/ledger", status_code=303)

@app.post("/delete-group/{group_id}")
def delete_group_submit(group_id: int, db: Session = Depends(get_db)):
    # Use your existing delete_group logic
    db.query(models.GroupMembership).filter(models.GroupMembership.group_id == group_id).delete()
    db.query(models.Balance).filter(models.Balance.group_id == group_id).delete()
    db.query(models.Expense).filter(models.Expense.group_id == group_id).delete()
    db.query(models.Group).filter(models.Group.id == group_id).delete()
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/manage-group-users/{group_id}")
def manage_group_users(request: Request, group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return RedirectResponse(url="/", status_code=303)
    
    group_members = db.query(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id
    ).join(models.User).all()
    
    return templates.TemplateResponse("manage_group_users.html", {
        "request": request,
        "group": group,
        "group_members": group_members
    })

@app.post("/add-user-to-group/{group_id}")
async def add_user_to_group(
    group_id: int,
    user_name: str = Form(...),
    user_email: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        # Create new user if they don't exist
        user = models.User(name=user_name, email=user_email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if user is already in the group
    existing_membership = db.query(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id,
        models.GroupMembership.user_id == user.id
    ).first()
    
    if not existing_membership:
        # Add user to group
        membership = models.GroupMembership(group_id=group_id, user_id=user.id)
        db.add(membership)
        db.commit()
    
    return RedirectResponse(url=f"/manage-group-users/{group_id}", status_code=303)

@app.post("/remove-user-from-group/{group_id}/{user_id}")
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    # Delete any balances involving this user in this group
    db.query(models.Balance).filter(
        models.Balance.group_id == group_id,
        (models.Balance.user_id == user_id) | (models.Balance.owe_to == user_id)
    ).delete()
    
    # Remove user from group
    db.query(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id,
        models.GroupMembership.user_id == user_id
    ).delete()
    
    db.commit()
    return RedirectResponse(url=f"/manage-group-users/{group_id}", status_code=303)

@app.get("/api/group-users/{group_id}")
async def get_group_users(group_id: int, db: Session = Depends(get_db)):
    users = db.query(models.User).join(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id
    ).all()
    
    return [{"id": user.id, "name": user.name} for user in users]

@app.get("/group/{group_id}/ledger")
def group_ledger(request: Request, group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get all expenses for this group, including the user who added the expense
    expenses = db.query(models.Expense)\
        .filter(models.Expense.group_id == group_id)\
        .options(joinedload(models.Expense.user))\
        .order_by(models.Expense.created_at.desc())\
        .all()
    
    # Get all balances
    balances = db.query(models.Balance).filter(
        models.Balance.group_id == group_id
    ).all()
    
    # Get all users in the group
    group_users = db.query(models.User).join(models.GroupMembership).filter(
        models.GroupMembership.group_id == group_id
    ).all()
    
    # Calculate user balances
    user_balances = {}
    for user in group_users:
        # Money user owes to others
        owes = db.query(models.Balance).filter(
            models.Balance.group_id == group_id,
            models.Balance.user_id == user.id
        ).all()
        
        # Money others owe to user
        owed = db.query(models.Balance).filter(
            models.Balance.group_id == group_id,
            models.Balance.owe_to == user.id
        ).all()
        
        total_owes = sum(balance.amount for balance in owes)
        total_owed = sum(balance.amount for balance in owed)
        net_balance = total_owed - total_owes
        
        user_balances[user.id] = {
            "user": user,
            "net_balance": net_balance
        }
    
    return templates.TemplateResponse("group_ledger.html", {
        "request": request,
        "group": group,
        "expenses": expenses,
        "balances": user_balances
    })
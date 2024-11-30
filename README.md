# Expense Splitter

A simple web application for splitting expenses among groups of people. Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

---

## Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/mohito1999/splitwise-assignment.git
   cd splitwise-assignment
2. Build and start the application:
    ```bash
    docker-compose up --build
3. Access the application:
    URL: http://localhost:8000

## API Endpoints

### Groups

- `GET /` - Home page with list of groups
- `POST /create-group` - Create a new group with body:

```json
{
  "group_name": "string",
  "users": [
    {
      "name": "string",
      "email": "string"
    }
  ]
}
```

- `POST /delete-group/{group_id}` - Delete a group
- `GET /manage-group-users/{group_id}` - View users in a group

### Users

- `POST /add-user-to-group/{group_id}` - Add a user to group with body:

```json
{
    "user_name":"string",
    "user_email":"string"
}
```

- `POST /remove-user-from-group/{group_id}/{user_id}` - Remove a user from group

### Expenses

- `POST /add-expense` - Create a new expense with body:

```json

{
    "group_id": "integer",
    "added_by": "integer",
    "amount": "float",
    "split_type": "string (equal/percent)",
    "percentages": ["float"] // Optional, required for percent split
}
```

## Database Schema

### Tables
- `groups` (id, name)
- `users` (id, name, email)
- `group_memberships` (id, group_id, user_id)
- `expenses` (id, group_id, added_by, amount, split_type)
- `balances` (id, group_id, user_id, owe_to, amount)

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

text
expense-splitter/
├── app/
│ ├── main.py
│ ├── models.py
│ ├── database.py
│ ├── templates/
│ └── static/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
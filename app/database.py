from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

# Ensure the URL starts with postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_expense_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Add description column if it doesn't exist
        conn.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='expenses' AND column_name='description') THEN
                ALTER TABLE expenses ADD COLUMN description VARCHAR;
                UPDATE expenses SET description = 'Expense' WHERE description IS NULL;
            END IF;
        END $$;
        """)
        
        # Add created_at column if it doesn't exist
        conn.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='expenses' AND column_name='created_at') THEN
                ALTER TABLE expenses ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                UPDATE expenses SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
            END IF;
        END $$;
        """)
        conn.commit()

# Add this to your create_tables function
def create_tables():
    Base.metadata.create_all(bind=engine)
    add_expense_columns()  # Add this line
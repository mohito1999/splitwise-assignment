from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
import os
import sys

# Get the directory containing env.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of migrations)
project_root = os.path.dirname(current_dir)
# Add project root to Python path
sys.path.append(project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, '.env'))

# Import your models
from app.models import Base

# Get database URL with debug output
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Current working directory: {os.getcwd()}")
print(f"Loading DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Ensure the URL starts with postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# this is the Alembic Config object
config = context.config

# Set SQLAlchemy URL in Alembic config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to your models' metadata
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

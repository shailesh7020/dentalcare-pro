import os

os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/dentalcare",
        "SECRET_KEY": "test-secret-key-that-is-longer-than-thirty-two-characters",
        "JWT_SECRET": "test-jwt-secret-that-is-longer-than-thirty-two-characters",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_DAYS": "14",
        "REDIS_URL": "redis://localhost:6379/15",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001",
    }
)

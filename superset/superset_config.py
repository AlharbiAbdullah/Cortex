# Superset configuration for Cortex BI
import os

# Security settings for iframe embedding
# Allow embedding in iframes from any origin
HTTP_HEADERS = {
    'X-Frame-Options': 'ALLOWALL',
}

# Disable X-Frame-Options header (allows iframe embedding)
X_FRAME_OPTIONS = ''

# Enable CORS
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:3000', 'http://127.0.0.1:3000', '*'],
}

# Feature flags
FEATURE_FLAGS = {
    'EMBEDDED_SUPERSET': True,
    'ENABLE_TEMPLATE_PROCESSING': True,
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
}

# Allow public (guest) access for embedding
PUBLIC_ROLE_LIKE = 'Gamma'
GUEST_ROLE_NAME = 'Public'
GUEST_TOKEN_JWT_SECRET = os.environ.get('SUPERSET_SECRET_KEY', 'cortex-superset-secret-key-change-in-production')

# Database connection
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SUPERSET_DATABASE_URI',
    'postgresql://superset:superset@superset-db:5432/superset'
)

# Redis for caching and celery
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 1,
}

# Secret key for session management
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'cortex-superset-secret-key-change-in-production')

# Webserver settings
WEBSERVER_TIMEOUT = 300
SUPERSET_WEBSERVER_TIMEOUT = 300

# Enable CSRF but allow for embedding
WTF_CSRF_ENABLED = False  # Disable CSRF for embedding (re-enable in production with proper config)

# Talisman security (disabled for iframe embedding)
TALISMAN_ENABLED = False

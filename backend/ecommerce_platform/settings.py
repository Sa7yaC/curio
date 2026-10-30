import os
from pathlib import Path
from datetime import timedelta
import logging

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# 1. DEBUG CONFIGURATION (Practice 1: Never leave DEBUG=True in Production)
# ==============================================================================
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# ==============================================================================
# 2. SECRET KEY MANAGEMENT (Practice 1 & 6: Never hardcode secrets in repository)
# ==============================================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        # Development fallback only
        SECRET_KEY = 'django-insecure-dev-only-local-secret-key-replace-in-production'
        logging.warning("SECURITY WARNING: Using insecure development SECRET_KEY. Configure DJANGO_SECRET_KEY in production.")
    else:
        raise ValueError("DJANGO_SECRET_KEY environment variable must be set when DEBUG=False!")

# ==============================================================================
# 3. ALLOWED HOSTS (Practice 1: Prevent HTTP Host Header poisoning)
# ==============================================================================
allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS')
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']

# Auto-detect Render external hostname if provided by Render environment
render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_host and render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_host)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'store',
]

AUTH_USER_MODEL = 'store.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'store.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'ecommerce_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database Configuration
# Supports PostgreSQL via DB_* environment variables or DATABASE_URL, with SQLite fallback
DB_NAME = os.environ.get('DB_NAME')
DATABASE_URL = os.environ.get('DATABASE_URL')

if DB_NAME or os.environ.get('DB_ENGINE') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': DB_NAME or 'ecommerce_db',
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 60)),
        }
    }
elif DATABASE_URL:
    import urllib.parse as urlparse
    url = urlparse.urlparse(DATABASE_URL)
    query_params = urlparse.parse_qs(url.query)
    
    # Handle SSL mode (Supabase requires SSL)
    db_options = {}
    if 'sslmode' in query_params:
        db_options['sslmode'] = query_params['sslmode'][0]
    elif url.hostname and 'supabase' in url.hostname:
        db_options['sslmode'] = 'require'

    is_supabase = bool(url.hostname and 'supabase' in url.hostname)
    default_conn_max_age = 0 if is_supabase else 60

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': urlparse.unquote(url.username) if url.username else '',
            'PASSWORD': urlparse.unquote(url.password) if url.password else '',
            'HOST': url.hostname,
            'PORT': url.port or 5432,
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', default_conn_max_age)),
            'OPTIONS': db_options,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 30,
            }
        }
    }

# ==============================================================================
# 4. PASSWORD POLICIES & HASHERS
# ==============================================================================
# Optional Fast Password Hasher (Useful for high-concurrency load testing to prevent CPU bottlenecks)
FAST_HASHING = os.environ.get('FAST_HASHING', 'False').lower() in ('true', '1', 'yes')
if FAST_HASHING:
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# 5. REST FRAMEWORK & JWT SETTINGS
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ==============================================================================
# 6. CORS CONFIGURATION (Prevent cross-origin request hijacking)
# ==============================================================================
cors_origins_env = os.environ.get('CORS_ALLOWED_ORIGINS')
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = [
        o.strip().rstrip('/') for o in cors_origins_env.split(',') if o.strip()
    ]
    CORS_ALLOW_ALL_ORIGINS = False
elif DEBUG:
    # Safe local dev defaults
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
    CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'True').lower() == 'true'
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = []

# ==============================================================================
# 7. SECURE COOKIE & SESSION SETTINGS (Practice 2 & 3: Protect session and CSRF)
# ==============================================================================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 1 day

# In production, cookies are transmitted strictly over HTTPS
SESSION_COOKIE_SECURE = os.environ.get(
    'DJANGO_SESSION_COOKIE_SECURE',
    str(not DEBUG)
).lower() in ('true', '1', 'yes')

CSRF_COOKIE_SECURE = os.environ.get(
    'DJANGO_CSRF_COOKIE_SECURE',
    str(not DEBUG)
).lower() in ('true', '1', 'yes')

# ==============================================================================
# 8. HTTPS EVERYWHERE & SSL REDIRECTION (Practice 8)
# ==============================================================================
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')

if SECURE_SSL_REDIRECT:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS policy
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==============================================================================
# 9. CONTENT SECURITY & BROWSER HEADERS (Practice 9: XSS, Clickjacking, MIME)
# ==============================================================================
X_FRAME_OPTIONS = 'DENY'  # Mitigate clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS filter
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ==============================================================================
# 10. STRUCTURED SECURITY LOGGING & MONITORING (Practice 10)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'store': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

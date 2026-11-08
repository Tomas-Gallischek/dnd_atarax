import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

raw_secret = os.getenv('SECRET_KEY')
SECRET_KEY = raw_secret.strip() if (raw_secret and raw_secret.strip()) else 'django-insecure-(p^uw3gjeu=s)h3e#x=(6n_(=%pzb)9kkmb$_+a1=g3*dk*6)8'

debug_env = (os.getenv('DEBUG') or 'False').strip().lower()
DEBUG = debug_env in ('true', '1', 't')

default_hosts = ['draciadementi.cz', 'www.draciadementi.cz', '192.168.0.95', 'localhost', '127.0.0.1', 'web', 'dnd_django']
env_hosts = [h.strip() for h in (os.getenv('ALLOWED_HOSTS') or '').split(',') if h.strip()]
ALLOWED_HOSTS = list(dict.fromkeys(default_hosts + env_hosts))

CSRF_TRUSTED_ORIGINS = [
    'https://draciadementi.cz',
    'https://www.draciadementi.cz',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'player_site_app',
    'dm_site_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dnd_atarax.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dnd_atarax.wsgi.application'

DB_ENGINE = (os.getenv('DB_ENGINE') or 'postgresql').strip().lower()

if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    raw_host = (os.getenv('DB_HOST') or 'localhost').strip()
    if raw_host == 'db':
        import socket
        try:
            socket.gethostbyname('db')
            db_host = 'db'
        except (socket.gaierror, OSError):
            db_host = '192.168.0.95'
    else:
        db_host = raw_host or 'localhost'

    db_name = (os.getenv('DB_NAME') or 'dnd_atarax_db').strip() or 'dnd_atarax_db'
    db_user = (os.getenv('DB_USER') or 'postgres').strip() or 'postgres'
    db_password = (os.getenv('DB_PASSWORD') or 'postgres').strip() or 'postgres'
    db_port = (os.getenv('DB_PORT') or '5432').strip() or '5432'

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': db_port,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# Zde máš pravděpodobně své zdrojové styly a obrázky
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Sem je Django zkopíruje po spuštění collectstatic (nesmí se jmenovat stejně jako složka výše)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Nastavení pro nahrané obrázky (z předchozí konfigurace už bys měl mít)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}

LOGIN_URL = 'player_site_app:index'
LOGIN_REDIRECT_URL = 'player_site_app:prehled_postav'
LOGOUT_REDIRECT_URL = 'player_site_app:index'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


# Movie Recommendation Backend API

A high-performance Django REST API for movie discovery and recommendations featuring JWT authentication, Redis caching, and comprehensive API documentation.

## 🎬 Features

- **Movie Discovery**: Browse trending, recommended, and search movies
- **User Management**: JWT authentication with user profiles
- **Favorites System**: Save and manage personal movie collections
- **Performance**: Redis caching for optimal response times
- **Documentation**: Interactive Swagger/OpenAPI documentation

## 🛠 Tech Stack

**Backend Framework**: Django 5.2.8 + Django REST Framework  
**Database**: PostgreSQL  
**Caching**: Redis  
**Authentication**: JWT Tokens  
**Documentation**: Swagger/OpenAPI 3.0  
**API Integration**: TMDb API

## 🚀 Quick Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Redis server
- TMDb API account

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd movie_recommendation
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
   Create a `.env` file in the project root:

```
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_NAME=movie_recommendation_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
TMDB_API_KEY=your_tmdb_api_key
TMDB_BASE_URL=https://api.themoviedb.org/3
```

5. **Setup PostgreSQL database**

```bash
psql -U postgres
CREATE DATABASE movie_recommendation_db;
\q
```

6. **Start Redis server**

```bash
redis-server
```

7. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

8. **Create superuser (optional)**

```bash
python manage.py createsuperuser
```

9. **Run development server**

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Authentication

| Method | Endpoint                   | Description          |
| ------ | -------------------------- | -------------------- |
| `POST` | `/api/users/register/`     | User registration    |
| `POST` | `/api/users/login/`        | JWT token obtain     |
| `POST` | `/api/users/token/refresh` | Refresh token access |

### Movies

| Method | Endpoint                            | Description                 |
| ------ | ----------------------------------- | --------------------------- |
| `GET`  | `/api/movies/trending/`             | Trending movies (cached)    |
| `GET`  | `/api/movies/search/?query=string`  | Search movies               |
| `GET`  | `/api/movies/details/{id}/`         | Movie details (cached)      |
| `GET`  | `/api/movies/recommendations/{id}/` | Recommended movies (cached) |

### User Features

| Method   | Endpoint                             | Description     |
| -------- | ------------------------------------ | --------------- |
| `GET`    | `/api/users/profile/`                | User profile    |
| `GET`    | `/api/movies/favorites/`             | User favorites  |
| `POST`   | `/api/movies/favorites/add/`         | Add favorites   |
| `DELETE` | `/api/movies/favorites/remove/{id}/` | Remove favorite |

### Admin/Monitoring

| Method | Endpoint                   | Description                         |
| ------ | -------------------------- | ----------------------------------- |
| `GET`  | `/api/movies/cache-stats/` | Redis cache statistics (admin only) |

### Documentation

- `GET /api/docs/` - Interactive Swagger UI
- `GET /api/redoc/` - ReDoc documentation

## ⚡ Caching Strategy

| Data Type             | Cache Duration | Purpose              |
| --------------------- | -------------- | -------------------- |
| Trending Movies       | 1 Hour         | High-frequency data  |
| Movie Recommendations | 2 Hours        | Personalized content |
| Movie Details         | 24 Hours       | Static movie data    |

**Cache Monitoring:** Access real-time cache statistics via `/api/movies/cache-stats/` endpoint.

## 📝 Logging

The application includes comprehensive logging for:

### Log Files (in `logs/` directory)

- **app.log**: General application logs
- **cache.log**: Cache hits/misses and Redis operations
- **api.log**: API requests and responses
- **celery.log**: Celery task logs

### Log Levels

- **INFO:** Normal operations, cache hits/misses
- **WARNING:** Non-critical issues
- **ERROR:** Error conditions

### Sample Log Output

```
[INFO] 2025-11-12 10:30:45 - ✓ CACHE HIT: trending_movies_1 | Retrieved from Redis cache
[INFO] 2025-11-12 10:31:12 - ✗ CACHE MISS: movie_details_550 | Fetching from TMDb API
[INFO] 2025-11-12 10:31:13 - ✓ CACHE SET: movie_details_550 | Stored in Redis with TTL=86400s
```

### Monitoring Cache Performance

Access cache statistics (admin only):

```bash
GET /api/movies/cache-stats/
```

Response:

```json
{
  "total_commands": 1250,
  "keyspace_hits": 892,
  "keyspace_misses": 358,
  "hit_rate": 71.36
}
```

## 🔗 Git Commit Workflow

```bash
# Initial Setup
git commit -m "feat: set up Django project with PostgreSQL"
git commit -m "feat: integrate TMDb API for movie data"

# Feature Development
git commit -m "feat: implement movie recommendation API"
git commit -m "feat: add user authentication and favorite movie storage"

# Optimization
git commit -m "perf: add Redis caching for movie data"

# Documentation
git commit -m "feat: integrate Swagger for API documentation"
git commit -m "docs: update README with API details"
```

## 🧪 Testing

Run tests with:

```bash
python manage.py test # Run all tests
python manage.py test movies.tests # Run only movies test
python manage.py test users.tests # Run only users test
python manage.py test movies.test_celery # Run celery test script
```

### Sample Output (`test_celery.py`)

```
Found 3 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
[INFO] 2025-11-21 16:46:13,886 - Fetch details for movie 550
[INFO] 2025-11-21 16:46:13,891 - Successfully cached details for movie 550
.[INFO] 2025-11-21 16:46:14,119 - Starting Trending Movies cache refresh
[INFO] 2025-11-21 16:46:14,119 - Refreshing cache for trending_movies_1
[INFO] 2025-11-21 16:46:14,120 - Successfully refreshed trending_movies_1
[INFO] 2025-11-21 16:46:14,120 - Refreshing cache for trending_movies_2
[INFO] 2025-11-21 16:46:14,120 - Successfully refreshed trending_movies_2
[INFO] 2025-11-21 16:46:14,120 - Refreshing cache for trending_movies_3
[INFO] 2025-11-21 16:46:14,120 - Successfully refreshed trending_movies_3
[INFO] 2025-11-21 16:46:14,120 - Trending Movies cache refresh completed
.[INFO] 2025-11-21 16:46:14,345 - Sent favorite movie notification to test@example.com
.
----------------------------------------------------------------------
Ran 3 tests in 0.680s

OK
```

---

## 🐰 RabbitMQ + Celery Setup Guide

RabbitMQ is a robust message broker that provides:

- **Reliable message delivery**
- **Message persistence**
- **Flexible routing**
- **Multiple queue support**
- **Priority queues**
- **Dead letter exchanges**

### 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│   Django    │─────▶│   RabbitMQ   │─────▶│ Celery Workers │
│ Application │      │   (Broker)   │      │   (Multiple)   │
└─────────────┘      └──────────────┘      └────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Redis     │
                     │  (Results)   │
                     └──────────────┘
```

### 📊 Queue Structure

| Queue       | Priority        | Purpose            | Tasks                                                   |
| ----------- | --------------- | ------------------ | ------------------------------------------------------- |
| **emails**  | 10 (highest)    | User notifications | send_favorite_notification, send_weekly_recommendations |
| **cache**   | 7 (high)        | Cache management   | refresh_trending_cache, cleanup_old_cache               |
| **api**     | 6 (medium-high) | External API calls | fetch_movie_details_async, bulk_cache_popular_movies    |
| **default** | 5 (medium)      | General tasks      | Fallback queue                                          |
| **reports** | 4 (low-medium)  | Analytics          | generate_analytics_report                               |

#### 1. Install RabbitMQ

**macOS:**

```bash
brew install rabbitmq
brew services start rabbitmq
sudo rabbitmq-plugins enable rabbitmq_management
```

**Ubuntu:**

```bash
sudo apt-get update
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

#### 2. Configure RabbitMQ

```bash
# Create admin user
sudo rabbitmqctl add_user admin admin123
sudo rabbitmqctl set_user_tags admin administrator
sudo rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

# Verify installation
sudo rabbitmqctl status
```

#### 3. Start Services

**Terminal 1: Django**

```bash
python manage.py runserver
```

**Terminal 2: Celery Worker**

```bash
celery -A movie_recommendation worker \
  --loglevel=info \
  --concurrency=4 \
  -Q default,emails,cache,api,reports
```

**Terminal 3: Celery Beat**

```bash
celery -A movie_recommendation beat \
  --loglevel=info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Terminal 4: Flower (Optional)**

```bash
celery -A movie_recommendation flower --port=5555
```

---

## Code Quality Check - GitHub Actions

### What This Does

Automatically checks your code quality on every push:

✅ **Black** - Code formatting  
✅ **isort** - Import sorting  
✅ **Flake8** - Code linting (syntax errors, style issues)

**Time:** ~30 seconds

### Setup

#### Step 1: Create the workflow

Create `.github/workflows/code-quality.yml` with the content above.

#### Step 2: Add config files

Create `.flake8` and `pyproject.toml` in your project root.

#### Step 3: Push to GitHub

```bash
git add .github/ .flake8 pyproject.toml
git commit -m "ci: add code quality checks"
git push
```

### What Happens

Every push triggers code quality checks:

```
Your Push
    ↓
[Black] Formatting check
    ↓
[isort] Import sorting check
    ↓
[Flake8] Linting check
    ↓
✅ Pass or ⚠️ Issues found
```

### Fix Issues Locally

If the checks fail, fix them before pushing:

```bash
# Install tools
pip install black isort flake8

# Auto-fix formatting
black .

# Auto-fix imports
isort .

# Check for issues
flake8 .

# Commit and push again
git add .
git commit -m "style: fix code formatting"
git push
```

### View Results

Go to your repo → **Actions** tab → See the checks

---

## Deployment

1. Set `DEBUG=False` in production
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for sensitive data (Render Environment)
4. Setup PostgreSQL and Redis on production server
5. Collect static files: `python manage.py collectstatic` (defined in `render-build.sh`)
6. Use a production WSGI server (gunicorn, uwsgi)

## ⚙️ Performance Considerations

- All external API calls are cached with Redis
- Database queries use Django ORM with select_related/prefetch_related
- JWT tokens reduce database lookups for authentication
- Pagination implemented for large datasets

## 🔐 Security Features

- JWT-based authentication
- Password hashing with Django's built-in system
- CORS configuration
- Environment variables for sensitive data
- Input validation with DRF serializers

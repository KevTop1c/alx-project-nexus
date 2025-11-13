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
python manage.py test
```

## Deployment

1. Set `DEBUG=False` in production
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Setup PostgreSQL and Redis on production server
5. Collect static files: `python manage.py collectstatic`
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

# Amikiyo Backend — Social Platform API

Full-stack backend powering a **social media platform for anime communities**, designed to support scalable REST APIs, relational database architecture, containerized deployment, and real-time integrations.

The backend system is built using **Python and Django** with **Django REST Framework**, providing secure APIs consumed by a Flutter mobile application.

The platform enables users to interact socially through posts, comments, messaging, groups, and temporary stories while maintaining a modular backend architecture designed for scalability.

---

# System Architecture

```
Flutter Mobile Application
            │
            │  REST API Requests
            ▼
Django REST Backend (Containerized with Docker)
            │
            ├── Authentication & User Management
            ├── Social Graph (Follow System)
            ├── Content System (Posts & Comments)
            ├── Messaging System
            ├── Groups & Communities
            └── Stories System
```

The backend is fully containerized using Docker to provide **consistent development environments, reproducible builds, and easier deployment**.

---

# Technology Stack

### Backend Framework

* Python
* Django
* Django REST Framework

### Authentication

* JWT Authentication (SimpleJWT)

### Infrastructure & Deployment

* Docker Containerization
* Gunicorn WSGI Server
* Relational Database Support

### Cloud & Integrations

* Firebase Admin SDK
* Google Cloud Storage / Firestore

### Other Tools

* Pillow (image handling)
* Python Decouple (environment management)

---

# Database Architecture

The backend uses **Django ORM** for database abstraction and schema management, allowing the system to operate with multiple relational database engines without changing application logic.

### Supported Databases

The architecture is compatible with:

* PostgreSQL for production deployments
* MySQL for scalable relational database environments
* SQLite for lightweight development environments

During development the project runs on **SQLite**, while the schema and migrations are designed to support migration to **PostgreSQL or MySQL** in production environments.

### Database Design

The platform implements a **relational data model** with structured relationships between multiple entities.

Core database entities include:

* Users
* Profiles
* Posts
* Comments
* Followers
* Groups
* Group Memberships
* Stories
* Story Viewers
* Chat Rooms

Relationships are implemented using Django ORM constructs such as:

* Foreign Keys
* Many-to-Many relationships
* Database migrations
* Indexed fields for efficient querying

### Data Integrity & Query Handling

The backend ensures reliable data management through:

* ORM based query abstraction
* Schema migrations for version-controlled database updates
* Relational constraints for data consistency
* Optimized query handling for feed generation and social interactions

This architecture allows the platform to scale while keeping the database layer maintainable and modular.

---

# Core Backend Modules

## User Management

* User registration and authentication
* Profile creation and updates
* Public profile viewing
* Search users
* Follow / unfollow system
* Followers and following lists

---

## Posts System

* Create media posts
* Delete posts
* Retrieve posts by user
* Post detail endpoint
* Like / unlike posts
* Post view tracking

---

## Comments System

* Add comments to posts
* Retrieve post comments
* Delete comments

---

## Personalized Feed

* Dynamic home feed generation
* Content based on user activity and follow relationships

---

## Messaging System

* Chat room creation
* Retrieve existing conversations
* List user chat rooms
* Backend support for real-time messaging integration

---

## Groups & Communities

* Create community groups
* Send join requests
* Approve / reject requests
* Add or remove members
* Leave groups
* Transfer group ownership
* Update group information
* Search public groups

---

## Stories System

* Create temporary stories
* View story feed
* Track story viewers
* View user's stories
* Delete stories

---

# Example API Endpoints

```
/users/
/profiles/<id>/
/profiles/search/

/posts/
/posts/<post_id>/like/
/posts/<post_id>/comments/

/home-feed/

/chat/get-or-create/
/chat/my/

/groups/create/
/groups/<group_id>/

/story/create/
/story/feed/
```

These endpoints provide the primary API layer consumed by the Flutter mobile client.

---

# Running the Project Locally

### 1. Clone the Repository

```
git clone https://github.com/xARCELLx/Amikiyo_backend.git
cd Amikiyo_backend
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Run the Development Server

```
python manage.py runserver
```

Server will start at:

```
http://127.0.0.1:8000
```

---

# Running with Docker

The backend is containerized using Docker to provide a consistent runtime environment.

### Build the container

```
docker build -t amikiyo-backend .
```

### Run the container

```
docker run -p 8000:8000 amikiyo-backend
```

### Using Docker Compose

```
docker compose up --build
```

This launches the backend service inside a container.

---

# Repository Structure

```
Amikiyo_backend
│
├── api/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│
├── amikiyo_backend/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md
```

---

# Future Improvements

Planned enhancements for the backend system include:

* AI powered content recommendation
* Automated content moderation
* Real-time notifications
* Advanced analytics and engagement tracking

---

# Author

**Ayush Rawat**

Full Stack Developer specializing in:

* Flutter Mobile Development
* Django Backend Systems
* REST API Architecture
* Containerized Backend Deployment

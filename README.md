# Amikiyo Backend — Social Platform API

A scalable backend system built using **Python and Django** with **Django REST Framework** to power a modern mobile social media platform.

This backend provides secure REST APIs used by a **Flutter mobile client** and supports user interactions such as posting, messaging, groups, and story sharing.

The project demonstrates backend system design including authentication, social graph management, media handling, and modular API architecture.

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

The backend is fully containerized using Docker for reproducible environments and easier deployment.

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

### Cloud & Integrations

* Firebase Admin SDK
* Google Cloud Storage / Firestore

### Other Tools

* Pillow (image handling)
* Python Decouple (environment management)

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

The backend is containerized using Docker for consistent development and deployment environments.

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

This starts the backend service inside a container.

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
* Real time notifications
* Advanced analytics and engagement tracking

---

# Author

**Ayush Rawat**

Full Stack Developer specializing in:

* Flutter Mobile Development
* Django Backend Systems
* REST API Architecture
* Containerized Backend Deployment

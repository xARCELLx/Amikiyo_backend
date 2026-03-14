# Anime Social Platform Backend API

Backend system built with **Python and Django** using **Django REST Framework** to power a mobile social media application.

The backend provides REST APIs for user management, posts, social interactions, messaging, groups, and story features used by a Flutter mobile client.

---

## Tech Stack

* Python
* Django
* Django REST Framework
* REST API Architecture
* JWT Authentication
* Media Storage
* Real-time Messaging Integration
* Cloud-ready backend architecture

---

## Core Features

### User Management

* User registration
* Profile creation and management
* Public profile viewing
* Search users
* Follow / unfollow users
* Followers and following lists

### Posts System

* Create posts
* Delete posts
* Fetch posts by user
* Post detail view
* Like / unlike posts
* Record post views

### Comments System

* Add comments on posts
* Fetch comments
* Delete comments

### Home Feed

* Personalized home feed based on user activity and follows.

### Chat System

* Create or retrieve chat rooms
* List user chat rooms
* Messaging backend support

### Groups System

* Create groups
* Join group requests
* Approve / reject join requests
* Add members
* Remove members
* Leave group
* Transfer group admin
* Update group details
* Search groups

### Stories System

* Create stories
* View story feed
* View individual story
* Delete story
* Track story viewers
* View user's own stories

---

## API Architecture

The backend exposes RESTful endpoints for integration with mobile clients.

Example endpoints:

```
/users/
/posts/
/home-feed/
/profiles/search/
/chat/get-or-create/
/groups/create/
/story/create/
```

---

## Project Purpose

This backend powers a **mobile social media platform for anime communities** where users can:

* Share posts and media
* Follow other users
* Chat with friends
* Create groups
* Share temporary stories

---

## Repository Structure

```
api/
views.py
models.py
serializers.py
urls.py
```

---

## Future Improvements

* AI-powered recommendation system
* Content moderation tools
* Advanced analytics
* Real-time notifications

---

## Author

Ayush Rawat
Full Stack Developer (Flutter + Django)

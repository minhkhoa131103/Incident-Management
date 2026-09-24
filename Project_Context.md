# Project Context

## 1. Project Overview

**Project name:** Hệ thống quản lý lỗi và phân loại sự cố

**Goal:**
Build a web application for reporting, managing, classifying, assigning, and tracking software bugs/incidents.

The first target is a complete **Personal MVP** that can run and be demonstrated independently.

After the MVP is completed, the remaining team members will extend the existing codebase with additional features.

---

## 2. Development Strategy

The project has two stages.

### Stage 1 — Personal MVP

One developer builds the MVP end-to-end.

The MVP must be a complete, usable system, not merely a foundation for future development.

Main workflow:

Reporter creates Incident
→ Classification
→ Assignment
→ Agent processes Incident
→ Comments
→ Status updates
→ Resolved
→ Closed

### Stage 2 — Team Extensions

Other team members extend the existing MVP.

Extensions must not break the existing MVP workflow.

---

## 3. MVP Roles

The MVP has three roles:

* Reporter
* Agent
* Admin

### Reporter

* Login / Logout
* Create Incident
* View own Incidents
* Update own Incident when permitted
* View Status
* View Comments
* Add Comments

### Agent

* View assigned Incidents
* View Incident details
* Classify Incidents
* Update Priority
* Update Status
* Add Comments
* Process Incidents

### Admin

* View all Incidents
* Manage Incidents
* Assign Agents
* Manage Users
* Manage Categories
* View Dashboard

The architecture should allow additional roles in the future.

---

## 4. MVP Features

### Authentication

* Login
* Logout
* Password hashing
* Session-based authentication
* Protected routes
* Role-based authorization

### Incident Management

* Create
* Read
* Update
* Delete
* Detail view

### Classification

**Type**

* Bug
* Incident

**Category**

* Authentication
* UI/UX
* Database
* API
* Performance
* Security
* Other

**Priority**

* Low
* Medium
* High
* Critical

**Status**

* Open
* In Progress
* Resolved
* Closed

### Assignment

Each Incident has:

* Reporter
* Assignee

Admin can assign an Agent.

### Comments

Users with appropriate permissions can add comments to Incidents.

### Search / Filter

* Search by Title
* Filter by Status
* Filter by Priority
* Filter by Type
* Filter by Category
* Filter by Assignee

### Dashboard

Basic statistics:

* Total Incidents
* Open
* In Progress
* Resolved
* Closed
* Critical
* High

---

## 5. MVP Database

Initial tables:

* users
* categories
* incidents
* comments

User roles do NOT require a full permission-management system in the MVP.

A simple role-based design is sufficient initially:

User → role → Reporter / Agent / Admin

The code structure should remain extendable for a future Permission / RolePermission system.

---

## 6. Technology Stack

### Backend

* Python
* Flask

### Database

* MySQL

### ORM

* Flask-SQLAlchemy

### Authentication

* Flask-Login

### Validation / Forms

* Flask-WTF

### MySQL Driver

* PyMySQL

### Frontend

* HTML
* CSS
* Jinja2
* Basic JavaScript only when necessary

A separate frontend framework is NOT part of the MVP.

---

## 7. Architecture Direction

Target architecture:

Browser
→ Flask
→ Routes / Services
→ SQLAlchemy
→ MySQL

The project should be modular and readable.

Avoid putting the entire application into a single Flask file.

Business logic should not be unnecessarily coupled to route handlers.

---

## 8. Project Structure Direction

Suggested high-level modules:

* auth
* incidents
* users
* dashboard
* models
* templates
* static

The exact structure may be adjusted during planning if there is a clear technical reason.

---

## 9. Explicitly Out of MVP Scope

The following are NOT required for the Personal MVP:

* REST API
* React/Vue frontend
* OAuth / Google Login
* Email service
* Cloud storage
* Redis
* Message queues
* AI classification
* Advanced reporting
* File attachments
* Audit logs
* Advanced notification system
* Complex permission management

These may be implemented later as extensions.

---

## 10. Extension Roadmap

Possible future extensions:

* Advanced RBAC
* User Management
* Audit Log
* Notifications
* File Attachments
* REST API
* Advanced Dashboard / Reporting
* AI-assisted Classification
* CSV/PDF export

These extensions are secondary to the MVP.

---

## 11. MVP Principles

1. The MVP must work end-to-end.
2. Keep the MVP small enough for one developer.
3. Do not over-engineer.
4. Do not add unnecessary technologies.
5. Keep the codebase easy for other developers to understand and extend.
6. Do not break MVP functionality when adding extensions.
7. Prefer simple, maintainable solutions.
8. Server-side authorization is required.
9. Configuration and secrets must not be hard-coded.
10. The MVP should include enough documentation for another developer to run and understand it.

---

## 12. Documentation Requirements

The finished MVP should have:

* README.md
* .env.example
* Database setup instructions
* Run instructions
* Demo accounts
* Role descriptions
* Feature overview
* Basic project structure documentation

---

## 13. Deadline

**Deadline: 23:59, 25/09/2026**

Priority order:

1. Working MVP
2. Stability and testing
3. Documentation
4. Extensions
5. UI polish / advanced features

# Implementation Plan v2.1

## 1. Project Overview
*   **Project Goal:** Build a web application for reporting, managing, classifying, assigning, and tracking software bugs/incidents.
*   **Intended Users:** Reporters (submitting issues), Agents (resolving issues), and Admins (overseeing the system).
*   **MVP Boundaries:** The Personal MVP focuses solely on core incident lifecycle management, role-based access control, and basic reporting.
*   **Development Objective:** A single developer will build a complete, runnable MVP end-to-end that serves as a clean, modular foundation for future team extensions.
*   **Deadline:** 23:59, 25/09/2026.

## 2. Scope and Non-Scope
**Mandatory MVP Features:**
*   Role-based authentication (Admin, Agent, Reporter).
*   Admin-only user provisioning (no public registration).
*   Incident CRUD operations with strict ownership, conditional editing, and assignment rules.
*   Strict, unidirectional incident status workflow.
*   Commenting system on incidents.
*   Basic search and filtering.
*   Simple dashboard for Agents and Admins.

**Explicitly Excluded Features (Non-Scope):**
*   Public user registration.
*   Password reset/recovery workflows.
*   Email notifications.
*   File attachments.
*   REST API endpoints.
*   Frontend frameworks (React/Vue/Bootstrap/Tailwind).
*   Advanced user management (editing details, deletion, auditing).

**Future Extensions:**
*   Advanced RBAC, Audit Logs, AI Classification, CSV Export.

## 3. Technology Stack
*   **Language:** Python 3.10+
*   **Framework:** Flask
*   **Database:** MySQL
*   **Driver:** PyMySQL
*   **ORM:** Flask-SQLAlchemy
*   **Authentication:** Flask-Login
*   **Forms/Validation:** Flask-WTF
*   **Migration System:** Flask-Migrate / Alembic
*   **Templating:** Jinja2
*   **Frontend Approach:** Vanilla CSS and HTML
*   **Testing Tools:** Pytest and Pytest-Flask

## 4. Architecture
*   **Overall Architecture:** Server-Side Rendered (SSR) Monolithic Application.
*   **Application Factory:** A `create_app()` function will instantiate the Flask app, configure it, and initialize extensions (DB, Login, Migrate) to prevent circular dependencies.
*   **Blueprint Structure:** Routes are grouped by domain (`auth`, `incidents`, `admin`, `dashboard`).
*   **Request Flow:** Browser → Flask Router → Blueprint View → Form Validation → Authorization Check → SQLAlchemy Query → Jinja2 Template → Browser.
*   **Authentication Flow:** User submits credentials → validated against hashed password in DB → Flask-Login creates secure session cookie.
*   **Authorization Flow:** `@login_required` ensures session exists. `@role_required` ensures correct role. Route-level logic explicitly verifies resource ownership/assignment before querying or modifying the database.
*   **Database Access Flow:** Views interact purely with SQLAlchemy models; no raw SQL is written.

## 5. Project Structure
```text
/
├── app/
│   ├── __init__.py           
│   ├── models/               
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── incident.py
│   │   ├── category.py
│   │   └── comment.py
│   ├── views/                
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── incidents.py
│   │   ├── admin.py          
│   │   └── dashboard.py
│   ├── forms/                
│   │   ├── __init__.py
│   │   ├── auth_forms.py
│   │   ├── admin_forms.py
│   │   └── incident_forms.py
│   ├── templates/            
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── incidents/
│   │   ├── admin/
│   │   └── dashboard/
│   ├── static/               
│   │   └── css/style.css
│   └── utils/                
│       ├── decorators.py     
│       └── constants.py      
├── tests/
│   ├── conftest.py           
│   ├── test_auth.py
│   ├── test_authorization.py
│   └── test_incidents.py
├── migrations/               
├── config.py                 
├── requirements.txt          
├── .env.example              
├── run.py                    
├── seed.py                   
└── README.md                 
```

## 6. Database Design
**Note:** All choice fields use `VARCHAR` with application-level constants.

1.  **`users`**
    *   `id` (Integer, PK)
    *   `username` (String(64), Unique, Not Null)
    *   `email` (String(120), Unique, Not Null)
    *   `password_hash` (String(256), Not Null)
    *   `role` (String(20), Not Null, Default: 'Reporter') - *Choices: 'Reporter', 'Agent', 'Admin'*
    *   `created_at` (DateTime, Not Null)

2.  **`categories`**
    *   `id` (Integer, PK)
    *   `name` (String(50), Unique, Not Null)
    *   `description` (String(200), Nullable)

3.  **`incidents`**
    *   `id` (Integer, PK)
    *   `title` (String(150), Not Null)
    *   `description` (Text, Not Null)
    *   `type` (String(20), Not Null) - *Choices: 'Bug', 'Incident'*
    *   `priority` (String(20), Not Null, Default: 'Low') - *Choices: 'Low', 'Medium', 'High', 'Critical'*
    *   `status` (String(20), Not Null, Default: 'Open') - *Choices: 'Open', 'In Progress', 'Resolved', 'Closed'*
    *   `category_id` (Integer, FK: `categories.id`, Nullable)
    *   `reporter_id` (Integer, FK: `users.id`, Not Null)
    *   `assignee_id` (Integer, FK: `users.id`, Nullable)
    *   `created_at` (DateTime, Not Null)
    *   `updated_at` (DateTime, Not Null)

4.  **`comments`**
    *   `id` (Integer, PK)
    *   `content` (Text, Not Null)
    *   `incident_id` (Integer, FK: `incidents.id`, Not Null)
    *   `user_id` (Integer, FK: `users.id`, Not Null)
    *   `created_at` (DateTime, Not Null)

## 7. Validation and Business Rules
*   **Required Fields & Constraints:** Enforced by WTForms (`DataRequired()`, Max Lengths) and SQLAlchemy (`nullable=False`).
*   **Choice Validation:** Implemented in WTForms using `SelectField(choices=...)` and backed by Python constants defined in `app/utils/constants.py`.
*   **Ownership Checks:** Route logic must verify `incident.reporter_id == current_user.id` before a Reporter can view or comment on an incident.
*   **Reporter Edit Rules:** A Reporter may only edit their own incident's `title`, `description`, `type`, and `category` **only if the status is exactly `Open`**.
*   **Agent Assignment Rules:** Admins assign Agents. Agents can only view/modify incidents where `incident.assignee_id == current_user.id`.
*   **Status Transitions:** Enforced strictly in the backend update route. Invalid transitions return an error.
*   **Comment Permissions:** User must have read access to the incident to post a comment.

## 8. Authentication and Authorization
*   **Login/Logout & Hashing:** Flask-Login with `werkzeug.security`.
*   **Cookie Security:** Session cookies must always be set with `HttpOnly=True`. The `Secure` flag must be dynamic based on environment (`Secure=False` in development/local HTTP, `Secure=True` in production HTTPS). This configuration will be documented in `config.py` and the README.
*   **Role-Based Access Control:** Custom `@role_required(*roles)` decorator.
*   **Data-Level Authorization:** Access control is enforced in backend database queries.

## 9. Routes / Endpoints
| Method | Route | Allowed Roles | Purpose & Validation |
| :--- | :--- | :--- | :--- |
| GET/POST | `/auth/login` | Public | Authenticate user. |
| GET | `/auth/logout` | Authenticated | Clear session. |
| GET | `/` | Authenticated | Redirect based on role. |
| GET | `/dashboard` | Admin, Agent | Dashboard metrics. Agent sees only metrics for their assignments. |
| GET | `/incidents` | All | List incidents. Filtered securely by role on backend. |
| GET/POST | `/incidents/create` | Reporter, Admin | Create incident. Sets `reporter_id`. |
| GET | `/incidents/<id>` | All | Detail view. Fails with 403 if user lacks ownership/assignment access. |
| POST | `/incidents/<id>/update` | Reporter, Agent, Admin | Update logic. **Reporter:** title, description, type, category (only if `Open`). **Agent:** status/classification of assigned incidents. **Admin:** status/classification. Transition rules enforced. |
| POST | `/incidents/<id>/assign` | Admin | Assign Agent. Must validate `assignee_id` belongs to an Agent. |
| POST | `/incidents/<id>/comment`| All | Add comment. Validates read access to incident. |
| GET/POST | `/admin/users` | Admin | List users and create new accounts. |
| GET/POST | `/admin/categories`| Admin | Create/list categories. |

## 10. Pages and UI
*   **Base Layout (`base.html`):** Navigation bar and flash messages.
*   **Login (`login.html`):** Credentials form.
*   **Dashboard (`dashboard.html`):** Metric cards/tables.
*   **Incident List (`list.html`):** Data table with GET form for search/filtering.
*   **Incident Creation (`create.html`):** Form for title, description, type, category.
*   **Incident Detail (`detail.html`):** Displays data. Shows conditionally restricted update forms based on role (Reporter vs. Agent). Shows assignment form if Admin. Shows comments.
*   **Admin Users (`users.html`):** User list and creation form.
*   **Admin Categories (`categories.html`):** Category list and creation form.

## 11. Incident Lifecycle
**Lifecycle:** `Open → In Progress → Resolved → Closed`

**Transition Rules:**
*   **Reporter:** Cannot change status at all.
*   **Agent:** Allowed transitions: `Open → In Progress` and `In Progress → Resolved`.
*   **Admin:** Allowed transitions: `Open → In Progress`, `In Progress → Resolved`, and `Resolved → Closed`.
*   **Strict Adherence:** No role (including Admin) can skip a status (e.g., `Open → Closed`) and incidents cannot go backward (no `Reopened` state).

## 12. Search and Filtering
*   **Filters:** Title (LIKE), Status, Priority, Type, Category, Assignee.
*   **Location:** GET parameters appended to `/incidents`. Combined via SQL `AND`.
*   **Ordering:** `created_at DESC`. No pagination required for MVP.

## 13. Dashboard
*   **Metrics:** Total, Open, In Progress, Resolved, Closed, Critical, High.
*   **Visibility:** Admins see global metrics; Agents see metrics only for their assignments. Reporters cannot access this.

## 14. Database Migration Strategy
*   **Initialization:** `flask db init`.
*   **Schema Changes:** `flask db migrate -m "message"`.
*   **Applying Changes:** `flask db upgrade`.
*   **No `db.create_all()`:** The application exclusively uses Alembic to manage schemas.

## 15. Seed / Demo Data
*   `seed.py` inserts default Categories and 3 base Users (admin, agent, reporter).
*   Does not drop tables or run `create_all()`. Requires `flask db upgrade` first.

## 16. Testing Plan
*   **Categories:** Unit and Functional (`pytest`).
*   **Authorization Matrix:**
    *   Reporter accessing `/dashboard` -> 403.
    *   Agent accessing `/admin/users` -> 403.
    *   Agent accessing/updating incident assigned to someone else -> 403.
    *   Reporter modifying their incident when status is `Resolved` -> Error/403.
*   **Assignment & Workflow Tests:**
    *   Admin assigns user without 'Agent' role -> Validation Error.
    *   Agent attempts `Open → Closed` -> Validation Error.
    *   Admin attempts `Resolved → Closed` -> Success.

## 17. Implementation Order
1.  **Foundation:** Project setup, `create_app()`, configurations (incl. Cookie security).
2.  **Database Configuration:** MySQL via `.env`.
3.  **Flask-Migrate Setup:** `flask db init`.
4.  **Models & Constants:** Write models and python choice constants. Create first migration.
5.  **Seed Data:** Write `seed.py`.
6.  **Authentication:** Flask-Login, login routes, templates.
7.  **Base Layout/UI:** HTML/CSS structure.
8.  **Authorization:** `@role_required` and backend query filters.
9.  **Incident Creation/Listing:** Reporter form.
10. **Incident Detail:** Read-only view.
11. **Admin Users/Categories:** Provisioning pages.
12. **Classification & Update:** WTForms for fields. Strict backend validation for Reporter edits (`Open` only) and Agent permissions.
13. **Assignment:** `POST /incidents/<id>/assign` route for Admins.
14. **Status Workflow:** Enforce strict sequential transitions.
15. **Comments:** Comments model, form, timeline.
16. **Search/Filter:** GET parameters logic.
17. **Dashboard:** Metric queries.
18. **Testing/Refinement:** Pytest suite for the authorization and workflow matrices.
19. **Documentation:** `README.md`.
20. **Final MVP Verification:** End-to-end manual pass.

## 18. Definition of Done
The Personal MVP is considered complete when:
*   The application uses the Factory pattern and Alembic migrations (no ENUMs).
*   Admins provision users; no public registration exists.
*   Reporters can log in, create incidents, and edit them *only* while `Open`.
*   Admins can explicitly assign incidents strictly to valid Agents.
*   Agents only process assigned incidents through the rigid `Open → In Progress → Resolved` pipeline.
*   Admins progress resolved incidents to `Closed`.
*   Comprehensive Pytest coverage exists for access control and workflow transitions.
*   A complete `README.md` allows a new developer to clone, migrate, seed, and run.

## 19. Risks and Mitigations
*   **Risk:** Invalid assignment mapping (e.g., assigning a Reporter as an Agent).
    *   **Mitigation:** `POST /incidents/<id>/assign` explicitly checks the target user's role before committing.
*   **Risk:** Horizontal/Vertical Privilege Escalation.
    *   **Mitigation:** Enforce query-level filtering (`assignee_id=current_user.id`) and comprehensive automated test coverage.
*   **Risk:** Skipping workflow states.
    *   **Mitigation:** Centralize transition logic in the update route and reject invalid jumps with validation errors.

## 20. Future Extension Roadmap
*   Advanced RBAC, Password Resets, External APIs, File Attachments, Notifications.

---

## 21. CÁC QUYẾT ĐỊNH CẦN NGƯỜI DÙNG LỰA CHỌN (Open Decisions)
*(Những phần dưới đây là chi tiết nhỏ cần chốt trước khi hoặc trong khi code để nhất quán)*

1.  **Quản lý Package Python:**
    *   *Option A (Đơn giản nhất):* Dùng `pip` và file `requirements.txt`.
    *   *Option B:* Dùng `Pipenv` hoặc `Poetry` để quản lý version chặt chẽ hơn.
    *(Đề xuất: Option A cho MVP).*
2.  **Độ khó của Mật khẩu (Password Policy):**
    *   *Option A:* Không ép ràng buộc (chỉ cần > 1 ký tự).
    *   *Option B:* Tối thiểu 6-8 ký tự. (Bạn muốn ràng buộc thêm chữ hoa/số không?)
    *(Đề xuất: Option B - tối thiểu 6 ký tự để đơn giản mà vẫn an toàn cơ bản).*
3.  **CSS Styling (Vanilla CSS):**
    *   Tuy không dùng framework, nhưng bạn có muốn ưu tiên thiết kế theo kiểu Dark Mode hay Light Mode? Hay chỉ cần một giao diện xám/trắng cơ bản có responsive?
    *(Đề xuất: Một file style.css thuần với Light Mode, bố cục Flexbox cơ bản).*
4.  **Tài khoản mặc định trong file seed.py:**
    *   Bạn muốn username/password mặc định cho 3 role là gì?
    *(Đề xuất: `admin/admin123`, `agent/agent123`, `reporter/reporter123`).*
5.  **Ngôn ngữ hiển thị (UI Language):**
    *   Web app sẽ hiển thị tiếng Anh hay tiếng Việt trên giao diện?
    *(Đề xuất: Tiếng Anh để dễ chuẩn hoá với code).*

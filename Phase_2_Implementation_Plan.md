# Phase 2 Implementation Plan

## A. Current MVP Architecture Assessment

**What is suitable for Phase 2:**
* **Modular Structure:** The application uses the Flask Application Factory pattern and Blueprints (`auth`, `admin`, `dashboard`, `incidents`), making it very easy to add new modules (e.g., `notifications`, `audit`).
* **Database Abstraction:** SQLAlchemy ORM is well-configured with Flask-Migrate, allowing smooth schema migrations for new tables like `AuditLog` and `Notification`.
* **Template Inheritance:** The `base.html` structure with flash messages and dynamic navbars is ready to accommodate notification badges and new admin links.

**What needs refactoring:**
* **Authorization:** Currently, the `role` field on the `User` model is a hardcoded string, and the `@role_required` decorator checks this string directly. This must be refactored into an RBAC model where Roles have specific Permissions, and decorators check for permissions (`@permission_required`).
* **User Model:** Needs an `is_active` boolean field for enabling/disabling accounts without deleting them.

**Technical debt or risks:**
* Transitioning from string-based roles to a relational Role/Permission model requires careful data migration to ensure existing users (Admin, Agent, Reporter) do not lose access.
* High coupling risk: Adding Audit Logging and Notifications directly into the route logic could bloat the view functions. We should abstract these into service/utility functions or use SQLAlchemy event listeners.

---

## B. Phase 2 Scope

**Included Functionality:**
1. **Advanced User Management:** Edit profile, disable/enable accounts, password reset by admin, safe deletion checks.
2. **Advanced RBAC:** Database-backed Roles and Permissions. Migration of existing authorization to permission-based checks.
3. **Audit Log:** Recording all critical actions (CRUD on incidents, user management, status changes).
4. **Notification System:** In-app, database-backed notifications for assignments, comments, and status changes.
5. **Advanced Dashboard & Reporting:** Server-rendered charts/tables for incident statistics, workload, and trends.

**Excluded Functionality:**
* Enterprise IAM (SSO, OAuth, SAML, LDAP).
* Real-time notifications (WebSockets, Redis, Message Queues).
* Email notifications or external SMS services.
* Client-side SPA frameworks (React/Vue) for the dashboard.
* File attachments for incidents.

**Future Extensions:**
* Email service integration for notifications.
* AI-driven classification and reporting.
* API rate limiting and OAuth.

---

## C. Database Changes

**New Tables:**
1. `roles`: `id`, `name`, `description`, `is_system` (to prevent deleting core roles).
2. `permissions`: `id`, `name`, `description`.
3. `role_permissions` (Association Table): `role_id`, `permission_id`.
4. `audit_logs`: `id`, `user_id` (FK), `action`, `resource_type`, `resource_id`, `details` (JSON/Text), `created_at`.
5. `notifications`: `id`, `user_id` (FK), `message`, `link`, `is_read` (Boolean), `created_at`.

**Modified Tables:**
1. `users`: 
   - Add `role_id` (FK to `roles`).
   - Add `is_active` (Boolean, default True).
   - *Migration note:* The old string `role` column will be dropped after data migration.

**Migration Sequence:**
1. Create `roles`, `permissions`, `role_permissions` tables.
2. Create `is_active` and `role_id` on `users`.
3. **Data Migration Script:** Insert default Roles (Admin, Agent, Reporter) and Permissions. Map existing users' string roles to their new `role_id`.
4. Drop old `role` column on `users`.
5. Create `audit_logs` and `notifications` tables.

---

## D. Architecture Changes

**Models:** Introduce `Role`, `Permission`, `AuditLog`, and `Notification`.
**Services/Utilities:**
* `app/utils/audit.py`: `log_action(user, action, resource, resource_id, details)`
* `app/utils/notify.py`: `create_notification(user_id, message, link)`
* `app/utils/rbac.py`: Decorator `@permission_required(permission_name)` to replace `@role_required`.
**Blueprints:** 
* Add `notifications` blueprint for handling notification views.
* Add `audit` blueprint for Admin log viewing.
**Authorization Changes:** 
* Update all routes to use `@permission_required`.
* Add `current_user.has_permission(name)` method.
**Notification Flow:** Route logic calls `create_notification` -> Saves to DB -> Displayed in Navbar via Jinja global context processor.
**Audit Flow:** Route logic calls `log_action` -> Saves to DB -> Viewable by Admins in `/admin/audit`.

---

## E. Feature Specifications

**1. Advanced User Management:**
* Admin can list, create, edit, disable, and delete users.
* **Safe Deletion:** If a user has assigned incidents or comments, soft-delete them (set `is_active = False`) or reassign their incidents to a "System" user before hard deletion. 
* Disabled users cannot log in (enforced in `login` route).

**2. Advanced RBAC:**
* Define granular permissions: `VIEW_ALL_INCIDENTS`, `EDIT_INCIDENT_STATUS`, `ASSIGN_INCIDENT`, `MANAGE_USERS`, `MANAGE_ROLES`, etc.
* Admins can create new custom roles and assign them combinations of permissions.
* Users belong to exactly one Role.

**3. Audit Log:**
* Immutable ledger. No updates or deletions allowed.
* Logs contain: Actor (User ID/Name), Action (e.g., `UPDATE_STATUS`), Resource (`Incident`), Resource ID (`#12`), Timestamp, Details (`Changed from Open to In Progress`).
* Viewable only by users with `VIEW_AUDIT_LOGS` permission.

**4. Notification System:**
* In-app dropdown in the Navbar showing unread notifications count.
* Clicking a notification marks it as read and redirects to the `link`.
* "Mark all as read" button.
* Triggers: Agent assigned, status changed, new comment on owned/assigned incident.

**5. Advanced Dashboard & Reporting:**
* **Admin View:** Total system stats, SLA breaches (e.g., Open > 24h), workload distribution by Agent (table/bar chart using simple CSS/Chart.js), incidents over time.
* **Agent View:** Personal stats (assigned, resolved this week), pending workload.
* Includes date-range filtering (e.g., `?start=2026-09-01&end=2026-09-30`).

---

## F. Route / Page Changes

**New Routes:**
* `GET /admin/users/<id>/edit`, `POST /admin/users/<id>/edit` - Edit user.
* `POST /admin/users/<id>/toggle_status` - Enable/Disable user.
* `GET /admin/roles`, `POST /admin/roles/create` - Manage roles.
* `GET /admin/audit` - View audit logs.
* `GET /notifications` - List notifications.
* `POST /notifications/<id>/read` - Mark read.

**Changed Routes:**
* All `admin_routes.py` and `incidents_routes.py` will have `@permission_required(...)` instead of `@role_required(...)`.
* `POST /incidents/<id>/update`, `POST /incidents/<id>/assign`, `POST /incidents/<id>/comment` will now trigger `log_action` and `create_notification`.
* `GET /` and `GET /dashboard` will load extended statistics based on user permissions.

**Affected Templates:**
* `base.html`: Add notification bell and badge. Add Audit Log link for Admins.
* `admin/users.html`: Add Edit and Disable buttons.
* `dashboard/index.html`: Complete revamp for reporting.

---

## G. Testing Strategy

1. **User Management:** Test login failure for disabled users. Test safe-deletion checks preventing foreign key crashes.
2. **RBAC Regression:** Test all existing MVP routes with the new `@permission_required` decorator. Ensure a Reporter cannot access Admin routes.
3. **Audit Logging:** Unit test the `log_action` utility. Verify that calling a POST route correctly writes an `AuditLog` record to the test database.
4. **Notifications:** Test that assigning an incident creates exactly one notification for the assignee. Test marking as read.
5. **Reporting:** Test dashboard queries with specific date-range parameters to ensure accurate counting.

---

## H. Implementation Order

1. **Advanced RBAC (Foundation):** 
   - Create Role/Permission models. 
   - Generate migration and write data-migration logic to port existing string roles. 
   - Implement `has_permission` and `@permission_required`. Replace all MVP auth decorators.
2. **Advanced User Management:** 
   - Add `is_active` to User. 
   - Build Edit/Disable/Delete routes and UI. Prevent login for disabled users.
3. **Audit Log:** 
   - Create `AuditLog` model and `log_action` utility. 
   - Integrate into existing Incident and Admin POST routes. 
   - Build `/admin/audit` UI.
4. **Notification System:** 
   - Create `Notification` model and `create_notification` utility. 
   - Integrate into Incident workflow (assignment, status, comments). 
   - Build UI in `base.html` and `/notifications`.
5. **Advanced Dashboard & Reporting:** 
   - Write advanced SQLAlchemy aggregations. 
   - Update `dashboard/index.html` with new metrics and tables.

---

## I. Definition of Done

* Phase 2 code is fully merged into the main branch.
* No regressions in MVP functionality (creating, updating, assigning incidents works).
* RBAC is database-driven and string-based roles are entirely removed.
* Disabled users cannot log in.
* Every Incident status change and assignment generates an accurate Audit Log entry.
* Assigning an Agent triggers an in-app notification that can be marked as read.
* Admin dashboard displays aggregated data correctly filtered by date.

---

## J. Risks and Mitigations

* **Authorization Regressions:** 
  * *Mitigation:* Create a strict mapping of old Roles to new Permissions. Write automated tests that mimic Reporter and Agent requests to Admin routes to guarantee 403 errors.
* **Migration Complexity:** 
  * *Mitigation:* The data migration (converting string roles to FKs) must be wrapped in a transaction. If it fails, rollback. Do not drop the old `role` column until the data migration is verified.
* **Excessive Coupling (Fat Routes):** 
  * *Mitigation:* Keep route handlers clean by moving Notification and Audit logic into dedicated utility functions (`notify.py`, `audit.py`). 
* **Notification Spam:** 
  * *Mitigation:* Only trigger notifications for *changes* (e.g., don't notify if status is updated to the same status).
* **Scope Creep:** 
  * *Mitigation:* Stick strictly to the defined UI/UX. Do not build email integrations or real-time WebSockets.

---

## K. Final Recommended Architecture

The system will evolve from a simple MVP to a robust, enterprise-ready application while remaining lightweight. It will retain the Flask Application Factory and Blueprint pattern. 

Authorization will be entirely decoupled from code via a dynamic RBAC module, allowing administrators to configure permissions without developer intervention. Incident state changes will act as a central nervous system, triggering decoupled Utility modules that write to the Audit Log and Notification tables independently. The Dashboard will act as a read-only aggregation layer sitting on top of the Incident data, separated safely by user permission levels.

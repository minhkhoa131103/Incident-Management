# Phase 2 Implementation Plan

## 1. Current MVP Architecture Assessment

**What is suitable for Phase 2:**
* **Modular Structure:** The application uses the Flask Application Factory pattern and Blueprints (`auth`, `admin`, `dashboard`, `incidents`), which scales cleanly.
* **Database Abstraction:** SQLAlchemy ORM and Flask-Migrate handle schema updates securely.
* **Template Inheritance:** The Jinja2 `base.html` structure supports UI extensions like notification dropdowns easily.

**What needs refactoring:**
* **Authorization:** Currently, `role` is a hardcoded string on `User`, checked by `@role_required`. This must be refactored into a relational RBAC model, relying on predefined granular permissions and a new `@permission_required` decorator. 
  * *Crucial note:* `@permission_required` does **not** replace incident-specific business rules. Both permission checks and existing MVP ownership/workflow rules must be enforced together.
* **User Status:** `User` needs an `is_active` field to allow disabling accounts instead of deleting them.

**Technical debt or risks:**
* Transitioning from string-based roles to a relational Role/Permission model poses a risk of locking out existing users if the data migration is not verified before dropping the old column.
* High coupling risk: We must avoid cluttering existing routes by abstracting logging and notifications into explicit utility functions.

---

## 2. Phase 2 Scope

**Included Functionality:**
1. **Advanced Admin User Management:** Admins can list, edit, disable (`is_active = False`), and hard-delete users (only if NO related records exist across all foreign-key relationships).
2. **Advanced RBAC:** Predefined system permissions. Admins can create custom roles by grouping these predefined permissions. Core system roles (Admin, Agent, Reporter) are protected from deletion.
3. **Audit Log:** Explicit, immutable logging of critical administrative and business actions.
4. **Notification System:** In-app notifications with clear, strict recipient rules for assignments, status changes, and comments, ensuring deduplication and actor exclusion.
5. **Advanced Dashboard & Reporting:** Server-rendered analytics showing workload by Agent, aging incidents, status/priority distributions, and date-range filters.

**Excluded Functionality:**
* Enterprise IAM (SSO, OAuth, SAML, LDAP).
* Real-time notifications (WebSockets, Redis, Message Queues).
* Email notifications or external SMS services.
* Client-side SPA frameworks (React/Vue).
* Admin UI for creating new system permissions (permissions are predefined in code/database).
* SLA enforcement or SLA-specific business rules.
* User self-service profile editing.
* Reassigning incidents to a fake or "System" user for deletion purposes.

---

## 3. Database Changes

**New Tables:**
1. `permissions`: `id`, `name`, `description`. (Populated by seed data only, immutable via UI).
2. `roles`: `id`, `name`, `description`, `is_system` (Boolean).
3. `role_permissions` (Association Table): `role_id`, `permission_id`.
4. `audit_logs`: `id`, `user_id` (FK to Actor), `action`, `resource_type`, `resource_id`, `details` (JSON/Text), `created_at`.
5. `notifications`: `id`, `user_id` (FK to Recipient), `message`, `link`, `is_read` (Boolean), `created_at`.

**Modified Tables:**
1. `users`: 
   - Add `role_id` (FK to `roles`).
   - Add `is_active` (Boolean, default True).

**Safe Data Migration Sequence:**
1. Generate migration to create `roles`, `permissions`, `role_permissions` tables, and add `role_id`, `is_active` columns to `users` (nullable initially).
2. Seed predefined system permissions.
3. Seed predefined system roles (Admin, Agent, Reporter) and assign their default permissions.
4. Data Migration: Map existing users' string `role` values to the correct `role_id`.
5. Verification step: Ensure no user is left with a null `role_id`.
6. Generate migration to alter `role_id` to `nullable=False` and drop the old `role` string column.

---

## 4. Architecture

**Preserved Core:** Flask Application Factory, Blueprints, SQLAlchemy, Flask-Migrate, Jinja2 SSR.

**New Services/Utilities:**
* `app/utils/rbac.py`: Decorator `@permission_required(permission_name)` to enforce base authorization. *This operates alongside, not instead of, MVP backend business logic checks.*
* `app/utils/audit.py`: `log_action(user_id, action, resource, resource_id, details)`. Called explicitly within route handlers. No SQLAlchemy events to avoid side-effects.
* `app/utils/notify.py`: `create_notification(recipient_id, message, link)`. Called explicitly within route handlers.

---

## 5. Feature Specifications

**1. Advanced User Management**
* **Purpose:** Allow Admins to manage staff accounts safely.
* **Functional Requirements:** Admins can edit user details (email, role). Admins can toggle `is_active`. Disabled users cannot log in.
* **Hard Deletion Safety:** Disabling (`is_active = False`) is the primary way to deactivate users. Hard delete is allowed **only** when the user has **no related records across all relevant foreign-key relationships** (e.g., incidents, comments, audit logs, notifications). Audit/history data must never be orphaned or silently lost. If any related data exists, the system blocks the deletion entirely and instructs the Admin to disable the account instead.
* **Auth:** Requires `MANAGE_USERS` permission.

**2. Advanced RBAC**
* **Purpose:** Move away from hardcoded roles to permission-based checks while preserving all MVP rules.
* **Predefined Permissions:** `VIEW_INCIDENT`, `CREATE_INCIDENT`, `EDIT_INCIDENT`, `UPDATE_INCIDENT_STATUS`, `ASSIGN_INCIDENT`, `MANAGE_USERS`, `MANAGE_ROLES`, `VIEW_AUDIT_LOGS`, `VIEW_DASHBOARD`.
* **Dual-Layer Authorization:** Permissions determine if a user *can* perform a type of action. Existing MVP business rules *must remain enforced separately in backend logic*. 
  * Reporter can only edit their own incidents while status is Open.
  * Agent can only process incidents assigned to them.
  * Strict status workflow: `Open → In Progress → Resolved → Closed`.
  * Only Admin can close an incident. No arbitrary status transitions.
* **Functional Requirements:** Admins can view roles, create custom roles, and assign predefined permissions to them. Core roles (`is_system = True`) cannot be deleted. 

**3. Audit Log**
* **Purpose:** Maintain an explicit, immutable ledger of critical actions.
* **Logged Actions:** Incident creation/updates, status changes, assignments, user creation/modification, user enable/disable, role changes, category changes.
* **Functional Requirements:** Logs capture Actor, Action, Resource, ID, Timestamp, Details. Viewable in a tabular list. Handled explicitly via `log_action()` in the routes.
* **Auth:** Requires `VIEW_AUDIT_LOGS` permission.

**4. Notification System**
* **Purpose:** Alert users of updates in-app.
* **Recipient Rules:**
  - *General Rule:* Always exclude the actor who triggered the event. Remove duplicate recipients (e.g., if Reporter and Agent are the same user, create only one notification).
  - *Assignment:* Notify the newly assigned Agent only. (If unassigned or no agent exists, do not create an Agent notification).
  - *Status change:* Notify the Reporter + assigned Agent (if applicable).
  - *Comment:* Notify the Reporter + assigned Agent (if applicable).
* **Functional Requirements:** Notifications appear in a Navbar dropdown. Clicking marks them as read. "Mark all as read" functionality. Notifications remain in-app only.

**5. Advanced Dashboard & Reporting**
* **Purpose:** Provide operational insights using existing data.
* **Functional Requirements:** 
  - Incident aging (e.g., incidents open for > 7 days).
  - Workload distribution by Agent.
  - Status/Priority/Category distributions.
  - Incidents over time chart/table.
  - Date-range filtering via GET parameters.
* **Auth:** Requires `VIEW_DASHBOARD`. Output dynamically adjusts based on user's visibility scope (Agent sees own workload, Admin sees overall).

---

## 6. Routes

**New Routes:**
* `GET/POST /admin/users/<id>/edit` - Edit user profile/role.
* `POST /admin/users/<id>/toggle_status` - Enable/disable account.
* `POST /admin/users/<id>/delete` - Hard delete. *Explicitly queries all related tables (Incident, Comment, AuditLog, Notification) and aborts/flashes error if any FK exists.*
* `GET /admin/roles`, `GET/POST /admin/roles/create`, `GET/POST /admin/roles/<id>/edit`
* `GET /admin/audit` - View audit logs.
* `GET /notifications` - View all notifications.
* `POST /notifications/<id>/read`, `POST /notifications/read_all`.

**Changed Routes:**
* All routes currently using `@role_required` updated to `@permission_required`.
* Existing `POST` routes in `incidents_routes.py` and `admin_routes.py` injected with `log_action()` and `create_notification()` where appropriate.
* `/auth/login` checks `is_active`.

---

## 7. Templates/UI

* `base.html`: Add notification bell. Add Audit Logs and Roles to Admin menu.
* `admin/users.html`: Add "Edit", "Disable", "Delete" buttons. The Delete button must gracefully handle rejection.
* `admin/roles.html`: List roles, identify system roles visually, form to assign checkboxes for permissions.
* `admin/audit.html`: Table displaying immutable audit logs with search/filter.
* `dashboard/index.html`: Enhanced layout for tables/charts representing distribution metrics and date filters.

---

## 8. Testing Strategy

1. **User Management:** Test login denial for disabled users. Rigorously test the hard-delete safety check by attempting to delete a user with an associated AuditLog, Comment, Notification, or Incident, guaranteeing the system blocks it.
2. **RBAC + MVP Rules:** Test the dual-layer authorization. Verify that a user with `EDIT_INCIDENT` permission is still blocked by business logic if they try to edit an incident they don't own, or an incident that is no longer `Open`. Test all strict workflow transitions.
3. **Audit Log:** Ensure `log_action` creates records accurately on Incident update. Ensure unauthorized users get 403 on `/admin/audit`.
4. **Notifications:** Mock an assignment and verify only the newly assigned Agent receives a notification. Test comment notification excludes the commenter and deduplicates recipients successfully.
5. **Dashboard:** Verify date-range GET parameters correctly limit the queries for distributions.

---

## 9. Implementation Order

1. **Advanced RBAC (Foundation):** 
   - Define Permissions/Roles models. 
   - Generate migration, seed permissions/roles, map users, verify, drop old column.
   - Implement `@permission_required` and apply it alongside MVP business rules.
2. **Advanced User Management:** 
   - Add `is_active`. Build Edit, Toggle, and strict Safe Delete logic checking all FKs.
   - Block disabled users from logging in.
3. **Audit Log:** 
   - Define `AuditLog` model and `log_action` utility.
   - Inject explicit logging calls into all relevant POST routes.
   - Build `/admin/audit` UI.
4. **Notification System:** 
   - Define `Notification` model and `create_notification` utility.
   - Implement the strict, deduplicated recipient rules in assignment, status change, and comment logic.
   - Build Navbar UI and mark-read routes.
5. **Advanced Dashboard & Reporting:** 
   - Build SQLAlchemy aggregation queries for aging and distributions.
   - Implement date-range filtering. Update UI.

---

## 10. Definition of Done

* Phase 2 code is fully implemented and tested.
* **No regressions:** MVP behavior remains completely intact (Reporter ownership, Agent assignment bounds, strict Open->In Progress->Resolved->Closed workflow). RBAC permissions work alongside these rules, not over them.
* RBAC migration is complete without data loss or stranded users.
* Users can be disabled safely. Hard deletion acts as an impenetrable safety net, perfectly blocking deletion if a single related record exists across any foreign-key relationship.
* The Audit Log tracks every specified action via explicit `log_action` calls.
* Notifications fire exactly according to the precise recipient rules, always excluding the actor, deduplicating recipients, and remaining in-app only.
* Dashboard renders distribution and aging metrics based on date ranges.

---

## 11. Risks and Mitigations

* **Authorization Regressions:** 
  * *Mitigation:* Explicit test coverage ensuring old MVP rules (e.g., Reporter edits restricted to Open incidents) are preserved under the new Permission model. Do not replace business logic checks with permission checks; use both.
* **Orphaned History via Deletion:**
  * *Mitigation:* Broaden the hard-delete safety check to query `Incident`, `Comment`, `AuditLog`, and `Notification`. If any `user_id` matches, block the operation instantly.
* **Audit and Notification Over-engineering:** 
  * *Mitigation:* Avoid SQLAlchemy event listeners. Keep `log_action` and `create_notification` explicit and imperative in the route handlers.
* **Spam Notifications:** 
  * *Mitigation:* Enforce strict recipient logic: collect recipients in a `set()` to deduplicate, discard the `current_user.id`, and ignore unassigned Agents (`None`).

---

## 12. Final Architecture

The system will move from basic hardcoded string-based roles to a robust, dynamic RBAC architecture. The Flask Application Factory will house explicitly called Utility modules (`audit`, `notify`) that operate synchronously within the main request cycle, keeping the architecture easy to trace and maintain. The system avoids external dependencies (no Redis, no message queues, no email servers), remaining a highly cohesive, monolithic student project that enforces strict business rules through database constraints and explicit backend logic.

---

## Review Summary

* **What was changed:** 
  1. **Separated RBAC Permissions from MVP Rules:** Explicitly stated that `@permission_required` operates *alongside* MVP business logic. All strict ownership and workflow transition rules are preserved in backend logic.
  2. **Notification Recipient Rules Explicit:** Defined exact targets for notifications (Assign -> New Agent; Status/Comment -> Reporter + Agent). Added mandatory rules to exclude the actor triggering the event, deduplicate recipients, and handle unassigned states.
  3. **Strengthened Hard-Delete Safety:** Removed the "System User" migration workaround. Hard deletion now actively checks all foreign key relationships (Incidents, Comments, Audits, Notifications). Deletion is entirely blocked if *any* related record exists, protecting historical integrity.
* **Why it was changed:** To prevent permission abstractions from eroding critical MVP business rules, to stop notification spam/duplicates, and to ensure strict referential integrity without resorting to ghost/system accounts. 
* **Remaining Ambiguities:** None. The plan is now completely specified for immediate implementation.

# Role-Based Access Control (RBAC) Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Components](#components)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Decorators](#decorators)
8. [Seeding Data](#seeding-data)
9. [Flow Diagrams](#flow-diagrams)
10. [Best Practices](#best-practices)

---

## Overview

### What is RBAC?

**Role-Based Access Control (RBAC)** is a security mechanism that restricts system access based on a user's role within an organization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RBAC CONCEPT                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   TRADITIONAL (User → Permissions)     │   RBAC (User → Role → Permissions)│
│   ─────────────────────────────────    │   ────────────────────────────────│
│                                         │                                    │
│   User A ─→ [read, update, delete]     │   User A ─→ Admin ─→ [all perms]  │
│   User B ─→ [read, update, delete]     │   User B ─→ Admin ─→ [all perms]  │
│   User C ─→ [read, update]             │   User C ─→ Moderator ─→ [r, u]   │
│   User D ─→ [read]                     │   User D ─→ User ─→ [read]        │
│                                         │                                    │
│   Change = Update each user            │   Change = Update role once        │
│                                         │                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Benefits

| Benefit             | Description                                                  |
| ------------------- | ------------------------------------------------------------ |
| **Scalability**     | Add new users by assigning roles, not individual permissions |
| **Maintainability** | Update role once, affects all users with that role           |
| **Security**        | Principle of least privilege - users only get what they need |
| **Audit**           | Easy to see who has what access                              |
| **Flexibility**     | Role inheritance + direct permissions for exceptions         |

### Our Implementation: Hybrid RBAC

This implementation supports:

-   ✅ **Role-based permissions** - Users get permissions from assigned roles
-   ✅ **Role inheritance** - Roles can inherit from parent roles
-   ✅ **Direct permissions** - Individual users can have extra permissions beyond their roles
-   ✅ **Wildcard permissions** - `*:*` for super admin, `users:*` for all user operations

---

## Architecture

### Module Structure

```
app/
├── models/
│   ├── permission.py        # Permission model
│   ├── role.py              # Role model with inheritance
│   ├── associations.py      # Many-to-many junction tables
│   └── user.py              # User model (updated with RBAC relationships)
│
├── rbac/                    # RBAC module
│   ├── __init__.py          # Module exports
│   ├── decorators.py        # @permission_required, @role_required
│   ├── permissions.py       # Permission constants & registry
│   ├── services.py          # RBACService business logic
│   └── exceptions.py        # RBAC-specific exceptions
│
├── schemas/
│   └── rbac.py              # Pydantic schemas for RBAC
│
└── routes/v1/admin/
    ├── __init__.py          # Admin routes blueprint
    ├── roles.py             # Role management endpoints
    └── permissions.py       # Permission management endpoints
```

### Component Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────────────┐                                                     │
│   │     Routes        │  @permission_required("users:delete")               │
│   │  (API Endpoints)  │                                                     │
│   └─────────┬─────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│   ┌───────────────────┐                                                     │
│   │   Decorators      │  Checks permissions/roles before route execution    │
│   │ (Route Protection)│                                                     │
│   └─────────┬─────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│   ┌───────────────────┐                                                     │
│   │   RBACService     │  Business logic for permission checking             │
│   │ (Business Logic)  │                                                     │
│   └─────────┬─────────┘                                                     │
│             │                                                                │
│             ▼                                                                │
│   ┌───────────────────┐                                                     │
│   │     Models        │  Permission, Role, User relationships               │
│   │  (Data Layer)     │                                                     │
│   └───────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   users.users                              rbac.roles                        │
│   ┌──────────────────────┐                 ┌──────────────────────┐         │
│   │ id (PK)              │                 │ id (PK)              │         │
│   │ username             │                 │ name                 │         │
│   │ email                │                 │ display_name         │         │
│   │ password_hash        │                 │ description          │         │
│   │ first_name           │                 │ is_system_role       │         │
│   │ ...                  │                 │ parent_role_id (FK)  │→────┐   │
│   └──────────┬───────────┘                 │ created_at           │     │   │
│              │                             │ is_deleted           │     │   │
│              │                             └──────────┬───────────┘     │   │
│              │                                        │                 │   │
│              │         rbac.user_roles                │                 │   │
│              │    ┌───────────────────────┐           │                 │   │
│              └───▶│ user_id (FK)          │◀──────────┘                 │   │
│                   │ role_id (FK)          │                             │   │
│                   │ assigned_at           │         Self-reference      │   │
│                   │ assigned_by (FK)      │         (inheritance)       │   │
│                   └───────────────────────┘              ◀──────────────┘   │
│                                                                              │
│   rbac.permissions                                                          │
│   ┌──────────────────────┐                                                  │
│   │ id (PK)              │                                                  │
│   │ name                 │  e.g., "users:delete"                           │
│   │ resource             │  e.g., "users"                                  │
│   │ action               │  e.g., "delete"                                 │
│   │ description          │                                                  │
│   │ created_at           │                                                  │
│   └──────────┬───────────┘                                                  │
│              │                                                              │
│              ├───────────────────────┐                                      │
│              │                       │                                      │
│              ▼                       ▼                                      │
│   ┌────────────────────┐   ┌────────────────────┐                          │
│   │ rbac.role_         │   │ rbac.user_         │                          │
│   │ permissions        │   │ permissions        │                          │
│   ├────────────────────┤   ├────────────────────┤                          │
│   │ role_id (FK)       │   │ user_id (FK)       │                          │
│   │ permission_id (FK) │   │ permission_id (FK) │                          │
│   │ granted_at         │   │ granted_at         │                          │
│   └────────────────────┘   │ granted_by (FK)    │                          │
│                            │ reason             │  (audit trail)            │
│                            └────────────────────┘                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Permission Naming Convention

```python
# Format: {resource}:{action}
# Examples:
"users:read"       # Read user data
"users:create"     # Create new users
"users:update"     # Update user data
"users:delete"     # Delete users (soft delete)
"users:list"       # List all users

"roles:read"       # View roles
"roles:create"     # Create new roles
"roles:assign"     # Assign roles to users

# Wildcards
"*:*"              # All permissions (super admin)
"users:*"          # All permissions on users resource
```

---

## Components

### 1. Permission Model

```python
# app/models/permission.py

class Permission(BaseModel):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "rbac"}

    name = Column(String(100), unique=True)  # "users:delete"
    resource = Column(String(50))             # "users"
    action = Column(String(50))               # "delete"
    description = Column(Text)
```

### 2. Role Model

```python
# app/models/role.py

class Role(BaseModel):
    __tablename__ = "roles"
    __table_args__ = {"schema": "rbac"}

    name = Column(String(50), unique=True)    # "admin"
    display_name = Column(String(100))         # "Administrator"
    description = Column(Text)
    is_system_role = Column(Boolean)           # Can't delete if True
    parent_role_id = Column(Integer, ForeignKey("rbac.roles.id"))

    # Relationships
    permissions = relationship("Permission", secondary="rbac.role_permissions")
    users = relationship("User", secondary="rbac.user_roles")
    parent_role = relationship("Role", remote_side=[id])
```

### 3. User Model Extensions

```python
# app/models/user.py (added fields)

class User(BaseModel):
    # ... existing fields ...

    # RBAC Relationships
    roles = relationship("Role", secondary="rbac.user_roles")
    direct_permissions = relationship("Permission", secondary="rbac.user_permissions")

    # Helper methods
    def has_permission(self, permission: str) -> bool: ...
    def has_role(self, role_name: str) -> bool: ...
    def get_all_permissions(self) -> set: ...
```

### 4. RBACService

```python
# app/rbac/services.py

class RBACService:
    @staticmethod
    def user_has_permission(user, permission): ...

    @staticmethod
    def assign_role_to_user(user, role_name, assigned_by=None): ...

    @staticmethod
    def grant_direct_permission(user, permission_name, granted_by=None): ...

    @staticmethod
    def seed_all(): ...  # Seed permissions and roles
```

### 5. Decorators

```python
# app/rbac/decorators.py

@permission_required("users:delete")          # Single permission
@permission_required("a:x", "b:y")            # ANY of these
@permission_required("a:x", "b:y", require_all=True)  # ALL required

@role_required("admin")                       # Single role
@role_required("admin", "moderator")          # ANY of these roles
```

---

## Usage

### Protecting Routes

```python
from app.rbac import permission_required, role_required

# Require specific permission
@app.route("/users/<id>", methods=["DELETE"])
@permission_required("users:delete")
def delete_user(id):
    # Only users with "users:delete" permission can access
    pass

# Require specific role
@app.route("/admin/dashboard")
@role_required("admin", "super_admin")
def admin_dashboard():
    # Only admins or super admins can access
    pass

# Require ALL permissions
@app.route("/reports/export")
@permission_required("reports:read", "reports:export", require_all=True)
def export_report():
    # User needs BOTH permissions
    pass
```

### Programmatic Permission Checking

```python
from app.rbac import check_permission, RBACService

# In a route handler
@app.route("/users/<id>")
@jwt_required()
def get_user(id):
    user_data = get_user_data(id)

    # Show sensitive info only if user has permission
    if check_permission("users:view_sensitive"):
        user_data["ssn"] = get_sensitive_info(id)

    return user_data

# In service layer
def some_service_function(current_user, target_user_id):
    # Raise exception if no permission
    RBACService.require_permission(current_user, "users:update")
    # Continue with operation...
```

### Assigning Roles

```python
from app.rbac import RBACService

# Assign role to user
RBACService.assign_role_to_user(user, "moderator", assigned_by=admin_user)

# Revoke role from user
RBACService.revoke_role_from_user(user, "moderator", revoked_by=admin_user)

# Grant direct permission
RBACService.grant_direct_permission(
    user,
    "users:delete",
    granted_by=admin_user,
    reason="Temporary access for cleanup project"
)
```

---

## API Endpoints

### Role Management

| Method | Endpoint                     | Permission     | Description       |
| ------ | ---------------------------- | -------------- | ----------------- |
| GET    | `/api/v1/admin/roles`        | `roles:list`   | List all roles    |
| POST   | `/api/v1/admin/roles`        | `roles:create` | Create a new role |
| GET    | `/api/v1/admin/roles/<name>` | `roles:read`   | Get role details  |
| PUT    | `/api/v1/admin/roles/<name>` | `roles:update` | Update a role     |
| DELETE | `/api/v1/admin/roles/<name>` | `roles:delete` | Delete a role     |

### User Role Assignment

| Method | Endpoint                                | Permission     | Description           |
| ------ | --------------------------------------- | -------------- | --------------------- |
| GET    | `/api/v1/admin/roles/users/<id>`        | `roles:read`   | Get user's roles      |
| POST   | `/api/v1/admin/roles/users/<id>`        | `roles:assign` | Assign role to user   |
| DELETE | `/api/v1/admin/roles/users/<id>/<role>` | `roles:revoke` | Revoke role from user |

### Permission Management

| Method | Endpoint                                      | Permission           | Description              |
| ------ | --------------------------------------------- | -------------------- | ------------------------ |
| GET    | `/api/v1/admin/permissions`                   | `permissions:list`   | List all permissions     |
| GET    | `/api/v1/admin/permissions/<name>`            | `permissions:read`   | Get permission details   |
| GET    | `/api/v1/admin/permissions/users/<id>`        | `permissions:read`   | Get user's permissions   |
| POST   | `/api/v1/admin/permissions/users/<id>`        | `permissions:assign` | Grant direct permission  |
| DELETE | `/api/v1/admin/permissions/users/<id>/<perm>` | `permissions:revoke` | Revoke direct permission |

---

## Seeding Data

### CLI Commands

```bash
# Seed permissions and default roles
python db_manage.py seed-rbac

# Assign super_admin role to a user
python db_manage.py assign-admin <username>
```

### Default Roles

| Role          | Permissions                                | Description           |
| ------------- | ------------------------------------------ | --------------------- |
| `super_admin` | `*:*`                                      | Full system access    |
| `admin`       | All user + role management                 | Administrative access |
| `moderator`   | `users:read`, `users:update`, `users:list` | Content moderation    |
| `user`        | `users:read`                               | Basic user access     |

---

## Flow Diagrams

### Permission Check Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERMISSION CHECK FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   HTTP Request                                                               │
│   DELETE /api/v1/users/5                                                    │
│   Authorization: Bearer <token>                                              │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────┐                    │
│   │          @permission_required("users:delete")       │                    │
│   └────────────────────────────────────────────────────┘                    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌─────────────────┐      ┌─────────────────┐                              │
│   │ Verify JWT      │──NO─▶│  401 Unauthorized│                              │
│   │ Token           │      └─────────────────┘                              │
│   └────────┬────────┘                                                        │
│            │ YES                                                             │
│            ▼                                                                 │
│   ┌─────────────────┐      ┌─────────────────┐                              │
│   │ Get Current     │──NO─▶│  401 Unauthorized│                              │
│   │ User            │      └─────────────────┘                              │
│   └────────┬────────┘                                                        │
│            │ YES                                                             │
│            ▼                                                                 │
│   ┌─────────────────┐      ┌─────────────────┐                              │
│   │ User Active?    │──NO─▶│  403 Forbidden   │                              │
│   │                 │      │  (deactivated)   │                              │
│   └────────┬────────┘      └─────────────────┘                              │
│            │ YES                                                             │
│            ▼                                                                 │
│   ┌────────────────────────────────────────────────────┐                    │
│   │         RBACService.user_has_permission()          │                    │
│   ├────────────────────────────────────────────────────┤                    │
│   │  1. Get all user roles                              │                    │
│   │  2. For each role, get permissions (+ inherited)    │                    │
│   │  3. Get user's direct permissions                   │                    │
│   │  4. Combine into effective_permissions              │                    │
│   │  5. Check if "users:delete" in effective_permissions│                    │
│   │  6. Check wildcards (*:* and users:*)               │                    │
│   └────────────────────────────────────────────────────┘                    │
│            │                                                                 │
│        ┌───┴───┐                                                            │
│        │       │                                                            │
│       YES      NO                                                           │
│        │       │                                                            │
│        ▼       ▼                                                            │
│   ┌─────────┐  ┌──────────────────────────────────────┐                    │
│   │ Execute │  │  403 Forbidden                        │                    │
│   │ Route   │  │  "Insufficient permissions"           │                    │
│   │ Handler │  │  details: {required: ["users:delete"]}│                    │
│   └─────────┘  └──────────────────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Effective Permissions Calculation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               EFFECTIVE PERMISSIONS CALCULATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   User: tejas@example.com                                                   │
│                                                                              │
│   Step 1: Get User's Roles                                                  │
│   ─────────────────────────                                                 │
│   user.roles = [moderator]                                                  │
│                                                                              │
│   Step 2: Get Role Permissions (including inherited)                        │
│   ──────────────────────────────────────────────────                        │
│                                                                              │
│   moderator.permissions = [users:read, users:update]                        │
│   moderator.parent_role = user                                              │
│                                                                              │
│   user.permissions = [users:read]  (already has, no new ones)              │
│   user.parent_role = None                                                   │
│                                                                              │
│   role_permissions = {users:read, users:update}                             │
│                                                                              │
│   Step 3: Get Direct Permissions                                            │
│   ───────────────────────────────                                           │
│   user.direct_permissions = [users:delete]  (granted for special project)  │
│                                                                              │
│   Step 4: Combine All                                                       │
│   ───────────────────                                                       │
│   effective_permissions = role_permissions ∪ direct_permissions             │
│                                                                              │
│   effective_permissions = {                                                 │
│       "users:read",      ← from role                                        │
│       "users:update",    ← from role                                        │
│       "users:delete"     ← DIRECT (extra permission)                        │
│   }                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### 1. Use Role-Based Permissions Primarily

```
✅ GOOD: Most permissions come from ROLES
⚠️ CAUTION: Direct permissions for EXCEPTIONS only
❌ BAD: Every user has unique direct permissions
```

### 2. Follow Permission Naming Convention

```python
# Format: {resource}:{action}
# ✅ Good
"users:delete"
"reports:export"
"settings:update"

# ❌ Bad
"deleteUser"
"can-export-reports"
"UPDATE_SETTINGS"
```

### 3. Use Specific Permissions, Not Roles

```python
# ✅ Good - checks specific capability
@permission_required("users:delete")
def delete_user():
    pass

# ⚠️ Less ideal - ties implementation to role names
@role_required("admin")
def delete_user():
    pass
```

### 4. Log Permission Denials

```python
# The decorators automatically log permission denials
# Check logs for security auditing
```

### 5. Create New Roles Instead of Many Direct Permissions

```
If many users need the same direct permission
→ Create a new role with that permission!
```

---

## Testing RBAC

### Unit Testing

```python
def test_user_has_permission():
    # Create user with role
    user = create_test_user()
    role = create_role_with_permissions(["users:read"])
    user.roles.append(role)

    assert user.has_permission("users:read") is True
    assert user.has_permission("users:delete") is False

def test_wildcard_permission():
    user = create_test_user()
    super_admin = create_role_with_permissions(["*:*"])
    user.roles.append(super_admin)

    # Super admin has all permissions
    assert user.has_permission("users:delete") is True
    assert user.has_permission("anything:anything") is True
```

### Integration Testing

```python
def test_protected_endpoint():
    # User without permission should get 403
    response = client.delete("/api/v1/users/1", headers=user_headers)
    assert response.status_code == 403

    # Admin should succeed
    response = client.delete("/api/v1/users/1", headers=admin_headers)
    assert response.status_code == 200
```

---

## Troubleshooting

### Common Issues

| Issue                         | Solution                                    |
| ----------------------------- | ------------------------------------------- |
| 403 Forbidden unexpectedly    | Check if user has role, role has permission |
| Permissions not seeded        | Run `python db_manage.py seed-rbac`         |
| Role inheritance not working  | Check `parent_role_id` is set correctly     |
| Direct permission not working | Ensure permission exists in database        |

### Debugging

```python
# Check user's effective permissions
from app.rbac import RBACService

with app.app_context():
    user = User.query.get(1)
    print(f"Roles: {[r.name for r in user.roles]}")
    print(f"Permissions: {RBACService.get_user_permissions(user)}")
```

---

## Related Documentation

-   [JWT Authentication](./JWT_AUTHENTICATION.md)
-   [Standardized API Responses](./STANDARDIZED_API_RESPONSES.md)
-   [Error Handling](./error-handling/)

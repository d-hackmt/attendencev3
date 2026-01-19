# 🚀 Scaling Suggestions: Multi-Admin & Multi-User Architecture

To scale from a single-admin MVP to a robust multi-user system, you need to transition Authorization and Data Ownership from "Environment Variables" to the "Database".

---

## 1. Database Schema Changes (Supabase)

You need to move away from `ADMIN_USERNAME` in `.env` to a proper `users` table.

### New Tables

#### `users`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | Primary Key (Default: `uuid_generate_v4()`) |
| `email` | Text | Unique, used for login |
| `password_hash` | Text | Argon2/Bcrypt hash (Never store plain text!) |
| `role` | Text | 'super_admin', 'admin', 'teacher', 'student' |
| `name` | Text | Display name |

#### `class_owners` (Many-to-Many)
This connects specific admins/teachers to specific classes so they only see *their* classes.
| Column | Type | Description |
| :--- | :--- | :--- |
| `class_name` | Text | FK to `classroom_settings` |
| `user_id` | UUID | FK to `users` |

---

## 2. Authentication Logic (`auth_service.py`)

### Current vs New
*   **Current**: Checks `if username == os.getenv("ADMIN")`.
*   **New**:
    1.  Fetch user by email from `users` table.
    2.  Verify password hash using `bcrypt` or `argon2`.
    3.  Generate a **JWT Token** or store `user_id` in `st.session_state`.

### Recommendation
Use **Supabase Auth** (GoTrue) instead of rolling your own `users` table if possible. It handles:
*   Email confirmations.
*   Password resets.
*   Secure session management.
*   Social Login (Google/GitHub).

---

## 3. Authorization & Row Level Security (RLS)

This is the most critical part for security.

### Application Level (Python)
In `class_service.py`, filter queries based on the logged-in user:
```python
# Old
supabase.table("classroom_settings").select("*")

# New
user_id = st.session_state.user.id
supabase.table("class_owners").select("class_name").eq("user_id", user_id)
```

### Database Level (Supabase RLS)
Enable RLS on your tables so even if the Python code has a bug, the database prevents unauthorized access.
*   **Policy**: `Users can only select rows where user_id = auth.uid()`

---

## 4. UI/UX Changes

### Admin Dashboard
*   **Super Admin View**: Sees ALL classes and can manage other Admins.
*   **Teacher View**: Sees only classes assigned to them.
*   **Profile Page**: Add ability to change password.

### Student Portal
*   **Sign Up/Login**: Students should also account if you want tracking across devices.
*   **My Classes**: Instead of typing a Class Code every time, students "Join" a class once and it appears in their dashboard permanently.

---

## 5. Summary of Next Steps

1.  **Migrate Auth**: Switch to Supabase Built-in Auth.
2.  **Create Tables**: Link Classes to Users (`owner_id`).
3.  **Update Services**: Rewrite `class_service.get_all_classes()` to accept a `user_id`.
4.  **Update UI**: Remove the simple login form and replace with a proper Auth Widget.

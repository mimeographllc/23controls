# SecureAuth API - Postman Quick Reference

## 🚀 Quick Start

1. **Import** → Select `SecureAuth_API.postman_collection.json`
2. **Run** "Login" request → Tokens auto-saved
3. **Test** any authenticated endpoint

## 🔑 Default Credentials

```
Email: admin@example.com
Password: Admin123!
```

## 📍 Base URL

```
http://localhost:8000
```

## 🎯 Essential Endpoints

### Authentication
```
POST   /auth/signup              Register new user
POST   /auth/login               Get JWT tokens
GET    /auth/me                  Get current user info
POST   /auth/refresh             Refresh access token
POST   /auth/logout              Logout
```

### MFA
```
POST   /auth/mfa/setup           Setup MFA (get QR code)
POST   /auth/mfa/verify          Verify TOTP token
```

### User Profile
```
GET    /users/me                 Get my profile
PUT    /users/me                 Update my profile
POST   /users/me/change-password Change password
```

### Admin - Users
```
GET    /users                    List all users
GET    /users/{id}               Get user by ID
PUT    /users/{id}               Update user
DELETE /users/{id}               Delete user
```

### Admin - Roles
```
POST   /users/roles              Create role
GET    /users/roles              List roles
POST   /users/{uid}/roles/{rid}  Assign role to user
DELETE /users/{uid}/roles/{rid}  Remove role from user
```

### Admin - Permissions
```
POST   /users/permissions        Create permission
GET    /users/permissions        List permissions
POST   /users/roles/{rid}/permissions/{pid}    Assign to role
DELETE /users/roles/{rid}/permissions/{pid}    Remove from role
POST   /users/{uid}/permissions/{pid}          Assign to user
DELETE /users/{uid}/permissions/{pid}          Remove from user
```

### Health
```
GET    /health                   Health check
GET    /docs                     Swagger UI
```

## 📋 Common Request Bodies

### Sign Up
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "security_type": "PASSWORD",
  "password": "SecurePass123!"
}
```

### Login
```json
{
  "email": "admin@example.com",
  "password": "Admin123!"
}
```

### Refresh Token
```json
{
  "refresh_token": "{{refresh_token}}"
}
```

### Update Profile
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

### Change Password
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

### Verify MFA
```json
{
  "token": "123456"
}
```

### Create Role
```json
{
  "name": "Editor",
  "description": "Can edit content",
  "tier_required": "FREE"
}
```

### Create Permission
```json
{
  "name": "edit_posts",
  "module": "posts",
  "action": "edit",
  "description": "Edit posts permission",
  "tier_required": "FREE"
}
```

## 🔐 Security Types

| Type | Value |
|------|-------|
| Password | `PASSWORD` |
| MFA TOTP | `MFA_TOTP` |
| MFA Passkey | `MFA_PASSKEY` |

## 👥 User Tiers

| Tier | Value |
|------|-------|
| Free | `FREE` |
| Basic | `BASIC` |
| Premium | `PREMIUM` |
| Enterprise | `ENTERPRISE` |

## 📊 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created |
| 204 | No Content - Deleted |
| 400 | Bad Request |
| 401 | Unauthorized - Login required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 500 | Internal Server Error |
| 501 | Not Implemented - Feature not configured |

## 🔄 Automatic Features

✅ **Login** → Saves `access_token` and `refresh_token`
✅ **Sign Up** → Saves `user_id`
✅ **Refresh** → Updates `access_token`
✅ **Authorization** → Auto-included in authenticated requests

## 🎯 Testing Workflow

1. **Login** → Get tokens
2. **Get My Profile** → Verify authentication
3. **Update My Profile** → Test modifications
4. **List Roles** → View available roles
5. **List Permissions** → View permissions

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Run "Login" request again |
| 403 Forbidden | Check user roles/permissions |
| Connection refused | Start backend: `docker-compose up -d` |
| Invalid JSON | Check Body → raw → JSON selected |

## 💡 Pro Tips

- **Collection Variables:** Click collection name → Variables tab
- **Test Scripts:** Auto-save tokens after login
- **Environments:** Create Dev/Staging/Prod environments
- **Collection Runner:** Run entire folders at once
- **Console:** View full request/response logs (bottom left)

## 📚 Documentation

- **This Collection:** 30+ endpoints with examples
- **Swagger UI:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

**Need Help?** Check `POSTMAN_COLLECTION_GUIDE.md` for detailed documentation.

# Quick Fix Scripts - SynthetIQ Signals CDP

This directory contains automated fix scripts for common issues.

## Available Fix Scripts

### 1. PostgreSQL Fix (`fix-postgres.*`)

**Fixes:** Logical replication launcher error

**Usage:**
```bash
# Unix/Mac/Linux
./fix-postgres.sh

# Windows
fix-postgres.bat
```

**What it does:**
1. Stops all containers
2. Removes PostgreSQL volume
3. Restarts with fixed configuration
4. Verifies no errors

**When to use:**
- First time setup
- PostgreSQL showing replication errors
- After updating docker-compose.yml

---

### 2. Frontend Fix (`fix-frontend.*`)

**Fixes:** Tailwind CSS plugin errors, build failures

**Usage:**
```bash
# Unix/Mac/Linux
./fix-frontend.sh

# Windows
fix-frontend.bat
```

**What it does:**
1. Stops frontend container
2. Rebuilds with no cache (installs dependencies)
3. Starts frontend
4. Shows recent logs

**When to use:**
- "Cannot find module @tailwindcss/forms" error
- Frontend won't build
- After updating package.json
- Missing dependencies

---

## Complete Reset

If all else fails, use this nuclear option:

```bash
# Stop everything
docker-compose down -v

# Remove all Docker resources
docker system prune -a --volumes

# Rebuild from scratch
docker-compose up -d --build
```

---

## Manual Fixes

### PostgreSQL Issue
```bash
docker-compose down -v
docker-compose up -d postgres
docker-compose logs postgres
```

### Frontend Issue
```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
docker-compose logs frontend
```

### Backend Issue
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
docker-compose logs backend
```

---

## Verification Commands

After running any fix script:

```bash
# Check all services
docker-compose ps

# Test backend
curl http://localhost:8000/health

# Test frontend (in browser)
open http://localhost:5173

# Check for errors
docker-compose logs postgres | grep -i error
docker-compose logs frontend | grep -i error
docker-compose logs backend | grep -i error
```

---

## Troubleshooting the Fix Scripts

### Script won't run (Unix/Mac)

**Error:** `Permission denied`

**Fix:**
```bash
chmod +x fix-postgres.sh
chmod +x fix-frontend.sh
./fix-postgres.sh
```

### Script not found (Windows)

**Error:** `'fix-postgres.bat' is not recognized`

**Fix:**
```cmd
cd synthetiq-signals-cdp
dir *.bat
fix-postgres.bat
```

### Docker commands fail

**Error:** `docker: command not found`

**Fix:**
1. Make sure Docker Desktop is running
2. Verify Docker is installed: `docker --version`
3. Restart Docker Desktop

---

## When to Use Which Script

| Issue | Script | Alternative |
|-------|--------|-------------|
| PostgreSQL errors | `fix-postgres.sh` | Rebuild from scratch |
| Frontend won't build | `fix-frontend.sh` | `docker-compose build --no-cache frontend` |
| Backend won't start | Rebuild backend | `docker-compose restart backend` |
| Everything broken | Complete reset | Download fresh copy |
| Celery won't start | Use profiles | `docker-compose --profile celery up -d` |

---

## Getting Help

If fix scripts don't work:

1. **Check Docker:**
   ```bash
   docker --version
   docker-compose --version
   docker system info
   ```

2. **Check logs:**
   ```bash
   docker-compose logs [service-name]
   ```

3. **Read docs:**
   - `TROUBLESHOOTING.md` - Comprehensive guide
   - `README.md` - Setup and usage
   - `FIXES_APPLIED.md` - What's been fixed

4. **Start fresh:**
   - Download latest: `synthetiq-signals-cdp-phase1-FINAL.tar.gz`
   - Extract and run: `docker-compose up -d --build`

---

## Best Practices

✅ **DO:**
- Run fix scripts when you encounter errors
- Check logs after running scripts
- Verify services are healthy: `docker-compose ps`
- Keep Docker Desktop updated

❌ **DON'T:**
- Run multiple fix scripts simultaneously
- Modify scripts without backing up
- Run scripts on production (use proper deployment)
- Ignore error messages in logs

---

**Need more help?** See `TROUBLESHOOTING.md` for detailed solutions to all known issues.

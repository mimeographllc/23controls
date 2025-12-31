# Celery Quick Reference - SynthetIQ Signals CDP

## What is Celery?

Celery is a distributed task queue that allows you to run tasks asynchronously in the background. In SynthetIQ Signals CDP, we use Celery for:

- **Email sending** (welcome emails, order confirmations, license delivery)
- **Model processing** (ECR pushes, security scanning, thumbnail generation)
- **Report generation** (daily/monthly reports, data exports)
- **Scheduled tasks** (cleanup, analytics updates)

## Starting Celery

### Basic Start (Core Services Only)
```bash
docker-compose up -d --build
```
This starts: postgres, redis, backend, frontend (NO Celery)

### With Celery Workers
```bash
docker-compose --profile celery up -d --build
```
This adds: celery-worker, celery-beat

### Everything
```bash
docker-compose --profile celery --profile tools up -d --build
```
This adds: celery-worker, celery-beat, pgadmin, mailhog

## Celery Services

### celery-worker
- Processes async tasks
- Handles emails, model uploads, data exports
- Can scale horizontally (multiple workers)

### celery-beat
- Scheduler for periodic tasks
- Runs daily reports, cleanup tasks
- Only need one instance

## Monitoring Celery

### View Worker Logs
```bash
docker-compose logs -f celery-worker
```

### View Beat Logs
```bash
docker-compose logs -f celery-beat
```

### Check Worker Status
```bash
docker-compose exec celery-worker celery -A app.celery_app inspect active
```

### Check Scheduled Tasks
```bash
docker-compose exec celery-beat celery -A app.celery_app inspect scheduled
```

### Flower (Web UI)
Start Flower to monitor tasks via web interface:
```bash
docker-compose exec celery-worker celery -A app.celery_app flower --port=5555
```
Then open: http://localhost:5555

## Available Tasks

### Email Tasks (`app.tasks.email`)
- `send_welcome_email` - Send welcome email to new users
- `send_order_confirmation` - Send order confirmation
- `send_license_email` - Send license key to customer
- `cleanup_expired_sessions` - Clean expired sessions (runs hourly)

### Model Tasks (`app.tasks.models`)
- `push_to_ecr` - Push Docker image to AWS ECR
- `scan_model_security` - Security vulnerability scanning
- `generate_model_thumbnail` - Create image thumbnails
- `update_model_analytics` - Update view/download counts

### Report Tasks (`app.tasks.reports`)
- `generate_daily_report` - Daily analytics (runs midnight UTC)
- `generate_monthly_report` - Monthly summary
- `export_customer_data` - GDPR data export
- `generate_invoice_pdf` - Generate PDF invoices

## Sending Tasks from Code

### From FastAPI Endpoint
```python
from app.tasks.email import send_welcome_email

# In your endpoint
@app.post("/users/register")
async def register_user(user_data: UserCreate):
    # Create user...
    
    # Send welcome email asynchronously
    send_welcome_email.delay(user.email, user.name)
    
    return {"message": "User created"}
```

### Using send_task
```python
from app.celery_app import send_task

# Send any task by name
send_task(
    "app.tasks.email.send_welcome_email",
    "user@example.com",
    "John Doe"
)
```

## Scheduled Tasks (Celery Beat)

Scheduled tasks are configured in `backend/app/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    "cleanup-expired-sessions": {
        "task": "app.tasks.email.cleanup_expired_sessions",
        "schedule": crontab(minute=0),  # Every hour
    },
    "generate-daily-reports": {
        "task": "app.tasks.reports.generate_daily_report",
        "schedule": crontab(hour=0, minute=0),  # Midnight UTC
    },
}
```

## Task Queues

Tasks can be routed to specific queues:

- **emails** - Email sending tasks (high priority)
- **reports** - Report generation (low priority)
- **models** - Model processing (medium priority)

This is configured in `celery_app.py`:
```python
celery_app.conf.task_routes = {
    "app.tasks.email.*": {"queue": "emails"},
    "app.tasks.reports.*": {"queue": "reports"},
    "app.tasks.models.*": {"queue": "models"},
}
```

## Development Tips

### Do I Need Celery for Development?

**No!** For Phase 1-2 basic development, you can work without Celery:
```bash
docker-compose up -d --build  # Core services only
```

**Yes, when you need:**
- Email sending functionality
- Background processing (ECR pushes, reports)
- Testing scheduled tasks

### Testing Tasks Manually

```bash
# Start Python shell in backend container
docker-compose exec backend python

# Import and run a task
>>> from app.tasks.email import send_welcome_email
>>> result = send_welcome_email.delay("test@example.com", "Test User")
>>> result.get()  # Wait for result
```

### Debugging Tasks

1. **View task execution in logs:**
   ```bash
   docker-compose logs -f celery-worker
   ```

2. **Check task status:**
   ```python
   from app.tasks.email import send_welcome_email
   result = send_welcome_email.delay("test@example.com", "Test")
   result.ready()  # True if complete
   result.successful()  # True if no errors
   result.get()  # Get result (blocks until complete)
   ```

3. **Task failed? Check exception:**
   ```python
   try:
       result.get()
   except Exception as e:
       print(f"Task failed: {e}")
   ```

## Common Issues

### "Unable to load celery application"

**Fix:** Make sure `app/celery_app.py` exists and `app/tasks/` directory has all required files.

### Worker not picking up tasks

**Fix:** 
1. Check Redis is running: `docker-compose ps redis`
2. Restart worker: `docker-compose restart celery-worker`
3. Check broker URL in .env

### Tasks timing out

**Fix:** Increase time limits in `celery_app.py`:
```python
task_time_limit = 60 * 60  # 60 minutes
task_soft_time_limit = 55 * 60  # 55 minutes
```

## Production Considerations

### Scaling Workers

Run multiple workers for better throughput:
```bash
docker-compose up -d --scale celery-worker=4
```

### Monitoring in Production

Use:
- **Flower** - Web UI for monitoring
- **Sentry** - Error tracking
- **Prometheus** - Metrics collection

### Retry Logic

Tasks should have retry logic for transient failures:
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def send_email(self, email, content):
    try:
        # Send email...
    except Exception as exc:
        raise self.retry(exc=exc)
```

## Further Reading

- **Celery Docs:** https://docs.celeryq.dev/
- **Best Practices:** https://docs.celeryq.dev/en/stable/userguide/tasks.html#tips-and-best-practices
- **Monitoring:** https://docs.celeryq.dev/en/stable/userguide/monitoring.html

---

**For Phase 1:** Celery is optional - focus on core functionality  
**For Phase 4+:** Celery becomes essential for developer portal and email features

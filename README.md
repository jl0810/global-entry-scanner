# Global Entry Appointment Scanner

Monitors Charlotte-Douglas Airport (CLT) for Global Entry appointment cancellations and sends instant email alerts.

## Features

- 🔍 Checks CLT every 60 seconds
- 📧 Emails both jefflawson@gmail.com and kate.r.lawson@gmail.com
- 🎨 Beautiful HTML emails with booking instructions
- 🔄 Auto-restarts if it crashes
- 🌐 Uses browser headers to avoid API blocks
- 📧 Uses Unsend email service (same as Fakesharp)

## Files

- `scanner.py` - Main scanner script
- `docker-compose.yml` - Docker Compose configuration (self-contained)
- `Dockerfile` - Docker image definition
- `.env` - Environment variables

## Deployment

Deployed on Hetzner via Dokploy at:
- Path: `/etc/dokploy/compose/main-globalentryscanner-tljinv/code/`
- Container: `global-entry-scanner`
- Network: `dokploy-network`

## Monitoring

```bash
ssh hetzner
docker logs -f global-entry-scanner
```

## How it works

1. Every 60 seconds, checks DHS API for CLT appointments
2. Uses browser headers to avoid being blocked
3. When slots found, sends beautiful HTML email to both recipients
4. Email includes first available slot, all times, and booking instructions

## Environment Variables

- `USESEND_API_KEY` - Email API key (shared with Fakesharp)
- `USESEND_HOST` - Email service URL (http://usesend:3000)
- `NOTIFICATION_FROM` - Sender email
- `PYTHONUNBUFFERED` - Fix output buffering

## Notes

- Scanner runs 24/7 automatically
- Slots typically disappear within 2-5 minutes
- CLT currently has no available appointments
- Will alert instantly when one appears

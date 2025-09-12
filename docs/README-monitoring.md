# Resource Monitoring & Auto-Scaling Guidance

## Real-Time Monitoring
- The app now includes a resource monitor panel (CPU, memory, Celery queue length) for admins.
- See `ui/components.py` and use `admin_resource_panel()` in your Streamlit UI to display stats.
- Alerts are shown for high resource usage.

## Auto-Scaling Celery Workers
- **Manual scaling:**
  - Start more workers: `celery -A celeryconfig.celery_app worker --loglevel=info -c 4` (for 4 concurrent workers)
  - Use a process manager (supervisord, systemd, pm2, etc.) to keep workers running and auto-restart on failure.
- **Cloud/Container scaling:**
  - On Kubernetes: use Horizontal Pod Autoscaler (HPA) to scale Celery worker pods based on CPU/memory/queue length.
  - On AWS ECS/Fargate: use Service Auto Scaling.
  - On Azure: use VM Scale Sets or Container Apps autoscaling.
- **Queue-based scaling:**
  - Monitor Redis queue length (`celery_queue_length` metric). If queue grows, add more workers.

## Alerts & Logging
- High resource usage triggers UI alerts.
- All resource stats can be logged by running `resource_monitor.py` as a background process.
- For production, integrate with Prometheus/Grafana or cloud-native monitoring for advanced dashboards and alerting.

## Example: Running the Monitor
```sh
python resource_monitor.py
```

## Best Practices
- Always monitor queue length and resource usage in production.
- Set up auto-scaling for Celery workers if expecting variable/high load.
- Use robust logging and alerting for reliability.

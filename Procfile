web: gunicorn --pythonpath exam_app/ exam_app:app --debug --log-file -
worker: celery -A exam_app.async_tasks.celery_app worker --loglevel=info

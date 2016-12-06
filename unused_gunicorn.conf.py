import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
backlog = 2048
worker_class = 'gevent'
daemon = True
debug = True
loglevel = 'debug'
accesslog = './gunicorn_access.log'
errorlog = './gunicorn_error.log'
max_requests = 1000
timeout = 300
graceful_timeout = 300


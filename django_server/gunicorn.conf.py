bind = "0.0.0.0:8000"
workers = 3
timeout = 120

accesslog = '/usr/local/bin/gunicorn/access.log'
errorlog = '/usr/local/bin/gunicorn/error.log'
loglevel = 'info'
capture_output = True
# Run gunicorn
venv/bin/gunicorn -k gevent -w 1 -b 127.0.0.1:4999 --log-file gunicorn.log app.wsgi
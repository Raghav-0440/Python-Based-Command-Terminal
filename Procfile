web: python -m gunicorn --worker-class eventlet -w 1 --timeout 120 --graceful-timeout 30 --keep-alive 5 --bind 0.0.0.0:$PORT web_terminal:app

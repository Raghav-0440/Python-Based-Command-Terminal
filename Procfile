web: python -m gunicorn --worker-class gthread --threads 4 -w 1 --timeout 300 --graceful-timeout 60 --keep-alive 10 --bind 0.0.0.0:$PORT web_terminal:app

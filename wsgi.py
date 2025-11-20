# wsgi.py
# Faili hili linaanzisha programu ya Flask ili Gunicorn iweze kuipata kwa urahisi.
from app import app as application

if __name__ == "__main__":
    # Tumia jina la 'application' kama Gunicorn inavyotaka
    application.run()

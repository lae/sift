#web_0: gunicorn --worker-class="egg:meinheld#gunicorn_worker" -b unix:/tmp/siftracker.jp.0.socket sift:sift --error-logfile - --access-logfile log/access.log --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Real-IP}i)s"' -w 3
web_0: gunicorn -b unix:/tmp/siftracker.en.0.socket sift:sift --error-logfile - --access-logfile log/access.log --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Real-IP}i)s"' -w 3
web_1: gunicorn -b unix:/tmp/siftracker.en.1.socket sift:sift --error-logfile - --access-logfile log/access.log --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Real-IP}i)s"' -w 3
web_2: gunicorn -b unix:/tmp/siftracker.en.2.socket sift:sift --error-logfile - --access-logfile log/access.log --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%({X-Real-IP}i)s"' -w 3

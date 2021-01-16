env/bin/coverage run tests/test_parser.py
env/bin/coverage run -a tests/test_changers.py
env/bin/coverage html
firefox htmlcov/index.html

test:
	@flake8 . --exclude fabfile.py --ignore=E241,E501,F403
	@flake8 fabfile.py --ignore=E241,E501,F401

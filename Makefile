test:
	@flake8 . --exclude fabfile.py --ignore=E241,E501, \
	  F403 # FIXME: Fix these errors and stop ignoring them
	@flake8 fabfile.py --ignore=E241,E501,F401

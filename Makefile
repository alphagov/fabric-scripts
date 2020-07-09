test:
	@flake8 . --exclude fabfile.py --ignore=E241,E501,E302
	@flake8 fabfile.py --ignore=E241,E501,F401,E302
	@fab -l

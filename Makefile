test:
	@flake8 . --exclude fabfile.py --ignore=E241,E501
	@flake8 fabfile.py --ignore=E241,E501,F401
	@fab -l

setup:
	pip install pipenv
	pip install aws-profile
	pip install awscli
	pipenv install

collect-sandbox:
	sh -c 'AWS_PROFILE=webops-sandbox aws-profile pipenv run python cloudmapper.py collect --account webops-sandbox --config config.json --profile webops-sandbox'

collect-integration:
	sh -c 'AWS_PROFILE=webops-integration aws-profile pipenv run python cloudmapper.py collect --account webops-integration --config config.json --profile webops-integration'

collect-qa:
	sh -c 'AWS_PROFILE=webops-qa aws-profile pipenv run python cloudmapper.py collect --account webops-qa --config config.json --profile webops-qa'

collect-staging:
	sh -c 'AWS_PROFILE=webops-staging aws-profile pipenv run python cloudmapper.py collect --account webops-staging --config config.json --profile webops-staging'

collect-externaltest:
	sh -c 'AWS_PROFILE=webops-externaltest aws-profile pipenv run python cloudmapper.py collect --account webops-externaltest --config config.json --profile webops-externaltest'

collect-production:
	sh -c 'AWS_PROFILE=webops-production aws-profile pipenv run python cloudmapper.py collect --account webops-production --config config.json --profile webops-production'

collect-management:
	sh -c 'AWS_PROFILE=webops-management aws-profile pipenv run python cloudmapper.py collect --account webops-management --config config.json --profile webops-managerment'

webserver:
	pipenv run python cloudmapper.py webserver --public --port 8000

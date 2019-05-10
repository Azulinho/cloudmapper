build:
	rm -f src/web/data.json
	docker build -t azulinho/cloudmapper .

shell:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper bash

collect-sandbox:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-sandbox

collect-integration:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-integration

collect-qa:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-qa

collect-staging:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-staging

collect-externaltest:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-externaltest

collect-production:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-production

collect-management:
	docker run -it -v $$PWD/config.json:/app/config.json -v ~/.aws:/root/.aws -v $$PWD/data:/app/account-data azulinho/cloudmapper make collect-management

prepare:
	rm -f tmp/data.json
	touch tmp/data.json
	docker run -it \
		-v $$PWD/config.json:/app/config.json  \
		-v ~/.aws:/root/.aws \
		-v $$PWD/data:/app/account-data \
		-v $$PWD/tmp/data.json:/app/web/data.json \
		azulinho/cloudmapper \
		pipenv run python cloudmapper.py prepare --config config.json \
		--account $$AWS_PROFILE \
		--regions eu-west-2 \
		--internal-edges \
		--no-inter-rds-edges \
		--no-azs \
		--filter-ec2-by-name $$SEARCHWORD \
		--filter-elb-by-name $$SEARCHWORD \
		--filter-rds-by-name $$SEARCHWORD

webserver:
	docker run -p 8000:8000 -it \
		-v $$PWD/config.json:/app/config.json \
		-v $$PWD/data:/app/account-data \
		-v $$PWD/tmp/data.json:/app/web/data.json \
		azulinho/cloudmapper \
		make webserver

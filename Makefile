.PHONY: init plan apply destroy fmt validate ssh kubeconfig build run deploy-all destroy-all

init:
	cd terraform && terraform init

plan:
	cd terraform && terraform plan

apply:
	cd terraform && terraform apply

destroy:
	cd terraform && terraform destroy

fmt:
	cd terraform && terraform fmt -recursive

validate:
	cd terraform && terraform validate

ssh:
	cd terraform && ssh -i ~/infra-ai-platform-key.pem ubuntu@$$(terraform output -raw node_public_ip)

kubeconfig:
	cd terraform && scp -i ~/infra-ai-platform-key.pem ubuntu@$$(terraform output -raw node_public_ip):/etc/rancher/k3s/k3s.yaml ./kubeconfig.yaml

build:
	docker build -t inference-api:local app/

run: build
	docker run -p 8000:8000 inference-api:local

# Full-stack automation — see deploy.sh / destroy.sh for what each step does.
deploy-all:
	./deploy.sh

deploy-with-monitoring:
	WITH_MONITORING=1 ./deploy.sh

destroy-all:
	./destroy.sh

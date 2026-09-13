.PHONY: init plan apply destroy fmt validate ssh kubeconfig build run

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
	cd terraform && ssh ubuntu@$$(terraform output -raw node_public_ip)

kubeconfig:
	cd terraform && scp ubuntu@$$(terraform output -raw node_public_ip):/etc/rancher/k3s/k3s.yaml ./kubeconfig.yaml

build:
	docker build -t inference-api:local app/

run: build
	docker run -p 8000:8000 inference-api:local

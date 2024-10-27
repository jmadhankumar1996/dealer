.DEFAULT_GOAL := help

docs: ## Generates Terraform docs using cytopia/terraform-docs container and outputs them to README.md
	docker run --rm \
	  -v $(PWD)/terraform:/data \
	  -e DELIM_START='<!-- TFDOC_START -->' \
	  -e DELIM_CLOSE='<!-- TFDOC_END -->' \
	  cytopia/terraform-docs \
	  terraform-docs-replace-012 md README.md

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' ./Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

.PHONY: docs
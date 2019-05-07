#################### Build Open edX Docker image based on Alpine Linux
.DEFAULT_GOAL := help

openedx-image: ## Build Open edX docker image
	openedx-build/build.sh

BASE_DEPS = openedx-build/build_base.sh \
	openedx-build/container_scripts/install_run_dependencies.sh
openedx-image-base: $(BASE_DEPS) ## Build base Alpine image for buildah
	$(eval SHA := $(shell sha256sum $$(echo "$(BASE_DEPS)") | sha256sum | cut -b 1-12))
	openedx-build/build_base.sh
	echo $(SHA) > openedx-image-base
	sudo buildah tag localhost/openedx-base localhost/openedx-base:$(SHA)

BUILDWHEELS_DEPS = openedx-build/build_buildwheels.sh \
	openedx-build/container_scripts/install_build_dependencies.sh
openedx-image-buildwheels: openedx-image-base $(BUILDWHEELS_DEPS) ## Build "Wheel builder" Alpine image for buildah
	$(eval SHA := $(shell sha256sum $$(echo "$(BUILDWHEELS_DEPS)") | sha256sum | cut -b 1-12))
	openedx-build/build_buildwheels.sh
	echo $(SHA) > openedx-image-buildwheels
	sudo buildah tag localhost/openedx-buildwheels localhost/openedx-buildwheels:$(SHA)

WHEELS_DEPS = openedx-build/build_wheels.sh \
	edx-platform/requirements/edx/development.txt \
	edx-platform/requirements/edx/base.txt
openedx-image-wheels: openedx-image-buildwheels $(WHEELS_DEPS) ## Build "Wheel builder" Alpine image for buildah
	$(eval SHA := $(shell sha256sum $$(echo "$(WHEELS_DEPS)") | sha256sum | cut -b 1-12))
	openedx-build/build_wheels.sh
	echo $(SHA) > openedx-image-wheels
	sudo buildah tag localhost/openedx-wheels localhost/openedx-wheels:$(SHA)

##################### Information
ESCAPE = 
help: ## Print this help
	@grep -E '^([a-zA-Z_-]+:.*?## .*|######* .+)$$' Makefile \
		| sed 's/######* \(.*\)/\n               $(ESCAPE)[1;31m\1$(ESCAPE)[0m/g' \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-30s\033[0m %s\n", $$1, $$2}'

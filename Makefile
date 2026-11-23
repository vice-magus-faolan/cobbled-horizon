PACKWIZ ?= packwiz

PACK_VERSION := $(shell python3 scripts/release_metadata.py --field version)
MINECRAFT_VERSION := $(shell python3 scripts/release_metadata.py --field minecraft)
PACK_BASENAME := cobbled-horizon-$(PACK_VERSION)
MRPACK := dist/$(PACK_BASENAME).mrpack
SERVER_DIR ?= build/server
SERVER_ZIP := build/$(PACK_BASENAME)-server.zip
# Only an explicitly supplied plan is a frozen caller contract.
DEFAULT_RELEASE_PLAN := $(if $(filter undefined,$(origin RELEASE_PLAN)),true,false)
RELEASE_PLAN ?= release-plan.json
RELEASE_TAG ?= v$(PACK_VERSION)

.PHONY: validate test refresh check-release check-metadata export release materialize server-zip clean

validate:
	python3 scripts/release_metadata.py
	python3 scripts/check_pack.py

test:
	python3 -m unittest discover -s tests -v

refresh:
	$(PACKWIZ) refresh --build

# Original-host references, approved config and finite notices contain no mod binaries.
export: refresh validate
	mkdir -p dist
	$(PACKWIZ) modrinth export -o $(MRPACK)
	python3 scripts/distribution.py metadata-notices --archive $(MRPACK)
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	cd dist && sha256sum $(PACK_BASENAME).mrpack > $(PACK_BASENAME).mrpack.sha256

check-metadata:
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	cd dist && sha256sum --check $(PACK_BASENAME).mrpack.sha256

release: export
	@if [ "$(DEFAULT_RELEASE_PLAN)" = true ]; then python3 scripts/distribution.py release-plan --tag "$(RELEASE_TAG)" > "$(RELEASE_PLAN)"; fi
	$(MAKE) check-release RELEASE_PLAN="$(RELEASE_PLAN)" RELEASE_TAG="$(RELEASE_TAG)"

# Consume the same exact plan as artifact transfer and draft comparison.
check-release:
	@if [ "$(DEFAULT_RELEASE_PLAN)" = true ]; then python3 scripts/distribution.py release-plan --tag "$(RELEASE_TAG)" > "$(RELEASE_PLAN)"; fi
	python3 scripts/distribution.py verify-release --plan "$(RELEASE_PLAN)" --tag "$(RELEASE_TAG)"
	$(MAKE) check-metadata

materialize: export
	mkdir -p $(dir $(SERVER_DIR))
	python3 scripts/server_folder.py materialize $(MRPACK) $(SERVER_DIR)

# Owner-run installation only: never a release, Actions artifact or cache input.
server-zip: materialize
	mkdir -p build
	python3 scripts/server_folder.py zip "$(SERVER_DIR)" "$(SERVER_ZIP)"

clean:
	rm -rf build dist

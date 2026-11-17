PACKWIZ ?= packwiz

# Public is the safe default; private preparation never grants upload authority.
CHANNEL ?= github
PACK_VERSION := $(shell python3 scripts/release_metadata.py --field version)
MINECRAFT_VERSION := $(shell python3 scripts/release_metadata.py --field minecraft)
PACK_BASENAME := cobbled-horizon-$(PACK_VERSION)
MRPACK := dist/$(PACK_BASENAME).mrpack
CURSEFORGE := dist/$(PACK_BASENAME).zip
SERVER_DIR ?= build/server
# Only an explicitly supplied plan is a frozen caller contract.
DEFAULT_RELEASE_PLAN := $(if $(filter undefined,$(origin RELEASE_PLAN)),true,false)
RELEASE_PLAN ?= release-plan.json
RELEASE_TAG ?= v$(PACK_VERSION)

.PHONY: validate test refresh distribution-check public-check check-release check-upload check-metadata export export-curseforge release materialize clean

validate:
	python3 scripts/permission_seed.py --check
	python3 scripts/release_metadata.py
	python3 scripts/check_pack.py

test:
	python3 -m unittest discover -s tests -v

refresh:
	python3 scripts/permission_seed.py
	$(PACKWIZ) refresh --build

distribution-check:
	python3 scripts/distribution.py check --channel $(CHANNEL)

# Upload boundaries always check public rights, irrespective of build flags.
public-check:
	python3 scripts/distribution.py check --channel github

# Metadata references, approved config and finite notices contain no mod binaries.
export: refresh validate
	mkdir -p dist
	$(PACKWIZ) modrinth export -o $(MRPACK)
	python3 scripts/distribution.py metadata-notices --archive $(MRPACK)
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	cd dist && sha256sum $(PACK_BASENAME).mrpack > $(PACK_BASENAME).mrpack.sha256

check-metadata:
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	cd dist && sha256sum --check $(PACK_BASENAME).mrpack.sha256


export-curseforge: refresh validate distribution-check
	mkdir -p dist
	$(PACKWIZ) curseforge export --side server -o $(CURSEFORGE)
	python3 scripts/distribution.py notices --channel $(CHANNEL) --archive $(CURSEFORGE)
	python3 scripts/validate_curseforge.py $(CURSEFORGE) --channel $(CHANNEL)

# Run exports sequentially: both packwiz commands refresh the source index.
release: export
	@if [ "$(DEFAULT_RELEASE_PLAN)" = true ]; then python3 scripts/distribution.py release-plan --tag "$(RELEASE_TAG)" > "$(RELEASE_PLAN)"; fi
	$(MAKE) export-curseforge CHANNEL=$(CHANNEL)
	rm -f $(MRPACK).sha256
	cd dist && sha256sum $(PACK_BASENAME).mrpack $(PACK_BASENAME).zip > $(PACK_BASENAME).sha256
	$(MAKE) check-release RELEASE_PLAN="$(RELEASE_PLAN)" RELEASE_TAG="$(RELEASE_TAG)"

# Consume the same plan as artifact transfer and draft comparison. A validator
# failure is fatal, never a reason to downgrade a full release to metadata.
check-release:
	@if [ "$(DEFAULT_RELEASE_PLAN)" = true ]; then python3 scripts/distribution.py release-plan --tag "$(RELEASE_TAG)" > "$(RELEASE_PLAN)"; fi
	python3 scripts/distribution.py verify-release --plan "$(RELEASE_PLAN)" --tag "$(RELEASE_TAG)"
	@mode=$$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["mode"])' "$(RELEASE_PLAN)"); \
	case "$$mode" in \
		full) $(MAKE) check-upload ;; \
		metadata) $(MAKE) check-metadata ;; \
		*) echo 'Invalid release mode' >&2; exit 1 ;; \
	esac

check-upload: public-check
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	python3 scripts/validate_curseforge.py $(CURSEFORGE) --channel github

	cd dist && sha256sum --check $(PACK_BASENAME).sha256

materialize: export
	mkdir -p $(dir $(SERVER_DIR))
	python3 scripts/server_folder.py materialize $(MRPACK) $(SERVER_DIR)

clean:
	rm -rf build dist

PACKWIZ ?= packwiz
MRPACK_INSTALL ?= mrpack-install
# Public is the safe default; private preparation never grants upload authority.
CHANNEL ?= github
PACK_VERSION := $(shell python3 scripts/release_metadata.py --field version)
MINECRAFT_VERSION := $(shell python3 scripts/release_metadata.py --field minecraft)
PACK_BASENAME := cobbled-horizon-$(PACK_VERSION)
MRPACK := dist/$(PACK_BASENAME).mrpack
CURSEFORGE := dist/$(PACK_BASENAME).zip
SERVER := dist/$(PACK_BASENAME)-server.zip

.PHONY: validate test refresh distribution-check public-check check-upload export export-curseforge release materialize clean

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

export: refresh validate distribution-check
	mkdir -p dist
	$(PACKWIZ) modrinth export -o $(MRPACK)
	python3 scripts/distribution.py notices --channel $(CHANNEL) --archive $(MRPACK)
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)

export-curseforge: refresh validate distribution-check
	mkdir -p dist
	$(PACKWIZ) curseforge export --side server -o $(CURSEFORGE)
	python3 scripts/distribution.py notices --channel $(CHANNEL) --archive $(CURSEFORGE)
	python3 scripts/validate_curseforge.py $(CURSEFORGE) --channel $(CHANNEL)

# Run exports sequentially: both packwiz commands refresh the source index.
release: export
	$(MAKE) export-curseforge CHANNEL=$(CHANNEL)
	python3 scripts/server_pack.py --channel $(CHANNEL) build $(CURSEFORGE) $(SERVER) --mrpack $(MRPACK)
	cd dist && sha256sum $(PACK_BASENAME).mrpack $(PACK_BASENAME).zip $(PACK_BASENAME)-server.zip > $(PACK_BASENAME).sha256

check-upload: public-check
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)
	python3 scripts/validate_curseforge.py $(CURSEFORGE) --channel github
	python3 scripts/server_pack.py --channel github validate $(SERVER)
	cd dist && sha256sum --check $(PACK_BASENAME).sha256

materialize: export
	mkdir -p build
	$(MRPACK_INSTALL) $(MRPACK) --server-dir build/server

clean:
	rm -rf build dist

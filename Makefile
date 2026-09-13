PACKWIZ ?= packwiz
MRPACK_INSTALL ?= mrpack-install
PACK_VERSION := $(shell python3 scripts/release_metadata.py --field version)
MINECRAFT_VERSION := $(shell python3 scripts/release_metadata.py --field minecraft)
PACK_BASENAME := cobbled-horizon-$(PACK_VERSION)
MRPACK := dist/$(PACK_BASENAME).mrpack
CURSEFORGE := dist/$(PACK_BASENAME).zip

.PHONY: validate test refresh export export-curseforge release materialize clean

validate:
	python3 scripts/release_metadata.py
	python3 scripts/check_pack.py

test:
	python3 -m unittest discover -s tests -v

refresh:
	$(PACKWIZ) refresh --build

export: refresh validate
	mkdir -p dist
	$(PACKWIZ) modrinth export -o $(MRPACK)
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)

export-curseforge: refresh validate
	mkdir -p dist
	$(PACKWIZ) curseforge export --side server -o $(CURSEFORGE)
	python3 scripts/validate_curseforge.py $(CURSEFORGE)

# Run exports sequentially: both packwiz commands refresh the source index.
release: export
	$(MAKE) export-curseforge
	cd dist && sha256sum $(PACK_BASENAME).mrpack $(PACK_BASENAME).zip > $(PACK_BASENAME).sha256

materialize: export
	mkdir -p build
	$(MRPACK_INSTALL) $(MRPACK) --server-dir build/server

clean:
	rm -rf build dist

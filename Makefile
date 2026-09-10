PACKWIZ ?= packwiz
MRPACK_INSTALL ?= mrpack-install
PACK_VERSION := 0.1.0
MINECRAFT_VERSION := 26.2
MRPACK := dist/cobbled-horizon-$(PACK_VERSION)+mc$(MINECRAFT_VERSION).mrpack

.PHONY: validate test refresh export materialize clean

validate:
	python3 scripts/check_pack.py

test:
	python3 -m unittest discover -s tests -v

refresh:
	$(PACKWIZ) refresh --build

export: refresh validate
	mkdir -p dist
	$(PACKWIZ) modrinth export -o $(MRPACK)
	python3 scripts/validate_mrpack.py $(MRPACK) --minecraft $(MINECRAFT_VERSION)

materialize: export
	mkdir -p build
	$(MRPACK_INSTALL) $(MRPACK) --server-dir build/server

clean:
	rm -rf build dist

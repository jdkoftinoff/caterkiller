# Caterkiller -- Apple II reverse engineering project
#
#   make verify           assemble the three original levels and compare to the originals
#   make test             verify + the Python unit tests in tests/
#   make test-rust        cargo test for the terminal frontend
#   make test-web         node tests for the web frontend modules and the 6502 bundle
#   make caterkiller2026  assemble the 2026 reimplementation
#   make tui              build the Rust terminal frontend (needs cargo)
#   make disasm           regenerate raw disassemblies of the original binaries
#   make run-web          build caterkiller2026, serve it locally and open it in the browser
#   make deploy-web       package the web frontend + caterkiller2026.bin as a tarball
#   make all              verify + caterkiller2026 (Python only; no cargo needed)

TOOLS_DIR   = tools
ASM         = python3 $(TOOLS_DIR)/asm6502.py
DISASM      = python3 $(TOOLS_DIR)/disasm6502.py
FMT         = python3 $(TOOLS_DIR)/fmt6502.py

CK_SRC      = games/caterkiller/source
CK_ORIG     = games/caterkiller/original
CK_2026     = games/caterkiller/caterkiller2026
CK_BUILD    = build/caterkiller

CK_L1_BIN   = $(CK_BUILD)/level1_new.bin
CK_L2_BIN   = $(CK_BUILD)/level2_new.bin
CK_L3_BIN   = $(CK_BUILD)/level3_new.bin
CK_2026_BIN = $(CK_BUILD)/caterkiller2026.bin
CK_COLOR    = $(CK_BUILD)/color.bin

DISASM_DIR  = $(CK_BUILD)/disassembly
DISASM_OUT  = $(DISASM_DIR)/level1.asm $(DISASM_DIR)/level2.asm $(DISASM_DIR)/level3.asm

TUI_DIR     = frontends/tui
TUI_BIN     = $(TUI_DIR)/target/release/caterkiller-tui

WEB_DIR     = frontends/web
WEB_SHARED  = frontends/shared/cpu6502
WEB_DEPLOY  = $(CK_BUILD)/caterkiller2026-web.tar.gz

.PHONY: all clean verify test test-rust test-web caterkiller caterkiller2026 color tui disasm deploy-web run run-web

all: verify caterkiller2026

caterkiller: $(CK_L1_BIN) $(CK_L2_BIN) $(CK_L3_BIN)

$(CK_BUILD) $(DISASM_DIR):
	mkdir -p $@

$(CK_L1_BIN): $(CK_SRC)/level1.s $(TOOLS_DIR)/asm6502.py | $(CK_BUILD)
	$(ASM) $< $@

$(CK_L2_BIN): $(CK_SRC)/level2.s $(TOOLS_DIR)/asm6502.py | $(CK_BUILD)
	$(ASM) $< $@

$(CK_L3_BIN): $(CK_SRC)/level3.s $(TOOLS_DIR)/asm6502.py | $(CK_BUILD)
	$(ASM) $< $@

# Verify assembled binaries match the originals byte for byte
verify: caterkiller
	@for n in 1 2 3; do \
	  if cmp -s $(CK_BUILD)/level$${n}_new.bin $(CK_ORIG)/level$${n}.bin; \
	    then echo "  level$$n: MATCH"; \
	    else echo "  level$$n: MISMATCH"; fail=1; fi; \
	done; [ -z "$$fail" ]

test: verify
	python3 -m unittest discover -s tests -v

# Caterkiller 2026 reimplementation
caterkiller2026: $(CK_2026_BIN)

$(CK_2026_BIN): $(CK_2026)/caterkiller2026.s $(CK_2026)/level1.s $(CK_2026)/level2.s $(CK_2026)/level3.s $(CK_2026)/level4.s $(TOOLS_DIR)/asm6502.py | $(CK_BUILD)
	$(ASM) $(CK_2026)/caterkiller2026.s $@
	$(DISASM) $@ 0x6000 > $(CK_BUILD)/caterkiller2026_disasm.asm

color: $(CK_COLOR)

$(CK_COLOR): $(CK_2026)/color.s $(TOOLS_DIR)/asm6502.py | $(CK_BUILD)
	$(ASM) $< $@

# Raw disassembler output for the original binaries (annotated source lives in source/)
disasm: $(DISASM_OUT)

$(DISASM_DIR)/level1.asm: $(CK_ORIG)/level1.bin $(TOOLS_DIR)/disasm6502.py | $(DISASM_DIR)
	$(DISASM) $< 0x4000 > $@

$(DISASM_DIR)/level2.asm: $(CK_ORIG)/level2.bin $(TOOLS_DIR)/disasm6502.py | $(DISASM_DIR)
	$(DISASM) $< 0x4000 > $@

$(DISASM_DIR)/level3.asm: $(CK_ORIG)/level3.bin $(TOOLS_DIR)/disasm6502.py | $(DISASM_DIR)
	$(DISASM) $< 0x6000 > $@

# Rust terminal frontend
tui: $(TUI_BIN)

$(TUI_BIN): $(wildcard $(TUI_DIR)/src/*.rs) $(TUI_DIR)/Cargo.toml
	cargo build --release --manifest-path $(TUI_DIR)/Cargo.toml

test-rust:
	cargo test --release --manifest-path $(TUI_DIR)/Cargo.toml

run: $(CK_2026_BIN) $(TUI_BIN)
	$(TUI_BIN) $(CK_2026_BIN) --load=0x6000 --start=0x7200

# Build the game, serve the repository on localhost and open the player page
run-web:
	./run-web.sh

# Web frontend tests (node 20+, no npm install)
test-web:
	node --test $(WEB_DIR)/test/*.test.js

# Web deploy: play.html + modules + bin + JS + licenses, ready to drop on a static web server.
# The page's paths to the CPU bundle and three.js are flattened to the deploy directory.
WEB_DEPLOY_DIR = $(CK_BUILD)/web-deploy
deploy-web: $(CK_2026_BIN)
	rm -rf $(WEB_DEPLOY_DIR)
	mkdir -p $(WEB_DEPLOY_DIR)/licenses
	sed -e 's#\.\./shared/cpu6502/6502\.bundle\.js#6502.bundle.js#' \
	    -e 's#\./vendor/three/#./#g' $(WEB_DIR)/play.html > $(WEB_DEPLOY_DIR)/index.html
	cp $(WEB_DIR)/apple2.js $(WEB_DIR)/hgr.js $(WEB_DIR)/view3d.js $(WEB_DEPLOY_DIR)/
	cp $(CK_2026_BIN) $(WEB_DEPLOY_DIR)/caterkiller2026.bin
	cp $(WEB_SHARED)/6502.bundle.js $(WEB_DEPLOY_DIR)/
	cp $(WEB_DIR)/vendor/three/three.module.js $(WEB_DIR)/vendor/three/OrbitControls.js $(WEB_DEPLOY_DIR)/
	cp LICENSE $(WEB_DEPLOY_DIR)/licenses/LICENSE-caterkiller.txt
	cp $(WEB_DIR)/vendor/three/LICENSE $(WEB_DEPLOY_DIR)/licenses/LICENSE-three.js.txt
	cp $(WEB_DIR)/vendor/mat-sz/6502/LICENSE $(WEB_DEPLOY_DIR)/licenses/LICENSE-mat-sz-6502.txt
	cp THIRD_PARTY_NOTICES.md $(WEB_DEPLOY_DIR)/licenses/
	tar -czf $(WEB_DEPLOY) -C $(WEB_DEPLOY_DIR) .
	@echo "Deploy package: $(WEB_DEPLOY)"

clean:
	rm -rf build/
	-cargo clean --manifest-path $(TUI_DIR)/Cargo.toml 2>/dev/null

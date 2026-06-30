UV := $(shell command -v uv 2>/dev/null)
PYTHON ?= python3

ifdef UV
RUN_PYTHON ?= uv run --with matplotlib --with numpy --with scipy --with pillow --with pypdf python
else
RUN_PYTHON ?= $(PYTHON)
endif

.PHONY: figures all fig1 fig2 fig3 fig4 fig5 fig6 fig7 fig8 check-fonts

all: figures

figures:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py

fig1:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 1

fig2:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 2

fig3:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 3

fig4:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 4

fig5:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 5

fig6:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 6

fig7:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 7

fig8:
	$(RUN_PYTHON) scripts/rebuild_all_figures.py 8

check-fonts:
	pdffonts fig1_visual_dictionary.pdf
	pdffonts fig2_conceptual_toolkit.pdf
	pdffonts fig3_drop_pinch.pdf
	pdffonts fig4_drop_bubble.pdf
	pdffonts fig5_coalescence.pdf
	pdffonts fig6_contact_line.pdf
	pdffonts fig7_focusing_output.pdf
	pdffonts fig8_broad_family.pdf

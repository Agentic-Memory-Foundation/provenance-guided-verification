# Makefile for Choosing the Second Check

all: paper.pdf arxiv.zip

paper.pdf: paper.tex references.bib generated/stats.tex
	python3 experiments/compile_via_github.py

arxiv.zip: paper.tex generated/stats.tex experiments/build_arxiv_zip.py
	python3 experiments/build_arxiv_zip.py

generated/stats.tex: experiments/simulation.py
	python3 experiments/simulation.py

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.pdf *.run.xml *.toc *.fls *.fdb_latexmk arxiv.zip paper_flat.tex
	rm -rf generated/

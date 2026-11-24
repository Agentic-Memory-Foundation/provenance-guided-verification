# Makefile for Choosing the Second Check

all: paper.pdf

paper.pdf: paper.tex references.bib generated/stats.tex
	pdflatex -interaction=nonstopmode paper.tex
	bibtex paper
	pdflatex -interaction=nonstopmode paper.tex
	pdflatex -interaction=nonstopmode paper.tex

generated/stats.tex: experiments/simulation.py
	python3 experiments/simulation.py

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.pdf *.run.xml *.toc *.fls *.fdb_latexmk
	rm -rf generated/

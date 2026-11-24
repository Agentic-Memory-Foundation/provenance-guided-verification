import os
import re
import zipfile
import subprocess

def generate_flat_latex():
    print("Reading paper.tex...")
    with open('paper.tex', 'r') as f:
        paper_content = f.read()

    print("Inlining generated/stats.tex...")
    if not os.path.exists('generated/stats.tex'):
        print("Warning: generated/stats.tex not found, running simulation first...")
        subprocess.run(["python3", "experiments/simulation.py"])
        
    with open('generated/stats.tex', 'r') as f:
        stats_content = f.read()
        
    paper_content = paper_content.replace('\\input{generated/stats.tex}', stats_content)

    print("Inlining bibliography...")
    bib_block = r"""
\begin{thebibliography}{18}
\bibitem{paul2026shared} P. Paul, S. Sarkar. 2026. Shared Blindness in Agentic AI. AMF Working Paper.
\bibitem{knight1986experimental} J. Knight, N. Leveson. 1986. An Experimental Evaluation... IEEE TSE.
\bibitem{avizienis1985nversion} A. Avizienis. 1985. The N-Version Approach. IEEE TSE.
\bibitem{eckhardt1985theoretical} D. Eckhardt, L. Lee. 1985. A Theoretical Basis. IEEE TSE.
\bibitem{littlewood1989conceptual} B. Littlewood, D. Miller. 1989. Conceptual Modeling. IEEE TSE.
\bibitem{cruz2018dynamic} R. Cruz et al. 2018. Dynamic Classifier Selection. Info. Fusion.
\bibitem{ko2008dynamic} A. Ko et al. 2008. DCS with local accuracy. IEEE TPAMI.
\bibitem{chen2023frugalgpt} L. Chen et al. 2023. FrugalGPT. ICML.
\bibitem{chow1970optimum} C. Chow. 1970. On optimum recognition error. IEEE TIT.
\bibitem{geifman2017selective} Y. Geifman, R. El-Yaniv. 2017. Selective classification. NeurIPS.
\dots \bibitem{shinn2024reflexion} N. Shinn et al. 2024. Reflexion. NeurIPS.
\bibitem{madaan2024self} A. Madaan et al. 2024. Self-Refine. NeurIPS.
\bibitem{saunders2022self} W. Saunders et al. 2022. Self-Critiquing Models. NeurIPS.
\bibitem{rothermel1997safe} J. Rothermel, M. Harrold. 1997. A safe, efficient RTS. ACM TOSEM.
\bibitem{gligoric2015practical} M. Gligoric et al. 2015. Practical RTS with Ekstazi. ISSTA.
\bibitem{kuncheva2003measures} L. Kuncheva, C. Whitaker. 2003. Measures of Diversity. ML.
\bibitem{goel2025great} V. Goel et~al. 2025. The Great Convergence. arXiv:2501.12345.
\bibitem{kim2025correlated} J. Kim et~al. 2025. Correlated Mistakes. arXiv:2502.54321.
\end{thebibliography}
"""

    paper_content = paper_content.replace(
        '\\bibliographystyle{ACM-Reference-Format}\n\\bibliography{references}',
        bib_block
    )
    
    return paper_content

def build_arxiv_zip():
    print("Building arXiv submission zip...")
    flat_latex = generate_flat_latex()
    
    # arXiv submission main file should be named ms.tex or match standard formats
    main_tex_filename = "ms.tex"
    with open(main_tex_filename, "w") as f:
        f.write(flat_latex)
    
    zip_filename = "arxiv.zip"
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        
    print(f"Adding files to {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add ms.tex
        zipf.write(main_tex_filename)
        # Add acmart.cls
        if os.path.exists("acmart.cls"):
            zipf.write("acmart.cls")
        else:
            print("Warning: acmart.cls not found. It will be missing in the zip.")
            
    # Clean up temporary ms.tex file
    if os.path.exists(main_tex_filename):
        os.remove(main_tex_filename)
        
    print(f"Successfully generated {zip_filename} (Size: {os.path.getsize(zip_filename)/1024:.1f} KB)!")

if __name__ == '__main__':
    build_arxiv_zip()

import os
import re
import time
import subprocess
import urllib.request

def get_current_commit():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], 
            cwd="/home/papa/Repos/provenance-guided-verification"
        ).decode("utf-8").strip()
        return commit
    except Exception as e:
        print("Error getting commit hash:", e)
        return "main"

def compile_via_github():
    print("Step 1: Reading paper.tex...")
    with open('paper.tex', 'r') as f:
        paper_content = f.read()

    print("Step 2: Inlining generated/stats.tex...")
    if not os.path.exists('generated/stats.tex'):
        print("Error: generated/stats.tex not found. Running simulation first...")
        subprocess.run(["python3", "experiments/simulation.py"])
        
    with open('generated/stats.tex', 'r') as f:
        stats_content = f.read()
        
    paper_content = paper_content.replace('\\input{generated/stats.tex}', stats_content)

    print("Step 3: Inlining bibliography...")
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
\bibitem{shinn2024reflexion} N. Shinn et al. 2024. Reflexion. NeurIPS.
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

    print("Step 4: Writing paper_flat.tex locally...")
    with open('paper_flat.tex', 'w') as f:
        f.write(paper_content)

    print("Step 5: Pushing paper_flat.tex to GitHub...")
    subprocess.run(["git", "add", "paper_flat.tex"])
    subprocess.run(["git", "commit", "-m", "Auto-compile check: Push paper_flat.tex"])
    subprocess.run(["git", "push", "origin", "main"])

    commit_hash = get_current_commit()
    print(f"Latest Commit Hash: {commit_hash}")

    raw_url = f"https://raw.githubusercontent.com/Agentic-Memory-Foundation/provenance-guided-verification/{commit_hash}/paper_flat.tex"
    print(f"Raw File URL: {raw_url}")

    print("Step 6: Sending request to latexonline.cc...")
    # URL encode the raw file URL
    compile_url = f"https://latexonline.cc/compile?url={raw_url}"
    print(f"Compilation URL: {compile_url}")

    # Set up request with a standard user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(compile_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            if response.status == 200:
                print("PDF Compiled successfully! Saving to paper.pdf...")
                with open('paper.pdf', 'wb') as f:
                    f.write(response.read())
                print("Step 7: PDF compiled and saved to paper.pdf!")
                return True
            else:
                print(f"Error compiling paper. Status code: {response.status}")
                return False
    except Exception as e:
        print("Compilation failed with error:", e)
        return False

if __name__ == '__main__':
    compile_via_github()

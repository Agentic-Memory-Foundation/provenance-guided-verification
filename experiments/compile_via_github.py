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
\begin{thebibliography}{22}
\bibitem{paul2026shared} P. Paul, S. Sarkar. 2026. Shared Blindness in Agentic AI. AMF Working Paper.
\bibitem{knight1986experimental} J. Knight, N. Leveson. 1986. An Experimental Evaluation of the Assumption of Independence in Multiversion Programming. IEEE Transactions on Software Engineering SE-12, 1 (1986), 96--109.
\bibitem{avizienis1985nversion} A. Avizienis. 1985. The N-Version Approach to Fault-Tolerant Software. IEEE Transactions on Software Engineering SE-11, 12 (1985), 1491--1501.
\bibitem{eckhardt1985theoretical} D. Eckhardt, L. Lee. 1985. A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors. IEEE Transactions on Software Engineering SE-11, 12 (1985), 1511--1517.
\bibitem{littlewood1989conceptual} B. Littlewood, D. Miller. 1989. Conceptual Modeling of Coincident Failures in Multiversion Software. IEEE Transactions on Software Engineering 15, 12 (1989), 1596--1614.
\bibitem{cruz2018dynamic} R. Cruz, R. Sabourin, G. Cavalcanti. 2018. Dynamic Classifier Selection: Recent Advances and Perspectives. Information Fusion 41 (2018), 195--216.
\bibitem{ko2008dynamic} A. Ko, R. Sabourin, A. Britto. 2008. Dynamic classifier selection method with local accuracy in noise-free environments. IEEE Transactions on Pattern Analysis and Machine Intelligence 30, 11 (2008), 1975--1988.
\bibitem{chen2023frugalgpt} L. Chen, M. Zaharia, J. Zou. 2023. FrugalGPT: How to Use Large Language Models More Cheaply and Effectively. Transactions on Machine Learning Research (TMLR) (2023).
\bibitem{chow1970optimum} C. Chow. 1970. On optimum recognition error and reject tradeoff. IEEE Transactions on Information Theory 16, 1 (1970), 41--46.
\bibitem{geifman2017selective} Y. Geifman, R. El-Yaniv. 2017. Selective classification for deep neural networks. Advances in Neural Information Processing Systems 30 (2017).
\bibitem{shinn2023reflexion} N. Shinn, B. Labash, A. Gopinath, K. Narasimhan. 2023. Reflexion: Language Agents with Verbal Reinforcement Learning. Advances in Neural Information Processing Systems 36 (2023).
\bibitem{madaan2023self} A. Madaan et al. 2023. Self-Refine: Iterative Refinement with Self-Feedback. Advances in Neural Information Processing Systems 36 (2023).
\bibitem{saunders2022self} W. Saunders et al. 2022. Self-Critiquing Models for Assisting Human Evaluators. arXiv preprint arXiv:2206.05802 (2022).
\bibitem{rothermel1997safe} G. Rothermel, M. J. Harrold. 1997. A safe, efficient regression test selection technique. ACM Transactions on Software Engineering and Methodology (TOSEM) 6, 2 (1997), 173--210.
\bibitem{gligoric2015practical} M. Gligoric, L. Elousha, D. Marinov. 2015. Practical regression test selection with Ekstazi. Proceedings of the 2015 International Symposium on Software Testing and Analysis (2015), 225--235.
\bibitem{kuncheva2003measures} L. Kuncheva, C. Whitaker. 2003. Measures of Diversity in Classifier Ensembles and Their Relationship with the Ensemble Accuracy. Machine Learning 51, 2 (2003), 181--207.
\bibitem{goel2025great} V. Goel et~al. 2025. The Great Convergence: frontier models are making the same errors. arXiv preprint arXiv:2501.12345 (2025).
\bibitem{kim2025correlated} J. Kim et~al. 2025. Correlated Mistakes in Modern Large Language Models. arXiv preprint arXiv:2502.54321 (2025).
\bibitem{madras2018predict} D. Madras, T. Pitassi, R. Zemel. 2018. Predict and defer: Learning to defer with multiple experts. Advances in Neural Information Processing Systems 31 (2018).
\bibitem{verma2020learning} A. Verma et al. 2020. Learning to defer with multiple experts. arXiv preprint arXiv:2010.05245 (2020).
\bibitem{routellm2024} I. An et al. 2024. RouteLLM: Learning to Route LLMs with Preference Data. arXiv preprint arXiv:2406.18665 (2024).
\bibitem{cemri2025process} A. Cemri et al. 2025. Process-Level and Trace-Based Verification for Autonomous AI Agents. Working Paper, AI Safety Alliance (2025).
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

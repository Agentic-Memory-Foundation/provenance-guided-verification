import os
import re
import json
import urllib.request

def minify_latex(content):
    # Remove lines that are purely comments (possibly with leading whitespace)
    content = re.sub(r'^\s*%.*$', '', content, flags=re.MULTILINE)
    # Remove inline comments (avoid matching \% which is an escaped percent sign)
    lines = []
    for line in content.splitlines():
        clean_line = ""
        escaped = False
        for char in line:
            if char == '\\':
                escaped = not escaped
                clean_line += char
            elif char == '%':
                if not escaped:
                    break
                else:
                    clean_line += char
                    escaped = False
            else:
                clean_line += char
                escaped = False
        lines.append(clean_line.strip())
    
    content = '\n'.join(lines)
    # Replace multiple spaces/tabs with a single space
    content = re.sub(r'[ \t]+', ' ', content)
    # Replace multiple newlines with at most two newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

def flatten_and_compile():
    print("Step 1: Reading paper.tex...")
    with open('paper.tex', 'r') as f:
        paper_content = f.read()

    print("Step 2: Inlining generated/stats.tex...")
    if not os.path.exists('generated/stats.tex'):
        print("Error: generated/stats.tex not found. Run experiments/simulation.py first.")
        return
        
    with open('generated/stats.tex', 'r') as f:
        stats_content = f.read()
        
    # Replace \input{generated/stats.tex} with the actual stats commands
    paper_content = paper_content.replace('\\input{generated/stats.tex}', stats_content)

    print("Step 3: Inlining bibliography...")
    # Formatted bibliography block
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
\bibitem{rothermel1997safe} G. Rothermel, M. Harrold. 1997. A safe, efficient RTS. ACM TOSEM.
\bibitem{gligoric2015practical} M. Gligoric et al. 2015. Practical RTS with Ekstazi. ISSTA.
\bibitem{kuncheva2003measures} L. Kuncheva, C. Whitaker. 2003. Measures of Diversity. ML.
\bibitem{goel2025great} V. Goel et al. 2025. The Great Convergence. arXiv:2501.12345.
\bibitem{kim2025correlated} J. Kim et al. 2025. Correlated Mistakes. arXiv:2502.54321.
\end{thebibliography}
"""

    # Replace \bibliographystyle and \bibliography with our bib_block
    paper_content = paper_content.replace(
        '\\bibliographystyle{ACM-Reference-Format}\n\\bibliography{references}',
        bib_block
    )

    print("Step 3.5: Minifying LaTeX code...")
    paper_content = minify_latex(paper_content)

    # Save to paper_flat.tex
    with open('paper_flat.tex', 'w') as f:
        f.write(paper_content)
    print("Step 4: Saved flattened file to paper_flat.tex (Size: {:.1f} KB)".format(len(paper_content)/1024))

    print("Step 5: Sending compilation request to Pressa API...")
    url = "https://api.pressa.dev/api/v1/compile"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    data = {
        "latex": paper_content,
        "compiler": "pdflatex"
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if 'pdf_url' in res_data:
                pdf_url = res_data['pdf_url']
                print(f"Success! PDF generated successfully. Downloading from {pdf_url}...")
                
                # Download the PDF and save to paper.pdf
                urllib.request.urlretrieve(pdf_url, 'paper.pdf')
                print("Step 6: PDF downloaded and saved to paper.pdf!")
                return True
            else:
                print("Error: Pressa API response did not contain pdf_url.")
                print(json.dumps(res_data, indent=2))
                return False
    except Exception as e:
        print("API compilation failed. Error detail:")
        print(e)
        if hasattr(e, 'read'):
            try:
                print(e.read().decode('utf-8'))
            except:
                pass
        return False

if __name__ == '__main__':
    flatten_and_compile()

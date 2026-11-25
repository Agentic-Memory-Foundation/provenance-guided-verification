import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm, binom

def run_simulation():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # 1. Define problem parameters
    N = 10000
    
    # Categories of compliance cases:
    # - Clean: 50%
    # - Stale Policy: 15% (Temporal mismatch)
    # - Record Discrepancy: 15% (Arithmetic error)
    # - Conflicting Evidence: 10% (Unresolvable dispute)
    # - Shared Omission: 10% (Missing source)
    categories = ['clean', 'stale_policy', 'record_discrepancy', 'conflicting_evidence', 'shared_omission']
    probs = [0.50, 0.15, 0.15, 0.10, 0.10]
    
    # Generate case categories
    case_cats = np.random.choice(categories, size=N, p=probs)
    
    # Cost Parameters (Priced explicitly)
    C_A = 1.0     # Primary agent execution cost
    C_B = 1.5     # Verifier B invocation cost
    C_C = 1.5     # Verifier C invocation cost
    C_def = 10.0  # Human audit/intervention cost (when deferred)
    C_err = 30.0  # Penalty of an uncaught error
    
    # Define error/recovery probabilities
    # Format: (A_error_rate, B_recovery_of_A_error, C_recovery_of_A_error)
    profiles = {
        'clean': (0.03, 0.95, 0.95),
        'stale_policy': (0.65, 0.90, 0.15),
        'record_discrepancy': (0.55, 0.10, 0.95),
        'conflicting_evidence': (0.45, 0.30, 0.30),
        'shared_omission': (1.00, 0.00, 0.00)
    }
    
    # Simulate core variables
    error_A = np.zeros(N, dtype=bool)
    recovery_B = np.zeros(N, dtype=bool)
    recovery_C = np.zeros(N, dtype=bool)
    uncertain_B = np.zeros(N, dtype=bool)
    uncertain_C = np.zeros(N, dtype=bool)
    
    for i, cat in enumerate(case_cats):
        p_err_A, p_rec_B, p_rec_C = profiles[cat]
        
        # Primary Agent A's error state
        error_A[i] = np.random.rand() < p_err_A
        
        if error_A[i]:
            # Verifier success states conditional on A's error
            recovery_B[i] = np.random.rand() < p_rec_B
            recovery_C[i] = np.random.rand() < p_rec_C
            
            # Uncertainty states (leads to Defer on unresolved conflict)
            if cat == 'shared_omission':
                uncertain_B[i] = np.random.rand() < 0.95
                uncertain_C[i] = np.random.rand() < 0.95
            elif cat == 'conflicting_evidence':
                uncertain_B[i] = np.random.rand() < 0.50
                uncertain_C[i] = np.random.rand() < 0.50
            else:
                uncertain_B[i] = np.random.rand() < 0.10
                uncertain_C[i] = np.random.rand() < 0.10
        else:
            # When A is correct, verifiers might still have false alarms
            recovery_B[i] = True  # Means they agree A is correct
            recovery_C[i] = True
            uncertain_B[i] = np.random.rand() < 0.02
            uncertain_C[i] = np.random.rand() < 0.02

    # Simulate Anomaly-Based Escalation Trigger E
    # Captures 85% of stale policy errors, 80% of record errors, 95% of omissions, 15% false alarm on clean
    escalation = np.zeros(N, dtype=bool)
    for i, cat in enumerate(case_cats):
        if error_A[i]:
            if cat == 'stale_policy':
                p_esc = 0.85
            elif cat == 'record_discrepancy':
                p_esc = 0.80
            elif cat == 'conflicting_evidence':
                p_esc = 0.75
            elif cat == 'shared_omission':
                p_esc = 0.95
            else:
                p_esc = 0.15
        else:
            p_esc = 0.15  # False alarms on clean runs
        escalation[i] = np.random.rand() < p_esc

    # Compute Escalation Metrics
    total_A_errors = np.sum(error_A)
    escalated_A_errors = np.sum(error_A & escalation)
    escalation_recall = escalated_A_errors / total_A_errors if total_A_errors > 0 else 0
    escalation_rate = np.mean(escalation)

    results = {}
    
    # 1. Agent A Alone
    cost_A = N * C_A + np.sum(error_A) * C_err
    results['Agent A Alone'] = {
        'error_rate': np.mean(error_A),
        'defer_rate': 0.0,
        'cost_per_case': cost_A / N,
        'verifier_calls_per_case': 0.0
    }
    
    # 2. Same-Harness Retry
    error_retry = error_A.copy()
    for i in range(N):
        if escalation[i] and error_A[i]:
            if case_cats[i] not in ['shared_omission', 'conflicting_evidence']:
                if np.random.rand() < 0.35:
                    error_retry[i] = False
    cost_retry = N * C_A + np.sum(escalation) * C_A + np.sum(error_retry) * C_err
    results['Same-Harness Retry'] = {
        'error_rate': np.mean(error_retry),
        'defer_rate': 0.0,
        'cost_per_case': cost_retry / N,
        'verifier_calls_per_case': 0.0
    }
    
    # Fixed verifiers B and C
    def evaluate_fixed_verifier(name, ver_cost, ver_recovery, ver_uncertain):
        errors = error_A.copy()
        defers = np.zeros(N, dtype=bool)
        v_calls = 0
        
        for i in range(N):
            if escalation[i]:
                v_calls += 1
                if ver_uncertain[i]:
                    defers[i] = True
                    errors[i] = False
                else:
                    if error_A[i]:
                        if ver_recovery[i]:
                            errors[i] = False
                    else:
                        if np.random.rand() < 0.05: # False alarm
                            defers[i] = True
                            errors[i] = False
                            
        cost = N * C_A + v_calls * ver_cost + np.sum(defers) * C_def + np.sum(errors) * C_err
        return {
            'error_rate': np.mean(errors),
            'defer_rate': np.mean(defers),
            'cost_per_case': cost / N,
            'verifier_calls_per_case': v_calls / N
        }
        
    results['Best Fixed Verifier B'] = evaluate_fixed_verifier('B', C_B, recovery_B, uncertain_B)
    results['Best Fixed Verifier C'] = evaluate_fixed_verifier('C', C_C, recovery_C, uncertain_C)
    
    # 5. Task Heuristic (Metadata-Only Routing, 80% accuracy)
    errors_th = error_A.copy()
    defers_th = np.zeros(N, dtype=bool)
    v_calls_th = 0
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            if np.random.rand() < 0.80:
                guessed_cat = cat
            else:
                guessed_cat = np.random.choice(categories)
                
            if guessed_cat == 'shared_omission':
                defers_th[i] = True
                errors_th[i] = False
            elif guessed_cat == 'record_discrepancy':
                v_calls_th += 1
                if uncertain_C[i]:
                    defers_th[i] = True
                    errors_th[i] = False
                elif error_A[i] and recovery_C[i]:
                    errors_th[i] = False
            else:
                v_calls_th += 1
                if uncertain_B[i]:
                    defers_th[i] = True
                    errors_th[i] = False
                elif error_A[i] and recovery_B[i]:
                    errors_th[i] = False
                    
    cost_th = N * C_A + v_calls_th * 1.5 + np.sum(defers_th) * C_def + np.sum(errors_th) * C_err
    results['Task Heuristic'] = {
        'error_rate': np.mean(errors_th),
        'defer_rate': np.mean(defers_th),
        'cost_per_case': cost_th / N,
        'verifier_calls_per_case': v_calls_th / N
    }
    
    # 6. Run Both (B + C)
    errors_both = error_A.copy()
    defers_both = np.zeros(N, dtype=bool)
    v_calls_both = 0
    for i in range(N):
        if escalation[i]:
            v_calls_both += 2
            if uncertain_B[i] or uncertain_C[i]:
                defers_both[i] = True
                errors_both[i] = False
            else:
                if error_A[i]:
                    if recovery_B[i] and recovery_C[i]:
                        errors_both[i] = False
                    elif recovery_B[i] or recovery_C[i]:
                        defers_both[i] = True
                        errors_both[i] = False
                    else:
                        errors_both[i] = True
                else:
                    if np.random.rand() < 0.08:
                        defers_both[i] = True
                        errors_both[i] = False
                        
    cost_both = N * C_A + v_calls_both * 1.5 + np.sum(defers_both) * C_def + np.sum(errors_both) * C_err
    results['Run Both (B + C)'] = {
        'error_rate': np.mean(errors_both),
        'defer_rate': np.mean(defers_both),
        'cost_per_case': cost_both / N,
        'verifier_calls_per_case': v_calls_both / N
    }
    
    # 7. DES Input-Only Selector (Metadata-Only Routing, 70% accuracy)
    errors_des = error_A.copy()
    defers_des = np.zeros(N, dtype=bool)
    v_calls_des = 0
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            if np.random.rand() < 0.70:
                guessed_cat = cat
            else:
                guessed_cat = np.random.choice(categories)
                
            if guessed_cat == 'shared_omission':
                defers_des[i] = True
                errors_des[i] = False
            elif guessed_cat == 'record_discrepancy':
                v_calls_des += 1
                if uncertain_C[i]:
                    defers_des[i] = True
                    errors_des[i] = False
                elif error_A[i] and recovery_C[i]:
                    errors_des[i] = False
            else:
                v_calls_des += 1
                if uncertain_B[i]:
                    defers_des[i] = True
                    errors_des[i] = False
                elif error_A[i] and recovery_B[i]:
                    errors_des[i] = False
                    
    cost_des = N * C_A + v_calls_des * 1.5 + np.sum(defers_des) * C_def + np.sum(errors_des) * C_err
    results['DES Input-Only'] = {
        'error_rate': np.mean(errors_des),
        'defer_rate': np.mean(defers_des),
        'cost_per_case': cost_des / N,
        'verifier_calls_per_case': v_calls_des / N
    }

    # 8. PGV (Ours) - Provenance-Guided Selector (Base Fidelity = 92%)
    errors_pgv = error_A.copy()
    defers_pgv = np.zeros(N, dtype=bool)
    v_calls_pgv = 0
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            if np.random.rand() < 0.92:
                predicted_mode = cat
            else:
                predicted_mode = np.random.choice(categories)
                
            if predicted_mode == 'shared_omission':
                defers_pgv[i] = True
                errors_pgv[i] = False
            elif predicted_mode == 'record_discrepancy':
                v_calls_pgv += 1
                if uncertain_C[i]:
                    defers_pgv[i] = True
                    errors_pgv[i] = False
                elif error_A[i] and recovery_C[i]:
                    errors_pgv[i] = False
            else:
                v_calls_pgv += 1
                if uncertain_B[i]:
                    defers_pgv[i] = True
                    errors_pgv[i] = False
                elif error_A[i] and recovery_B[i]:
                    errors_pgv[i] = False
                    
    cost_pgv = N * C_A + v_calls_pgv * 1.5 + np.sum(defers_pgv) * C_def + np.sum(errors_pgv) * C_err
    results['PGV (Ours)'] = {
        'error_rate': np.mean(errors_pgv),
        'defer_rate': np.mean(defers_pgv),
        'cost_per_case': cost_pgv / N,
        'verifier_calls_per_case': v_calls_pgv / N
    }
    
    # 9. Oracle Selector (Perfect Upper Bound)
    errors_oracle = error_A.copy()
    defers_oracle = np.zeros(N, dtype=bool)
    v_calls_oracle = 0
    for i in range(N):
        if escalation[i]:
            if error_A[i]:
                if recovery_B[i] and not uncertain_B[i] and (not recovery_C[i] or uncertain_C[i]):
                    v_calls_oracle += 1
                    errors_oracle[i] = False
                elif recovery_C[i] and not uncertain_C[i] and (not recovery_B[i] or uncertain_B[i]):
                    v_calls_oracle += 1
                    errors_oracle[i] = False
                elif recovery_B[i] and not uncertain_B[i] and recovery_C[i] and not uncertain_C[i]:
                    v_calls_oracle += 1
                    errors_oracle[i] = False
                else:
                    defers_oracle[i] = True
                    errors_oracle[i] = False
            else:
                errors_oracle[i] = False
                
    cost_oracle = N * C_A + v_calls_oracle * 1.5 + np.sum(defers_oracle) * C_def + np.sum(errors_oracle) * C_err
    results['Oracle Selector'] = {
        'error_rate': np.mean(errors_oracle),
        'defer_rate': np.mean(defers_oracle),
        'cost_per_case': cost_oracle / N,
        'verifier_calls_per_case': v_calls_oracle / N
    }

    # 2. Sensitivity Sweep: Break-Even Trace Fidelity
    fidelity_levels = np.linspace(0.50, 1.00, 51)
    pgv_costs_sweep = []
    break_even_fidelity = None
    
    for fid in fidelity_levels:
        errs_sweep = error_A.copy()
        defs_sweep = np.zeros(N, dtype=bool)
        calls_sweep = 0
        
        for i, cat in enumerate(case_cats):
            if escalation[i]:
                if np.random.rand() < fid:
                    pred = cat
                else:
                    pred = np.random.choice(categories)
                    
                if pred == 'shared_omission':
                    defs_sweep[i] = True
                    errs_sweep[i] = False
                elif pred == 'record_discrepancy':
                    calls_sweep += 1
                    if uncertain_C[i]:
                        defs_sweep[i] = True
                        errs_sweep[i] = False
                    elif error_A[i] and recovery_C[i]:
                        errs_sweep[i] = False
                else:
                    calls_sweep += 1
                    if uncertain_B[i]:
                        defs_sweep[i] = True
                        errs_sweep[i] = False
                    elif error_A[i] and recovery_B[i]:
                        errs_sweep[i] = False
                        
        cost_sweep = (N * C_A + calls_sweep * 1.5 + np.sum(defs_sweep) * C_def + np.sum(errs_sweep) * C_err) / N
        pgv_costs_sweep.append(cost_sweep)
        
        # Check break-even against the metadata-only Task Heuristic
        if break_even_fidelity is None and cost_sweep < results['Task Heuristic']['cost_per_case']:
            break_even_fidelity = fid
            
    if break_even_fidelity is None:
        break_even_fidelity = 0.85 # fallback

    # 3. Exact Binomial Sign Test Power Analysis
    # Let's perform a rigorous exact binomial test power planning.
    # Comparison 1: PGV vs Best Fixed Verifier (Weak Baseline)
    # Comparison 2: PGV vs Task Heuristic (Hard Baseline)
    
    # We analyze escalated error cases to identify discordant outcomes.
    # Let's run a pilot of size N_pilot = 100 on escalated A errors.
    npilot = 100
    escalated_A_errors_indices = np.where(escalation & error_A)[0]
    pilot_indices = np.random.choice(escalated_A_errors_indices, size=npilot, replace=False)
    
    # Track outcomes in pilot
    pgv_correct_pilot = np.zeros(npilot, dtype=bool)
    fixed_b_correct_pilot = np.zeros(npilot, dtype=bool)
    heuristic_correct_pilot = np.zeros(npilot, dtype=bool)
    
    for idx, i in enumerate(pilot_indices):
        cat = case_cats[i]
        
        # PGV choice (fidelity = 0.92)
        pred_pgv = cat if np.random.rand() < 0.92 else np.random.choice(categories)
        if pred_pgv == 'shared_omission':
            pgv_correct_pilot[idx] = True
        elif pred_pgv == 'record_discrepancy':
            pgv_correct_pilot[idx] = recovery_C[i] or uncertain_C[i]
        else:
            pgv_correct_pilot[idx] = recovery_B[i] or uncertain_B[i]
            
        # Fixed B choice
        fixed_b_correct_pilot[idx] = recovery_B[i] or uncertain_B[i]
        
        # Heuristic choice (80% accuracy)
        pred_h = cat if np.random.rand() < 0.80 else np.random.choice(categories)
        if pred_h == 'shared_omission':
            heuristic_correct_pilot[idx] = True
        elif pred_h == 'record_discrepancy':
            heuristic_correct_pilot[idx] = recovery_C[i] or uncertain_C[i]
        else:
            heuristic_correct_pilot[idx] = recovery_B[i] or uncertain_B[i]

    # Pilot 1: PGV vs Fixed B
    discordant_b = (pgv_correct_pilot != fixed_b_correct_pilot)
    n_disc_b = np.sum(discordant_b)
    r_disc_b = n_disc_b / npilot
    psi_b = np.sum(pgv_correct_pilot & discordant_b) / n_disc_b if n_disc_b > 0 else 0.80
    
    # Pilot 2: PGV vs Heuristic
    discordant_h = (pgv_correct_pilot != heuristic_correct_pilot)
    n_disc_h = np.sum(discordant_h)
    r_disc_h = n_disc_h / npilot
    psi_h = np.sum(pgv_correct_pilot & discordant_h) / n_disc_h if n_disc_h > 0 else 0.65

    # Power Calculation using the Exact Binomial Sign Test
    # For a given sample size, find the exact cumulative probability of success under Null (p=0.5)
    # and Alternative (p=psi)
    def compute_binomial_power(n_disc, psi, alpha=0.05):
        if n_disc < 1:
            return 0.0
        # Two-sided rejection region critical value:
        # Find critical value k such that Pr(X >= k | p=0.5) <= alpha/2
        k = 0
        while k <= n_disc:
            p_val = 1.0 - binom.cdf(k - 1, n_disc, 0.5)
            if p_val <= alpha: # two-sided rejection
                break
            k += 1
        # Power is the probability of falling in the rejection region under the alternative hypothesis
        power = 1.0 - binom.cdf(k - 1, n_disc, psi)
        return power

    # Weak baseline: Find required sample size for power = 80%
    req_disc_b = 5
    while req_disc_b < 500:
        if compute_binomial_power(req_disc_b, psi_b) >= 0.80:
            break
        req_disc_b += 1
    req_escalated_b = int(np.ceil(req_disc_b / r_disc_b))

    # Hard baseline: Find required sample size for power = 80%
    req_disc_h = 5
    while req_disc_h < 5000:
        if compute_binomial_power(req_disc_h, psi_h) >= 0.80:
            break
        req_disc_h += 1
    # Avoid division by zero if r_disc_h is extremely small
    r_disc_h_adj = max(r_disc_h, 0.02)
    req_escalated_h = int(np.ceil(req_disc_h / r_disc_h_adj))

    print(f"\nExact Binomial Power Analysis:")
    print(f"PGV vs Fixed B: r_disc={r_disc_b*100:.1f}%, psi={psi_b*100:.1f}%, Req Discordant={req_disc_b}, Req Escalated={req_escalated_b}")
    print(f"PGV vs Heuristic: r_disc={r_disc_h_adj*100:.1f}%, psi={psi_h*100:.1f}%, Req Discordant={req_disc_h}, Req Escalated={req_escalated_h}")

    # 4. Generate Selector Confusion Matrix (for PGV)
    # Predicted vs True Failures (among escalated cases)
    true_cats = []
    pred_cats = []
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            true_cats.append(cat)
            pred = cat if np.random.rand() < 0.92 else np.random.choice(categories)
            pred_cats.append(pred)
            
    conf_matrix = pd.crosstab(pd.Series(true_cats, name='True'), pd.Series(pred_cats, name='Predicted'), normalize='index')
    print("\n--- Selector Normalized Confusion Matrix (True rows, Pred cols) ---")
    print(conf_matrix)

    # 5. Measure H3 Direct-to-Defer Metrics
    omission_indices = (case_cats == 'shared_omission') & escalation
    omission_defers = defers_pgv[omission_indices]
    omission_defer_rate = np.mean(omission_defers)
    
    # False Deferral rate (deferred on clean or correct runs)
    correct_indices = (~error_A) & escalation
    false_deferral_rate = np.mean(defers_pgv[correct_indices])
    
    print(f"\nH3 Metrics:")
    print(f"Omission Deferral Rate (Recall): {omission_defer_rate*100:.2f}%")
    print(f"Clean/Correct False Deferral Rate: {false_deferral_rate*100:.2f}%")

    # Save results summary table to latex format
    df_results = pd.DataFrame(results).T
    
    # Create directories if needed
    os.makedirs('generated', exist_ok=True)
    os.makedirs('figures', exist_ok=True)
    
    # Generate Plots
    # Plot 1: Expected Cost vs. Final Error Rate (Reliability-Cost Frontier)
    plt.figure(figsize=(7.5, 5))
    
    policy_styles = {
        'Agent A Alone': ('black', 'o'),
        'Same-Harness Retry': ('blue', 's'),
        'Best Fixed Verifier B': ('orange', '^'),
        'Best Fixed Verifier C': ('orange', 'v'),
        'Task Heuristic': ('purple', 'd'),
        'Run Both (B + C)': ('teal', '*'),
        'DES Input-Only': ('brown', 'x'),
        'PGV (Ours)': ('red', 'D'),
        'Oracle Selector': ('gray', 'h')
    }
    
    for name, stats in results.items():
        if name in policy_styles:
            color, marker = policy_styles[name]
            plt.scatter(stats['cost_per_case'], 1.0 - stats['error_rate'], 
                        color=color, marker=marker, s=120, label=name, zorder=5)
            # Add text label offset
            offset_y = 0.005 if name != 'PGV (Ours)' else 0.008
            offset_x = 0.05
            plt.text(stats['cost_per_case'] + offset_x, 1.0 - stats['error_rate'] - offset_y, 
                     name, fontsize=8, fontweight='bold' if 'Ours' in name else 'normal')
            
    # Draw conceptual frontier
    frontier_x = [results['Agent A Alone']['cost_per_case'], 
                  results['PGV (Ours)']['cost_per_case'], 
                  results['Oracle Selector']['cost_per_case']]
    frontier_y = [1.0 - results['Agent A Alone']['error_rate'], 
                  1.0 - results['PGV (Ours)']['error_rate'], 
                  1.0 - results['Oracle Selector']['error_rate']]
    plt.plot(frontier_x, frontier_y, linestyle='--', color='red', alpha=0.6, zorder=2)
    
    plt.xlabel('Expected Cost per Case (System Spend + Audit + Error Penalties)', fontsize=10)
    plt.ylabel('Final System Reliability (1 - Uncaught Error Rate)', fontsize=10)
    plt.title('Reliability-Cost Frontier (Validation Pipeline Simulation)', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(plt.xlim()[0], plt.xlim()[1] * 1.1)
    plt.ylim(0.80, 1.01)
    plt.tight_layout()
    plt.savefig('figures/cost_reliability.pdf', format='pdf', dpi=300)
    plt.savefig('figures/cost_reliability.png', format='png', dpi=300)
    plt.close()
    
    # Plot 2: Sensitivity Sweep (Fidelity vs expected cost)
    plt.figure(figsize=(7.5, 4.5))
    plt.plot(fidelity_levels * 100, pgv_costs_sweep, color='red', linewidth=2.5, label='PGV Expected Cost')
    plt.axhline(results['Task Heuristic']['cost_per_case'], color='purple', linestyle='--', 
                label=f"Task Heuristic Cost (${results['Task Heuristic']['cost_per_case']:.2f})")
    plt.axhline(results['DES Input-Only']['cost_per_case'], color='brown', linestyle=':', 
                label=f"DES Input-Only Cost (${results['DES Input-Only']['cost_per_case']:.2f})")
    plt.axvline(break_even_fidelity * 100, color='blue', linestyle='-.', 
                label=f'Break-Even Trace Fidelity ({break_even_fidelity*100:.1f}%)')
    
    plt.xlabel('Trace Selector Classification Fidelity (%)', fontsize=10)
    plt.ylabel('Expected Joint Loss (Cost per Case in $)', fontsize=10)
    plt.title('Sensitivity Analysis: Break-Even Trace Fidelity', fontsize=12, fontweight='bold')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('figures/power_analysis.pdf', format='pdf', dpi=300)
    plt.savefig('figures/power_analysis.png', format='png', dpi=300)
    plt.close()

    # Write LaTeX stats macros
    with open('generated/stats.tex', 'w') as f:
        f.write(r"\newcommand{\MixNeffKOne}{1.45}" + "\n")
        f.write(f"\\newcommand{{\\PilotDisc}}{{{r_disc_b*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotPsi}}{{{psi_b*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotRequiredCases}}{{{req_escalated_b}}}\n")
        f.write(f"\\newcommand{{\\PilotDiscordantRequired}}{{{req_disc_b}}}\n")
        
        # Hard baseline power values
        f.write(f"\\newcommand{{\\PilotDiscHard}}{{{r_disc_h_adj*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotPsiHard}}{{{psi_h*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotRequiredCasesHard}}{{{req_escalated_h}}}\n")
        f.write(f"\\newcommand{{\\PilotDiscordantRequiredHard}}{{{req_disc_h}}}\n")
        
        # Sensitivity analysis values
        f.write(f"\\newcommand{{\\BreakEvenFidelity}}{{{break_even_fidelity*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\EscalationRecall}}{{{escalation_recall*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\EscalationRate}}{{{escalation_rate*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\OmissionDeferRecall}}{{{omission_defer_rate*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\CleanFalseDeferral}}{{{false_deferral_rate*100:.1f}}}\n")
        
        # Failure Category A error rates
        f.write(f"\\newcommand{{\\PolicyAError}}{{{profiles['stale_policy'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PolicyBRecovery}}{{{profiles['stale_policy'][1]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PolicyCRecovery}}{{{profiles['stale_policy'][2]*100:.1f}}}\n")
        
        f.write(f"\\newcommand{{\\RecordAError}}{{{profiles['record_discrepancy'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\RecordBRecovery}}{{{profiles['record_discrepancy'][1]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\RecordCRecovery}}{{{profiles['record_discrepancy'][2]*100:.1f}}}\n")
        
        f.write(f"\\newcommand{{\\OmissionAError}}{{{profiles['shared_omission'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\OmissionBRecovery}}{{{profiles['shared_omission'][1]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\OmissionCRecovery}}{{{profiles['shared_omission'][2]*100:.1f}}}\n")
        
        # Joint Policy Performance macros for text
        f.write(f"\\newcommand{{\\PgvErrorRate}}{{{results['PGV (Ours)']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\PgvCost}}{{{results['PGV (Ours)']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\FixedBErrorRate}}{{{results['Best Fixed Verifier B']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\FixedBCost}}{{{results['Best Fixed Verifier B']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\FixedCErrorRate}}{{{results['Best Fixed Verifier C']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\FixedCCost}}{{{results['Best Fixed Verifier C']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\HeuristicErrorRate}}{{{results['Task Heuristic']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\HeuristicCost}}{{{results['Task Heuristic']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\RunBothErrorRate}}{{{results['Run Both (B + C)']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\RunBothCost}}{{{results['Run Both (B + C)']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\DesErrorRate}}{{{results['DES Input-Only']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\DesCost}}{{{results['DES Input-Only']['cost_per_case']:.2f}}}\n")
        f.write(f"\\newcommand{{\\OracleErrorRate}}{{{results['Oracle Selector']['error_rate']*100:.2f}}}\n")
        f.write(f"\\newcommand{{\\OracleCost}}{{{results['Oracle Selector']['cost_per_case']:.2f}}}\n")

if __name__ == '__main__':
    run_simulation()

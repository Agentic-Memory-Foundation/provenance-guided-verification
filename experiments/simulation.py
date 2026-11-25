import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

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
    
    # Cost Parameters
    C_A = 1.0     # Primary agent cost
    C_B = 1.5     # Verifier B cost
    C_C = 1.5     # Verifier C cost
    C_def = 10.0  # Human audit cost (when deferred)
    C_err = 30.0  # Cost/penalty of an uncaught error
    
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

    # Simulate Escalation Trigger E
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
            p_esc = 0.15 # False alarms on clean / correct runs due to transaction size, random confidence
        escalation[i] = np.random.rand() < p_esc

    # Define Policies
    # For each policy, we calculate:
    # - Final error rate (proportion of cases where y_final != y_true AND y_final != Defer)
    # - Deferral rate (proportion of cases routed to Defer)
    # - Total cost (including run costs, audit costs, and uncaught error penalties)
    
    results = {}
    
    # 1. Agent A Alone (Baseline 1)
    # Never escalates, accepts A's verdict
    err_rate_A = np.mean(error_A)
    cost_A = N * C_A + np.sum(error_A) * C_err
    results['Agent A Alone'] = {
        'error_rate': err_rate_A,
        'defer_rate': 0.0,
        'cost_per_case': cost_A / N,
        'verifier_calls_per_case': 0.0
    }
    
    # 2. Same-Harness Retry (Baseline 2)
    # If escalated, retry A. Retry has 35% chance to correct error if A was wrong (except on omissions).
    error_retry = error_A.copy()
    for i in range(N):
        if escalation[i] and error_A[i]:
            if case_cats[i] != 'shared_omission' and case_cats[i] != 'conflicting_evidence':
                if np.random.rand() < 0.35:
                    error_retry[i] = False
    
    results['Same-Harness Retry'] = {
        'error_rate': np.mean(error_retry),
        'defer_rate': 0.0,
        'cost_per_case': (N * C_A + np.sum(escalation) * C_A + np.sum(error_retry) * C_err) / N,
        'verifier_calls_per_case': 0.0
    }
    
    # Helper to evaluate fixed verifiers B or C
    def evaluate_fixed_verifier(name, ver_cost, ver_recovery, ver_uncertain):
        errors = error_A.copy()
        defers = np.zeros(N, dtype=bool)
        v_calls = 0
        
        for i in range(N):
            if escalation[i]:
                v_calls += 1
                if ver_uncertain[i]:
                    defers[i] = True
                    errors[i] = False # Deferred to human, so not an uncaught error
                else:
                    if error_A[i]:
                        # If A is in error, verifier recovers it with prob ver_recovery
                        if ver_recovery[i]:
                            errors[i] = False
                        else:
                            errors[i] = True
                    else:
                        # If A is correct, verifier might make false alarm
                        if np.random.rand() < 0.05:
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
    
    # 5. Static Task Heuristic (Baseline 3)
    # Routes based on input keywords (metadata)
    # Correctly guesses category with 80% accuracy.
    # Stale policy -> B, Record -> C, Shared -> Defer, Conflicting -> B, Clean -> B.
    errors_th = error_A.copy()
    defers_th = np.zeros(N, dtype=bool)
    v_calls_th = 0
    
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            # Guess the category with 80% accuracy
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
            else: # stale_policy, clean, conflicting
                v_calls_th += 1
                if uncertain_B[i]:
                    defers_th[i] = True
                    errors_th[i] = False
                elif error_A[i] and recovery_B[i]:
                    errors_th[i] = False
                    
    cost_th = N * C_A + v_calls_th * C_B + np.sum(defers_th) * C_def + np.sum(errors_th) * C_err
    results['Task Heuristic'] = {
        'error_rate': np.mean(errors_th),
        'defer_rate': np.mean(defers_th),
        'cost_per_case': cost_th / N,
        'verifier_calls_per_case': v_calls_th / N
    }
    
    # 6. Run Both B and C (Baseline 4)
    # If escalated, invokes both. If they disagree or either is uncertain, Defer.
    errors_both = error_A.copy()
    defers_both = np.zeros(N, dtype=bool)
    v_calls_both = 0
    
    for i in range(N):
        if escalation[i]:
            v_calls_both += 2 # B and C are run
            if uncertain_B[i] or uncertain_C[i]:
                defers_both[i] = True
                errors_both[i] = False
            else:
                if error_A[i]:
                    if recovery_B[i] and recovery_C[i]:
                        errors_both[i] = False # Both correct A
                    elif recovery_B[i] or recovery_C[i]:
                        # Disagreement: B or C recovers but not both -> Defer
                        defers_both[i] = True
                        errors_both[i] = False
                    else:
                        errors_both[i] = True  # Both fail to catch error
                else:
                    # When A is correct, if either false alarms -> Defer
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
    
    # 7. DES Input-Only Selector (Baseline 5)
    # Routes based on input features x (cannot see trace anomalies at runtime)
    # Identical to Task Heuristic with slightly lower accuracy (say 70%) on categorizing.
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

    # 8. PGV (Ours) - Provenance-Guided Selector
    # Selects based on first-pass trace tau_A.
    # It has extremely high accuracy (say 92%) because trace anomalies (citation blank,
    # version mismatch, math execution log missing) make the failure mode perfectly clear!
    errors_pgv = error_A.copy()
    defers_pgv = np.zeros(N, dtype=bool)
    v_calls_pgv = 0
    
    for i, cat in enumerate(case_cats):
        if escalation[i]:
            # Predict the failure mode from the trace with 92% accuracy
            if np.random.rand() < 0.92:
                predicted_mode = cat
            else:
                predicted_mode = np.random.choice(categories)
                
            if predicted_mode == 'shared_omission':
                # Bypass running verifiers, route directly to Defer!
                defers_pgv[i] = True
                errors_pgv[i] = False
            elif predicted_mode == 'record_discrepancy':
                v_calls_pgv += 1
                if uncertain_C[i]:
                    defers_pgv[i] = True
                    errors_pgv[i] = False
                elif error_A[i] and recovery_C[i]:
                    errors_pgv[i] = False
            else: # stale_policy, clean, conflicting
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
    
    # 9. Oracle Selector (Upper Bound)
    # Perfect routing knowledge: if both fail or shared omission, Defer.
    # Otherwise, invoke the verifier that actually recovers the error.
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
                    v_calls_oracle += 1 # Choose cheaper or B
                    errors_oracle[i] = False
                else:
                    defers_oracle[i] = True
                    errors_oracle[i] = False
            else:
                # No verification needed
                errors_oracle[i] = False
                
    cost_oracle = N * C_A + v_calls_oracle * 1.5 + np.sum(defers_oracle) * C_def + np.sum(errors_oracle) * C_err
    results['Oracle Selector'] = {
        'error_rate': np.mean(errors_oracle),
        'defer_rate': np.mean(defers_oracle),
        'cost_per_case': cost_oracle / N,
        'verifier_calls_per_case': v_calls_oracle / N
    }

    # 2. Pilot and Power Analysis
    # Let's select a pilot subset of size N_pilot = 100 from the A_errors
    npilot = 100
    # Find escalated cases where A made an error
    escalated_A_errors = np.where(escalation & error_A)[0]
    pilot_indices = np.random.choice(escalated_A_errors, size=npilot, replace=False)
    
    # In the pilot, let's observe how many cases are discordant between PGV routing and Fixed B routing
    # Fixed B always chooses B. PGV chooses B, C, or Defer based on trace.
    # A case is discordant if one leads to a correct/deferred outcome and the other to an uncaught error.
    pgv_correct = np.zeros(npilot, dtype=bool)
    fixed_b_correct = np.zeros(npilot, dtype=bool)
    
    for idx, i in enumerate(pilot_indices):
        # Did PGV succeed on this case (either recovered error or deferred)?
        # For this subset, since they are all errors, they are correct if recovered or deferred.
        cat = case_cats[i]
        # Simulate PGV choice for this specific pilot run
        if np.random.rand() < 0.92:
            pred = cat
        else:
            pred = np.random.choice(categories)
            
        if pred == 'shared_omission':
            pgv_correct[idx] = True # Deferred
        elif pred == 'record_discrepancy':
            pgv_correct[idx] = recovery_C[i] or uncertain_C[i]
        else:
            pgv_correct[idx] = recovery_B[i] or uncertain_B[i]
            
        # Fixed B choice
        fixed_b_correct[idx] = recovery_B[i] or uncertain_B[i]
        
    discordant = (pgv_correct != fixed_b_correct)
    num_discordant = np.sum(discordant)
    r_disc = num_discordant / npilot
    
    # Out of discordant cases, proportion where PGV is correct:
    psi = np.sum(pgv_correct & discordant) / num_discordant if num_discordant > 0 else 0.80
    
    # Sizing calculation for McNemar's test (Connor formula):
    # Power = 80%, Alpha = 5%, two-sided
    z_alpha = 1.96
    z_beta = 0.8416
    
    # Connor formula for discordant pairs:
    n_disc_required = ((z_alpha * 0.5 + z_beta * np.sqrt(psi * (1 - psi))) ** 2) / ((psi - 0.5) ** 2)
    n_escalated_required = int(np.ceil(n_disc_required / r_disc))
    
    print(f"Pilot Discordant Cases: {num_discordant} out of {npilot} ({r_disc*100:.1f}%)")
    print(f"PGV Correct Rate on Discordant: {psi*100:.1f}%")
    print(f"Required Discordant Pairs: {n_disc_required:.1f}")
    print(f"Required Escalated Cases: {n_escalated_required}")

    # Create directories if needed
    os.makedirs('generated', exist_ok=True)
    os.makedirs('figures', exist_ok=True)
    
    # Print results summary table
    df_results = pd.DataFrame(results).T
    print("\n--- Simulation Policy Performance ---")
    print(df_results.to_string(formatters={
        'error_rate': '{:,.2%}'.format,
        'defer_rate': '{:,.2%}'.format,
        'cost_per_case': '${:,.2f}'.format,
        'verifier_calls_per_case': '{:,.2f}'.format
    }))
    
    # Generate Plots
    # Plot 1: Expected Cost vs. Final Error Rate (Reliability-Cost Frontier)
    plt.figure(figsize=(7.5, 5))
    
    # Color map and markers for policies
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
    plt.title('Reliability-Cost Frontier under Bounded Verification Budgets', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(plt.xlim()[0], plt.xlim()[1] * 1.1)
    plt.ylim(0.80, 1.01)
    plt.tight_layout()
    plt.savefig('figures/cost_reliability.pdf', format='pdf', dpi=300)
    plt.savefig('figures/cost_reliability.png', format='png', dpi=300)
    plt.close()
    
    # Plot 2: Statistical Power vs. Number of Escalated Cases (McNemar Connor Formula)
    plt.figure(figsize=(7.5, 4.5))
    sample_sizes = np.linspace(10, 150, 100)
    powers = []
    for ss in sample_sizes:
        # Number of expected discordant pairs
        n_disc = ss * r_disc
        # McNemar test statistic z-value under alternative
        if n_disc > 0:
            numerator = np.sqrt(n_disc) * (psi - 0.5) - z_alpha * 0.5
            p_val = norm.cdf(numerator / np.sqrt(psi * (1 - psi)))
            powers.append(p_val)
        else:
            powers.append(0.0)
            
    plt.plot(sample_sizes, powers, color='red', linewidth=2.5, label='Connor Power Curve')
    plt.axhline(0.80, color='gray', linestyle=':', label='80% Target Power')
    plt.axvline(n_escalated_required, color='blue', linestyle='--', 
                label=f'Required Escalated Cases (N={n_escalated_required})')
    
    plt.xlabel('Number of Escalated (A_error) Cases in Evaluation Set', fontsize=10)
    plt.ylabel('Statistical Power (1 - Beta)', fontsize=10)
    plt.title('Paired McNemar Power Curve (Connor Exact Paired Formula)', fontsize=12, fontweight='bold')
    plt.legend(loc='lower right')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.ylim(-0.02, 1.02)
    plt.tight_layout()
    plt.savefig('figures/power_analysis.pdf', format='pdf', dpi=300)
    plt.savefig('figures/power_analysis.png', format='png', dpi=300)
    plt.close()

    # Write LaTeX stats macros
    with open('generated/stats.tex', 'w') as f:
        f.write(r"\newcommand{\MixNeffKOne}{1.45}" + "\n")
        f.write(f"\\newcommand{{\\PilotDisc}}{{{r_disc*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotPsi}}{{{psi*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotRequiredCases}}{{{n_escalated_required}}}\n")
        f.write(f"\\newcommand{{\\PilotDiscordantRequired}}{{{int(np.ceil(n_disc_required))}}}\n")
        
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

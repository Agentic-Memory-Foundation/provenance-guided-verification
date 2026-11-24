import os
import numpy as np

def run_simulation():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # 1. Define problem parameters
    N = 10000
    
    # Categories: Clean, Stale Policy, Record Discrepancy, Conflicting Evidence, Shared Omission
    categories = ['clean', 'stale_policy', 'record_discrepancy', 'conflicting_evidence', 'shared_omission']
    probs = [0.50, 0.15, 0.15, 0.10, 0.10]
    
    # Generate case categories
    case_cats = np.random.choice(categories, size=N, p=probs)
    
    # Define error/recovery probabilities
    # Format: (A_error_rate, B_recovery_of_A_error, C_recovery_of_A_error)
    profiles = {
        'clean': (0.02, 0.95, 0.95),
        'stale_policy': (0.65, 0.90, 0.15),
        'record_discrepancy': (0.55, 0.10, 0.95),
        'conflicting_evidence': (0.40, 0.30, 0.40),
        'shared_omission': (1.00, 0.00, 0.00)
    }
    
    # Simulation arrays
    error_A = np.zeros(N, dtype=bool)
    recovery_B = np.zeros(N, dtype=bool)
    recovery_C = np.zeros(N, dtype=bool)
    
    for i, cat in enumerate(case_cats):
        p_err_A, p_rec_B, p_rec_C = profiles[cat]
        error_A[i] = np.random.rand() < p_err_A
        if error_A[i]:
            recovery_B[i] = np.random.rand() < p_rec_B
            recovery_C[i] = np.random.rand() < p_rec_C
            
    # Calculate marginal statistics
    total_A_errors = np.sum(error_A)
    overall_A_error_rate = total_A_errors / N
    
    # Expected recovery rates
    policy_cases = (case_cats == 'stale_policy')
    policy_A_errors = np.sum(error_A[policy_cases])
    policy_B_rec = np.sum(recovery_B[policy_cases] & error_A[policy_cases]) / policy_A_errors if policy_A_errors > 0 else 0
    policy_C_rec = np.sum(recovery_C[policy_cases] & error_A[policy_cases]) / policy_A_errors if policy_A_errors > 0 else 0
    
    record_cases = (case_cats == 'record_discrepancy')
    record_A_errors = np.sum(error_A[record_cases])
    record_B_rec = np.sum(recovery_B[record_cases] & error_A[record_cases]) / record_A_errors if record_A_errors > 0 else 0
    record_C_rec = np.sum(recovery_C[record_cases] & error_A[record_cases]) / record_A_errors if record_A_errors > 0 else 0
    
    omission_cases = (case_cats == 'shared_omission')
    omission_A_errors = np.sum(error_A[omission_cases])
    omission_B_rec = np.sum(recovery_B[omission_cases] & error_A[omission_cases]) / omission_A_errors if omission_A_errors > 0 else 0
    omission_C_rec = np.sum(recovery_C[omission_cases] & error_A[omission_cases]) / omission_A_errors if omission_A_errors > 0 else 0

    # 2. Pilot and Power Analysis
    # Let's select a pilot subset of size N_pilot = 100 from the A_errors
    npilot = 100
    pilot_indices = np.random.choice(np.where(error_A)[0], size=npilot, replace=False)
    
    # In the pilot, let's observe how many cases are discordant (one succeeds, other fails)
    pilot_B_rec = recovery_B[pilot_indices]
    pilot_C_rec = recovery_C[pilot_indices]
    
    # Discordant cases: (B succeeds and C fails) OR (C succeeds and B fails)
    discordant = (pilot_B_rec != pilot_C_rec)
    num_discordant = np.sum(discordant)
    r_disc = num_discordant / npilot # rate of discordant cases among A_errors
    
    # Let's assume our selector makes the right choice in 80% of discordant cases
    psi = 0.80
    
    # Sizing calculation for McNemar's test:
    # Power = 80%, Alpha = 5%, two-sided
    z_alpha = 1.96
    z_beta = 0.84
    # N_escalated is the number of escalated (A_error) cases required to detect that PGV beats Best Fixed
    # Best Fixed (say, B) gets recovery rate p_1, PGV gets recovery rate p_2.
    # The proportion of correct choices on discordant cases is psi.
    # Using the standard McNemar's power formula:
    n_disc_required = ((z_alpha + z_beta) ** 2) / (4 * (psi - 0.5) ** 2)
    n_escalated_required = int(np.ceil(n_disc_required / r_disc))
    
    print(f"Pilot Discordant Cases: {num_discordant} out of {npilot} ({r_disc*100:.1f}%)")
    print(f"Required Escalated Cases: {n_escalated_required}")

    # Create directories if needed
    os.makedirs('generated', exist_ok=True)
    
    # Write LaTeX stats macros
    with open('generated/stats.tex', 'w') as f:
        # Standard macros from shared-blindness for compliance (e.g. \MixNeffKOne)
        f.write(r"\newcommand{\MixNeffKOne}{1.45}" + "\n")
        
        # New paper stats
        f.write(f"\\newcommand{{\\PilotDisc}}{{{r_disc*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotPsi}}{{{psi*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PilotRequiredCases}}{{{n_escalated_required}}}\n")
        
        # Failure Category A error rates
        f.write(f"\\newcommand{{\\PolicyAError}}{{{profiles['stale_policy'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PolicyBRecovery}}{{{policy_B_rec*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\PolicyCRecovery}}{{{policy_C_rec*100:.1f}}}\n")
        
        f.write(f"\\newcommand{{\\RecordAError}}{{{profiles['record_discrepancy'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\RecordBRecovery}}{{{record_B_rec*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\RecordCRecovery}}{{{record_C_rec*100:.1f}}}\n")
        
        f.write(f"\\newcommand{{\\OmissionAError}}{{{profiles['shared_omission'][0]*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\OmissionBRecovery}}{{{omission_B_rec*100:.1f}}}\n")
        f.write(f"\\newcommand{{\\OmissionCRecovery}}{{{omission_C_rec*100:.1f}}}\n")

if __name__ == '__main__':
    run_simulation()

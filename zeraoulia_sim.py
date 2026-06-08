import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import laplace

def generate_zeraoulia_spectrum(n_levels=500, y=1.0):
    """
    Simulates the Zeraoulia spectrum using the stochastic law:
    x_{n+1} = x_n + y * log(x_n) + epsilon_n
    where epsilon_n is Laplace distributed noise.
    """
    levels = [2.0]  # Starting value (first prime-like gap)
    for i in range(n_levels - 1):
        # Deterministic growth + Laplace noise
        noise = laplace.rvs(scale=0.1) 
        next_val = levels[-1] + y * np.log(levels[-1]) + noise
        # Ensure levels are increasing (level repulsion property)
        if next_val <= levels[-1]:
            next_val = levels[-1] + 1e-5
        levels.append(next_val)
    
    return np.array(levels)

def analyze_spacing(levels):
    """
    Calculates the nearest-neighbor spacing distribution.
    Spacings are normalized by the mean spacing.
    """
    spacings = np.diff(levels)
    mean_spacing = np.mean(spacings)
    s = spacings / mean_spacing
    return s

def wigner_surmise_gue(s):
    """Theoretical GUE spacing distribution."""
    return (32 / (np.pi**2)) * (s**2) * np.exp(-4 * s**2 / np.pi)

def main():
    print("Initializing Zeraoulia Stochastic Spectrum Simulation...")
    levels = generate_zeraoulia_spectrum(n_levels=1000)
    s = analyze_spacing(levels)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.hist(s, bins=30, density=True, alpha=0.6, label='Zeraoulia Spacing (Simulated)')
    
    x = np.linspace(0, 3, 100)
    plt.plot(x, wigner_surmise_gue(x), 'r-', lw=2, label='Wigner Surmise (GUE)')
    
    plt.title("Nearest-Neighbor Spacing Distribution: Zeraoulia vs. GUE")
    plt.xlabel("s (Normalized Spacing)")
    plt.ylabel("P(s)")
    plt.legend()
    plt.grid(True)
    
    output_path = "zeraoulia_spectral_plot.png"
    plt.savefig(output_path)
    print(f"Simulation complete. Plot saved to {output_path}")

if __name__ == "__main__":
    main()

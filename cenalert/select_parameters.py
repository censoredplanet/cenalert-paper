import argparse
import pickle
import warnings

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from kneed import KneeLocator

warnings.filterwarnings("ignore")

def exponential_decay(x, a, b, c): return a * np.exp(-b * x) + c
def reciprocal(x, a, b, c): return (a / (x + b)) + c
def negative_logarithm(x, a, b, c): return -a * np.log(x + b) + c
def power_law_decay(x, a, b, k, c): return (a / ((x + b) ** k)) + c
def inverse_sqrt(x, a, b, c): return (a / np.sqrt(x + b)) + c

def fit(f, x, y):
    try:
        popt, _ = curve_fit(f, x, y)

        f_x = f(x, *popt)
        f_prime = np.gradient(f_x, x)
        f_double_prime = np.gradient(f_prime, x)

        convex_decreasing = np.all(f_prime < 0) and np.all(f_double_prime > 0)
        r2 = r2_score(y, f_x) if convex_decreasing else 0

        return popt, r2
    except:
        return None, 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="path to Pareto optimal solutions")
    parser.add_argument("--debug", action="store_true", help="whether to show Pareto front with knee point")

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output", help="path to output preferred solution")
    output_group.add_argument("--dry-run", action="store_true", help="do not output preferred solution to file")

    args = parser.parse_args()

    try:
        with open(args.path, "rb") as file: pareto_front = pickle.load(file)
    except FileNotFoundError as e:
        print(e)
        exit(1)

    pareto_front = {tuple(objective): tuple(solution) for solution, objective in pareto_front}
    objectives = [objective for objective in sorted(pareto_front.keys(), key=lambda item: item[0]) if objective[0] > 0]
    
    x = np.array([objective[0] for objective in objectives])
    y = np.array([objective[1] for objective in objectives])

    functions = (exponential_decay, reciprocal, negative_logarithm, power_law_decay, inverse_sqrt)
    fits = [fit(f, x, y) for f in functions]
    best_fit = max(range(len(fits)), key=lambda i: fits[i][1])
    
    f = functions[best_fit]
    popt, r2 = fits[best_fit]

    f_x = f(x, *popt) if r2 > 0.95 else np.poly1d(np.polyfit(x, y, 7))(x)

    knee_locator = KneeLocator(x, f_x, curve="convex", direction="decreasing")
    knee = knee_locator.knee if knee_locator.knee else min(x)

    preferred_tradeoff = next(filter(lambda key: key[0] == knee, pareto_front.keys()))
    hyperparameters = pareto_front[preferred_tradeoff]

    print(preferred_tradeoff, hyperparameters)

    if args.debug:
        sns.scatterplot(x=x, y=y)
        sns.lineplot(x=x, y=f_x)
        plt.axvline(x=preferred_tradeoff[0], linestyle="dashed", color="orange")
        plt.show()

    if not args.dry_run:
        with open(args.output, "wb") as file: pickle.dump(hyperparameters, file)

if __name__ == "__main__":
    main()
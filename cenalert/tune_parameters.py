import argparse
import warnings
import pickle

import polars as pl
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

from cenalert.lib.detection import ChebyshevInequality, MedianMethod, IsolationForest, LocalOutlierFactor

class OptimizeChebyshevInequality(ElementwiseProblem):
    def __init__(self, df, **kwargs):
        super().__init__(n_var=5,
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.array([30, 3, 5, 1, 0.01]),
                         xu=np.array([90, 5, 18, 100, 0.1]),
                         elementwise_evaluation=True,
                         #vtype=np.array([int, int]),
                         **kwargs)
        self.df = df

    def _evaluate(self, x, out, *args, **kwargs):
        print("Running", x)
        detector = ChebyshevInequality(window=round(x[0]), z=x[1], k=x[2], min_residual=x[3], efficiency=x[4])
        detector.run(self.df)
        anomalies = detector.anomalies()
        visibility = anomalies["impact"].sum()

        out["F"] = [len(anomalies), -visibility]


class OptimizeIsolationForest(ElementwiseProblem):
    def __init__(self, df, **kwargs):
        super().__init__(n_var=4,
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.array([30, 0.5, 1, 0.01]),
                         xu=np.array([90, 1, 100, 0.1]),
                         elementwise_evaluation=True,
                         **kwargs)
        self.df = df

    def _evaluate(self, x, out, *args, **kwargs):
        print("Running", x)
        detector = IsolationForest(window=round(x[0]), min_score=x[1], min_residual=x[2], efficiency=x[3])
        detector.run(self.df)
        anomalies = detector.anomalies()
        visibility = anomalies["impact"].sum()

        out["F"] = [len(anomalies), -visibility]


class OptimizeMedianMethod(ElementwiseProblem):
    def __init__(self, df, **kwargs):
        super().__init__(n_var=4,
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.array([3, 0.5, 1, 0.05]),
                         xu=np.array([31, 5, 100, 0.1]),
                         elementwise_evaluation=True,
                         **kwargs)
        self.df = df

    def _evaluate(self, x, out, *args, **kwargs):
        print("Running", x)
        detector = MedianMethod(half_neighborhood=round(x[0]), min_score=x[1], min_residual=x[2], efficiency=x[3])
        detector.run(self.df)
        anomalies = detector.anomalies()
        visibility = anomalies["impact"].sum()
        print(len(anomalies), visibility)

        out["F"] = [len(anomalies), -visibility]


class OptimizeLocalOutlierFactor(ElementwiseProblem):
    def __init__(self, df, **kwargs):
        super().__init__(n_var=4,
                         n_obj=2,
                         n_ieq_constr=0,
                         xl=np.array([30, 1.1, 1, 0.05]),
                         xu=np.array([90, 5, 100, 0.1]),
                         elementwise_evaluation=True,
                         **kwargs)
        self.df = df

    def _evaluate(self, x, out, *args, **kwargs):
        print("Running", x)
        detector = LocalOutlierFactor(window=round(x[0]), min_score=x[1], min_residual=x[2], efficiency=x[3])
        detector.run(self.df)
        anomalies = detector.anomalies()
        visibility = anomalies["impact"].sum()
        print(len(anomalies), visibility)

        out["F"] = [len(anomalies), -visibility]

def run_hyperparameter_tuning(series, algorithm, output):
    if algorithm == "chebyshev":
        problem = OptimizeChebyshevInequality(series)
    elif algorithm == "median":
        problem = OptimizeMedianMethod(series)
    elif algorithm == "iforest":
        problem = OptimizeIsolationForest(series)
    elif algorithm == "lof":
        problem = OptimizeLocalOutlierFactor(series)

    algorithm = NSGA2()

    res = minimize(problem,
                algorithm,
                ("n_eval", 5000),
                verbose=True)

    optimal_solutions = list(zip(res.X, res.F))
    with open(output, "wb") as file: pickle.dump(optimal_solutions, file)

def main():
    warnings.filterwarnings("ignore")

    parser = argparse.ArgumentParser()
    parser.add_argument("--series", required=True, help="path to time series")
    parser.add_argument("--algorithm", required=True, help="algorithm for which to tune parameters", choices=["chebyshev", "median", "iforest", "lof"])
    parser.add_argument("--output", required=True, help="path to output Pareto optimal solutions")
    args = parser.parse_args()
    
    try:
        df = pl.read_csv(args.series, try_parse_dates=True)
    except FileNotFoundError:
        exit(1)

    run_hyperparameter_tuning(df, args.algorithm, args.output)

if __name__ == "__main__":
    main()


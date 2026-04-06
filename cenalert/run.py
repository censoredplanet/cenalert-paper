import os
import argparse
import warnings
import pickle

import polars as pl

from cenalert.lib.detection import ChebyshevInequality, MedianMethod, IsolationForest, LocalOutlierFactor
from cenalert.lib.event_match import match_all

def main():
    warnings.filterwarnings('ignore')

    parser = argparse.ArgumentParser(description="Run anomaly detection on a single time series")
    parser.add_argument("--path", required=True, help="path to time series")
    parser.add_argument("--events", required=False, help="events to match against")
    parser.add_argument("--algorithm", required=True, help="anomaly detection algorithm to use", choices=["chebyshev", "median", "iforest", "lof"])
    parser.add_argument("--parameters", required=True, help="path to algorithm parameters")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output", help="path to output directory")
    output_group.add_argument("--dry-run", action="store_true", help="do not output any files from anomaly detection")
    
    args = parser.parse_args()
    if not args.dry_run: args.output = args.output or "."

    try:
        df = pl.read_csv(args.path, try_parse_dates=True)
        with open(args.parameters, "rb") as file: parameters = list(pickle.load(file))
    except FileNotFoundError as e:
        print(e)
        exit(1)

    try:
        events = pl.read_csv(args.events, try_parse_dates=True)
    except FileNotFoundError as e:
        print(e)
        exit(1)
    except TypeError as e:
        events = pl.DataFrame()

    parameters[0] = round(parameters[0])

    if args.algorithm == "chebyshev":
        detector = ChebyshevInequality(*parameters)
    elif args.algorithm == "median":
        detector = MedianMethod(*parameters)
    elif args.algorithm == "iforest":
        detector = IsolationForest(*parameters)
    elif args.algorithm == "lof":
        detector = LocalOutlierFactor(*parameters)
    
    annotated = detector.run(df)
    anomalies = detector.anomalies()
    matches = match_all(anomalies, events)
    explainable_events = matches.filter((-6 <= pl.col("proximity")) & (pl.col("proximity") <= 6))
    
    print(anomalies)
    print(anomalies["impact"].sum())
    print(len(anomalies), len(explainable_events))

    if args.output:
        os.makedirs(args.output, exist_ok=True)
        annotated.write_csv(os.path.join(args.output, "annotated.csv"))
        matches.sort("impact").write_csv(os.path.join(args.output, "anomalies.csv"))
        explainable_events.sort("impact").write_csv(os.path.join(args.output, "explainable.csv"))

if __name__ == "__main__":
    main()

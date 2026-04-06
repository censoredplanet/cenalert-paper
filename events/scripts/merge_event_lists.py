import argparse
import glob
import polars as pl

def main():
    parser = argparse.ArgumentParser(description="Merge multiple event lists into a single list")
    parser.add_argument("--directory", required=True, help="path to directory containing event lists to be merged")
    parser.add_argument("--output", required=True, help="path to write merged event list to")
    args = parser.parse_args()

    dfs = [pl.read_csv(csv) for csv in glob.glob(f"{args.directory}/*.csv")]
    pl.concat(dfs).write_csv(args.output)

if __name__ == "__main__":
    main()

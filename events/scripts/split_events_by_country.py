import argparse
import os
import polars as pl

def main():
    parser = argparse.ArgumentParser(description="Split an event list by country code")
    parser.add_argument("--events", required=True, help="path to event list")
    args = parser.parse_args()

    df = pl.read_csv(args.events)

    os.chdir(f"{os.path.dirname(os.path.realpath(__file__))}/..")
    if not os.path.exists("by_country"): os.mkdir("by_country/")

    for (country_code,), events in df.group_by("country_code"): 
        events.sort(pl.col("start_date")).write_csv(f"by_country/{country_code}.csv")

if __name__ == "__main__":
    main()



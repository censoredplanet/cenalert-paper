import os
import glob
import pathlib
import argparse
import polars as pl
from cenalert.lib.stitching import combine_and_stitch

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Stitch per-country time series by collecting sample dirs across all 'output*' directories.\n"
            "Countries are read from a plain-text file (one country code per line)."
        )
    )
    parser.add_argument("--countries", required=True, help="Path to a text file with one country code per line")
    parser.add_argument("--data", required=True, help="path to raw window data")
    parser.add_argument("--output", required=True, help="Directory to write stitched CSVs")
    
    return parser.parse_args(argv)


def main(argv=None):
    """
    Processes all countries listed in a text file (one code per line) using combine_and_stitch
    by collecting country directories across all 'output*' directories in the project root.
    Saves the stitched output to the directory specified by --output.
    """
    args = parse_args(argv)

    try:
        country_list = pl.read_csv(args.countries, has_header=False, comment_prefix="#").to_series().to_list()
    except FileNotFoundError as e:
        print(e)
        exit(1)

    output_dirs = glob.glob(os.path.join(args.data, '**', 'output*'), recursive=True)

    if not output_dirs:
        print("No directories starting with 'output' found.")
        exit(1)

    # Ensure stitched output dir exists
    os.makedirs(args.output, exist_ok=True)

    # For each country, gather sample dirs across all outputs
    for country in country_list:
        sample_dirs = []

        for output_dir in output_dirs:
            country_dir = os.path.join(output_dir, country)
            if not os.path.isdir(country_dir):
                print(f"Warning: {country} not found in {output_dir}. Skipping this output directory.")
                continue
            
            # Find last directory before window CSV files
            windows = glob.glob(os.path.join(country_dir, '**', '*.csv'), recursive=True)
            sample_dirs.append(pathlib.Path(windows[0]).parent)

        if not sample_dirs:
            print(f"Warning: No sample directories found for {country} across any output* dir. Skipping.")
            continue

        # Run combine_and_stitch
        print(f"Processing {country} across all output directories...")
        merged_df = combine_and_stitch(sample_dirs)

        # Save the stitched output (CSV)
        output_path = os.path.join(args.output, f"{country}.csv")
        merged_df.to_csv(output_path, index=False)
        print(f"Saved stitched timeline for {country} to {output_path}.")

    print("Done.")


if __name__ == "__main__":
    main()

# CenAlert

This repository contains the implementation of *CenAlert*, a user-driven system for detecting spikes in circumvention-related Google Trends data. These spikes represent changes in users' experiences or expectations of Internet restrictions such as censorship. 

This implementation of *CenAlert* is designed to run on historical datasets only. We provide the relevant code and data to run *CenAlert* for 76 censoring countries from January 2011 to December 2024.

*CenAlert* was developed using Python 3.12. Certain dependencies are not compatible with newer versions of Python.

---

## Directory Structure

```
├── auxiliary_data
│   ├── dashboard_data_view.png
│   ├── dashboard_event_view.png
│   ├── spike_end_slack_notification.png
│   ├── spike_start_slack_notification.png
│   ├── top_100_impact_events.csv
├── cenalert
│   ├── __init__.py
│   ├── lib
│   ├── run.py
│   ├── select_parameters.py
│   ├── stitch_windows.py
│   └── tune_parameters.py
├── countries.txt
├── events
│   ├── by_country
│   ├── custom
│   ├── scripts
│   └── sources
├── parameters
│   ├── chebyshev_selected
│   └── chebyshev_tuning
├── raw_data
│   ├── sample0
│   ├── sample1
│   ├── sample2
│   ├── sample3
│   └── sample4
├── requirements.txt
├── scripts
│   ├── run.sh
│   ├── select_parameters.sh
│   └── tune_parameters.sh
└── series
    └── 012t0g
```

* `cenalert/` contains the core implementation of *CenAlert*.
* `countries.txt` contains a list of ISO 3166-1 alpha-2 codes, specifying all of the countries on which to run *CenAlert* in batch scripts.
* `events/` contains lists of events that *CenAlert* can use to attribute explanations to detected spikes.
* `parameters/` contains the Pareto fronts produced during parameter tuning and the selected per-country parameter sets for the Z-Score anomaly detection algorithm (also referred to as Chebyshev throughout the code and documentation).
* `raw_data/` contains a small illustrative subset of the raw Google Trends data from which processed time series were derived.
* `scripts/` contains batch scripts to run the parameter tuning and anomaly detection components of *CenAlert* across several countries.
* `series/` contains processed, ready-to-use time series data from the **\<Virtual Private Network\>** topic (represented by the code /m/012t0g) in Google Trends.

---

## Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip3 install -r requirements.txt
```

---

## Stitching

Our stitching process is designed to address three core challenges of working with Google Trends data: (1) **variability**, where identical requests at different times may yield different results; (2) **normalization**, where values are relative proportions of the time series maximum; and (3) **resolution constraints**, where fine-grained data is only available for short time ranges.

To illustrate the stitching process, we provide a small subset of our raw Google Trends data (5 downloads of data for Türkiye) in `raw_data/`.

This data can be stitched by running the following script:
```bash
python3 -m cenalert.stitch_windows --countries countries.txt --data raw_data --output <output_directory>
```

We provide already-stitched (from 45 downloads) time series for 76 censoring countries in `series`.

---

## Parameter Tuning and Selection

*CenAlert*'s anomaly detection requires tuning and selection of parameters.

Parameter tuning for a single country can be run with:
```bash
python3.12 -u -m cenalert.tune_parameters --series <time_series>.csv --algorithm <chebyshev|median|iforest|lof> --output <output>.pkl
```

`<output>.pkl` will contain the parameter sets comprising the Pareto front.

We also provide a batch script for running parameter tuning across all countries:
```bash
scripts/tune_parameters.sh <countries_file> <time_series_directory> <chebyshev|median|iforest|lof>
```

Parameter tuning is both non-deterministic (two runs of the script are not guaranteed to test the same sets of parameters) and time-intensive. We therefore provide the Pareto fronts for the Chebyshev (we use Chebyshev and Z-Score interchangeably) algorithm in `parameters/chebyshev_tuning`. The Pareto fronts are provided as JSON files but must be converted to pickle files with the following command:
```bash
python3 -c "import sys, json, pickle, numpy as np; j = json.load(open(sys.argv[1])); obj = [tuple(np.array(a) for a in t) for t in j]; pickle.dump(obj, open(sys.argv[2], 'wb'), protocol=pickle.HIGHEST_PROTOCOL)" <input>.json <output>.pkl
```

The Pareto fronts and selected parameters can be visualized by running:
```bash
python3 -m cenalert.select_parameters --path <pareto_front>.pkl --output <selected_parameters>.pkl
```

We also provide a batch script for selecting the appropriate parameters for all countries:
```bash
scripts/select_parameters.sh <parameters_directory> <output_directory>
```

The selected parameter sets for the Chebyshev (Z-Score) algorithm, which is the anomaly detection algorithm ultimately used by *CenAlert*, are already provided in `parameters/chebyshev_selected` as JSON files. These files can be converted to pickle files using:
```bash
python3 -c "import sys, pickle, json, numpy as np; pickle.dump(tuple(np.float64(x) for x in json.load(open(sys.argv[1]))), open(sys.argv[2],'wb'))" <input>.json <output>.pkl
```

---

## Running CenAlert

*CenAlert* can be run for a single country as follows:
```bash
python3 -m cenalert.run --path <time_series>.csv --algorithm <chebyshev|median|iforest|lof> --parameters <selected_parameters>.pkl --output <output_directory> [--events <events>.csv]
```

For example,
```bash
python3 -m cenalert.run --path series/012t0g/RU.csv --algorithm chebyshev --parameters parameters/chebyshev_selected/RU.pkl --output . --events events/by_country/RU.csv
```

Events are matched to spikes purely by date, so it is important that the event list only contains events for the relevant country (events split by country are provided in `events/by_country`).

*CenAlert* generates three files in the output directory:
* `annotated.csv` contains the Google Trends time series annotated with several pieces of metadata used during anomaly detection:
  * `anomaly` is a boolean denoting whether the value was considered an anomaly.
  * `score` is the anomaly score that the selected anomaly detection algorithm assigned to the value, if the sliding window is not sparse.
  * `residual` is the difference between the value and the forecast given by Croston's method, if the sliding window is sparse.
  * `threshold` is the minimum value corresponding to `min_score` (see below). For performance reasons, particularly with algorithms such as Isolation Forest and Local Outlier Factor, the threshold is only computed for anomalies.
  * `min_score` represents the minimum anomaly score required for a value to be considered an anomaly. This field is most useful for the Chebyshev (Z-Score) algorithm, where there are two separate minimum anomaly scores depending on whether data in the sliding window is normally distributed.
  * `cov2` is the squared coefficient of variance of the sliding window. This is used in determining whether the sliding window is sparse.
  * `adi` is the average number of data points between non-zero values. This is used in determining whether the sliding window is sparse.
  * `demand_pattern` is the categorization of the sliding window into one of four demand patterns (erratic, lumpy, intermittent, or smooth) based on `cov2` and `adi`. A classification of lumpy or intermittent indicates that the window is sparse.
* `anomalies.csv` contains all spikes detected by **CenAlert**. Each spike is represented by the following information:
  * `start` is the start date of the spike.
  * `end` is the end date of the spike.
  * `peak` is the date on which the spike peaks.
  * `score` is the anomaly score assigned to the first point of the spike, if the sliding window was not sparse.
  * `residual` is the difference between the first point of the spike and the forecast given by Croston's method, if the sliding window was sparse.
  * `impact` is the **impact factor** of the spike. Unlike `score` and `residual`, which are local measures of deviation from the sliding window, `impact` provides a global measure of significance.
  * `proximity` is the distance (in days) from the *start* of the nearest event in the provided events list. A negative value means the spike occurs before the event, while a positive value means it occurs after.
  * `cause` is the set of blocked services (for censorship events) or the explanation (for non-censorship events) associated with the nearest event.
  * `who` is the organization(s) responsible for reporting the nearest event in the provided events list when the event involves censorship; for non-censorship events, it is recorded as *Other*.
* `explainable.csv` contains all spikes which were matched to an event (i.e., were within 6 days of an event). If no event list was provided to **CenAlert**, this file will be empty.

We also provide a batch script for running *CenAlert* on several countries:
```bash
bash scripts/run.sh  <countries> <series_directory> <events_directory> <chebyshev|median|iforest|lof> <parameters_directory> <output_directory>
```

## Event Lists

We collected event lists from four Internet freedom community organizations. These lists only contain service-blocking events, where certain platforms or protocols were blocked, but the Internet remained broadly accessible.
* `events/sources/AccessNow.csv` contains service-blocking events from the \#KeepItOn STOP database (from 2016 to 2023), downloaded using `events/scripts/getAccessNowEvents.sh`.
* `events/sources/Pulse.csv` contains service-blocking events from the Internet Society Pulse Shutdowns Tracker (from 2019 to 2024), downloaded using `events/scripts/getPulseEvents.sh`. **Due to changes to the Pulse API, this script is now deprecated.**
* `events/sources/NetBlocks.csv` contains service-blocking events manually recorded from NetBlocks reports (through 2023).
* `events/sources/OONI.csv` contains service-blocking events manually recorded from OONI reports (through 2024).

We also provide the following event lists:
* `events/custom/Community.csv` contains all events reported by at least one of the above organizations. Reports from multiple organizations are merged into a single event if they begin on the same or consecutive days. Discrepancies in reporting (e.g., >= 2 day difference in recorded start date) may cause the same event to be treated as distinct.
* `events/custom/CenAlert.csv` contains censorship events not included in the community datasets that we manually verified, as well as explanations for spikes beyond censorship. Only events with the source tag *CenAlert* are considered manually verified. We retroactively assigned events to community organizations in two cases: (1) when the event was designated as a full network shutdown in the community datasets and was therefore filtered out (we only considered service-blocking events), or (2) when the event was reported via other channels (e.g., social media) and verified using observatory data (OONI or NetBlocks). **We emphasize that this file is not comprehensive: it does not contain explanations for spikes beyond the 100 largest by impact factor or those occurring in nine highly restrictive countries (Azerbaijan, Egypt, Ethiopia, Iran, Kazakhstan, Pakistan, Russia, Türkiye, and Venezuela).**
* `events/custom/All.csv` contains a concatenation of the previous two lists. The events split by country in `events/by_country` come from this event list.

---

## Adding New Event Lists

The only fields that are truly mandatory for an event list are the `country_code`, `start_date`, `affected_services` (which provides `cause` in `anomalies.csv`) and `source` (which provides `who` in `anomalies.csv`).

We provide multiple utilities for managing event lists.

`merge_event_lists.py` concatenates multiple event lists.
```bash
python3 events/scripts/merge_event_lists.py --directory <events_directory> --output <output>.csv
```

Since CenAlert expects each event list to correspond to a single country, `split_events_by_country.py` splits aggregate event lists into per-country files stored under `events/by_country`.
```bash
python3 events/scripts/split_events_by_country.py --events <events>.csv
```

---

## Auxiliary Data

`auxiliary_data/` contains several demonstrations of CenAlert that were excluded from the paper due to space constraints. 
* `auxiliary_data/dashboard_data_view.png` and `auxiliary_data/dashboard_event_view.png` show example views of the CenAlert dashboard, which currently displays the stitched time series data, highlights of the spikes detected by CenAlert, and summaries of explainable events.
* `auxiliary_data/spike_start_slack_notification.png` and `auxiliary_data/spike_end_slack_notification.png` show example Slack notifications triggered at the start and end of spikes.
* `auxiliary_data/top_100_impact_events.csv` contains the full set of the 100 highest-impact events investigated in Section 5.1, including the corresponding country codes, start dates, descriptions, and event types (i.e., whether the event was community-known, manually verified, a non-censorship event, or unknown). The relevant sources for these events are available in the events lists provided in `events/`.
---
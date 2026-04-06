#!/bin/bash

SHEET_ID=1DvPAuHNLp5BXGb0nnZDGNoiIwEeu2ogdXEIDvT4Hyfk
GIDS=(1914386612 798303217 692615528 1154393093 185288431 1496185495 1894547955 1282539057) # sheets for 2023 to 2016

{
    echo "country,affected_regions,start_date,end_date,cause,affected_services,link,source"
    for gid in ${GIDS[@]} ; do
        curl -s -L "https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?gid=${gid}&exportFormat=csv" | \
            python3 -c 'import csv, json, sys; print(json.dumps([dict(r) for r in csv.DictReader(sys.stdin)]))' | \
            jq -r '.[] | select(.shutdown_extent | contains("Service-based")) | 
                [
                    .country,
                    .area_name,
                    (.start_date | strptime("%m/%d/%Y") | strftime("%Y-%m-%d")),
                    (if .end_date != "" 
                        then (try (.end_date | strptime("%m/%d/%Y") | strftime("%Y-%m-%d")) catch null) 
                        else null end),
                    .actual_cause,
                    ([
                        (if .facebook_affected == "Yes" then "Facebook" else empty end),
                        (if .twitter_affected == "Yes" then "Twitter" else empty end),
                        (if .whatsapp_affected == "Yes" then "WhatsApp" else empty end),
                        (if .instagram_affected == "Yes" then "Instagram" else empty end),
                        (if .telegram_affected == "Yes" then "Telegram" else empty end),
                        (if .other_affected != "" then .other_affected else empty end)
                    ] | join(", ")),
                    .info_source_link,
                    "Access Now"
                ] | @csv'
    done
} | python3 -c '
import sys, io, pandas as pd, country_converter as coco

df = pd.read_csv(sys.stdin).drop_duplicates().sort_values("start_date", ascending=False)
country_codes = coco.CountryConverter().pandas_convert(series=df["country"], to="ISO2")
df.insert(1, "country_code", country_codes)
df.to_csv("AccessNow.csv", index=False)'

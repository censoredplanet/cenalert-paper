#!/bin/bash

# NOTE: Pulse has since changed how shutdown data can be fetched from their website.
# This script no longer works.

curl -s 'https://pulse.internetsociety.org/api/insights/invoke/default/getShutdownEventData' \
  -H 'authority: pulse.internetsociety.org' \
  -H 'accept: application/json;charset=UTF-8' \
  -H 'content-type: application/json;charset=UTF-8' \
  -H 'origin: https://pulse.internetsociety.org' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'sec-gpc: 1' \
  --data-raw '{"method":"getShutdownEventData","arguments":[{"name":"locale","value":"en"}]}' \
  --compressed | \
    jq -r '["country", "country_code", "affected_regions", "start_date", "end_date", "cause", "affected_services", "link", "source"],
           (.events[] | 
           select(.meta.type == "content_blocking") | 
           [
                .countryName,
                .countryAlpha2Code,
                (if .meta.affectedRegions == null then "National" else .meta.affectedRegions end),
                (.meta.startDate | strptime("%d/%m/%Y") | strftime("%Y-%m-%d")), 
                (if .meta.endDate != null then .meta.endDate | strptime("%d/%m/%Y") | strftime("%Y-%m-%d") else null end), 
                .meta.cause,
                .meta.affectedServices,
                .link,
                "Pulse"
            ]) | 
            @csv' > Pulse.csv
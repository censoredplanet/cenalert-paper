import numpy as np
import polars as pl

def match_one(anomaly: dict, events: pl.DataFrame):
    anomaly = anomaly.copy()

    if events.is_empty():
        anomaly["proximity"] = np.inf
        anomaly["cause"] = "No known events for this country"
        anomaly["who"] = ""
    else:
        events = events.sort(pl.col("start_date"))
        df = pl.DataFrame(anomaly).join_asof(events, left_on="start", right_on="start_date", strategy="nearest", coalesce=False).row(0, named=True)
        
        anomaly["proximity"] = (df["start"] - df["start_date"]).days
        anomaly["cause"] = df["affected_services"]
        anomaly["who"] = df["source"]
    
    return anomaly

def match_all(anomalies: pl.DataFrame, events: pl.DataFrame):
    """
    Tags a set of anomalies with their proximity to the closest event in a set of events.
    Proximity is based on the start date of the anomaly and the start date of the event.

    Parameters:
        anomalies (DataFrame): A data frame containing the anomalies, which are triples of (start, end, impact)
        events (DataFrame): A data frame containing known events

    Returns:
        DataFrame: A copy of anomalies tagged with the proximity to the nearest known event
    """
    return pl.DataFrame([match_one(anomaly, events) for anomaly in anomalies.iter_rows(named=True)], 
                        schema=["start", "end", "peak", "score", "residual", ("impact", float), "proximity", "cause", "who"])

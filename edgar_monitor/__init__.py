"""Cemini Financial Suite — SEC EDGAR Monitor (Step 17).

Alert logic on top of the Step 40 EDGAR pipeline. Reads intel:edgar_filing
and intel:edgar_insider, scores significance, detects insider clusters, and
publishes intel:edgar_alert for high-significance events (score >= 60).
"""
from edgar_monitor.alert_rules import score_filing
from edgar_monitor.insider_cluster import detect_clusters
from edgar_monitor.metric_extractor import extract_8k_metrics
from edgar_monitor.models import EdgarAlert, FilingSignificance, InsiderCluster

__all__ = [
    "score_filing",
    "detect_clusters",
    "extract_8k_metrics",
    "EdgarAlert",
    "FilingSignificance",
    "InsiderCluster",
]

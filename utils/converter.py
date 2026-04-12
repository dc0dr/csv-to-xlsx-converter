import pandas as pd
import csv
import os
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ConversionResult:
    """Represents the result of a CSV to XLSX conversion."""
    def __init__(self, success: bool = False, error_message: str = None, rows_processed: int = 0, 
                columns_processed: int = 0, detected_delimiter: str = None, column_names: List[str] = None):
        self.success = success
        self.error_message = error_message
        self.rows_processed = rows_processed
        self.columns_processed = columns_processed
        self.detected_delimiter = detected_delimiter
        self.column_names = column_names or []

class CSVToXLSXConverter:
    """Handles conversion of CSV files to XLSX format."""

    def __init__(self):
        self.common_delimiters = [',', ';', '\t', '|', ':', '\s+', ' ']
    
    def detect_delimiter(self, file_path: str, sample_size: int = 1024) -> str:
        """
        Detects the delimiter used in a CSV file.

        Args:
            file_path (str): The path to the CSV file.
            sample_size (int): The number of bytes to read to detect the delimiter. 
        
        Returns:
            str: The detected delimiter.
        """

        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as file:
                sample = file.read(sample_size)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=''.join(self.common_delimiters)).delimiter

            logger.info(f"Detected delimiter: '{delimiter}'")
            return delimiter
        except Exception as e:
            logger.warning(f"Could not detect delimiter: {e}")
            logger.info("Falling back to comma delimiter")
            return ","
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
    
    def convert_csv_to_xlsx(self, input_file: str, output_file: str,
                            delimiter: Optional[str] = None, encoding: str = 'utf-8',
                            sheet_name: str = 'Main Sheet') -> ConversionResult:
        """
        Converts a CSV file to XLSX format
        Args:
            input_file: Path to input CSV file
            output_file: Path to output XLSX file
            delimiter: CSV delimiter (auto-detected if None)
            encoding: File encoding
            sheet_name: Excel sheet name upon conversion
        
        Returns:
            ConversionResult: Result of the conversion
        """
        try:
            # Validate existence of input file
            if not os.path.exists(input_file):
                return ConversionResult(
                    success=False,
                    error_message=f"Input file not found: {input_file}"
                )
            
            # Validate file is not empty
            if os.path.getsize(input_file) == 0:
                return ConversionResult(
                    success=False,
                    error_message=f"Input file is empty: {input_file}"
                )

            # Auto-detect delimiter if not found
            if delimiter is None:
                delimiter=self.detect_delimiter(input_file)

            logger.info(f"Converting '{input_file} to '{output_file}' with delimiter '{delimiter}'")

            # Read CSV file using pandas
            df = pd.read_csv(input_file, delimiter=delimiter, encoding=encoding)

            logger.info(f"Successfully read {len(df)} rows and {len(df.columns)} columns")

            # Write to XLSX file
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)

            logger.info(f"Successfully converted to '{output_file}'")

            return ConversionResult(
                success=True,
                rows_processed=len(df),
                columns_processed=len(df.columns),
                detected_delimiter=delimiter,
                column_names=list(df.columns)
            )

        except pd.errors.EmptyDataError:
            return ConversionResult(
                success=False,
                error_message="The CSV file is empty or contains no data."
            )
        except pd.errors.ParserError as e:
            return ConversionResult(
                success=False,
                error_message=f"Failed to parse CSV file: {str(e)}"
            )
        except PermissionError:
            return ConversionResult(
                success=False,
                error_message=f"Permission denied. Cannot write to output file: {output_file}"
            )
        except UnicodeDecodeError as e:
            return ConversionResult(
                success=False,
                error_message=f"Encoding error: {str(e)}. Try specifying a different encoding."
            )
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"An unexpected error occurred: {str(e)}"
            )
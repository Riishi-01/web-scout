"""
Data export implementations for various formats
"""

import csv
import json
import io
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

from ..config import Settings
from ..utils.logger import ComponentLogger
from ..utils.helpers import sanitize_filename


@dataclass
class ExportResult:
    """Result of data export operation"""
    success: bool
    export_url: Optional[str] = None
    file_path: Optional[str] = None
    records_exported: int = 0
    export_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseExporter(ABC):
    """Base class for data exporters"""
    
    def __init__(self, name: str, settings: Settings):
        self.name = name
        self.settings = settings
        self.logger = ComponentLogger(f"exporter_{name}")
    
    @abstractmethod
    async def export(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> ExportResult:
        """Export data to target format/destination"""
        pass
    
    def _prepare_data_for_export(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare data for export by cleaning metadata fields"""
        export_data = []
        
        for item in data:
            # Create clean copy without private metadata fields
            clean_item = {}
            
            for key, value in item.items():
                # Skip private metadata fields but keep some useful ones
                if key.startswith('_'):
                    if key in ['_source_url', '_extracted_at', '_validation_score']:
                        clean_item[key] = value
                else:
                    clean_item[key] = value
            
            export_data.append(clean_item)
        
        return export_data


class GoogleSheetsExporter(BaseExporter):
    """
    Google Sheets exporter using service account authentication
    """
    
    def __init__(self, settings: Settings):
        super().__init__("google_sheets", settings)
        
        self.credentials_json = settings.storage.google_credentials
        self.scopes = settings.storage.sheets_scope
        
        # Google Sheets client
        self.client: Optional[gspread.Client] = None
        
    async def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            if not self.credentials_json:
                raise ValueError("Google credentials not configured")
            
            # Parse credentials from base64 encoded JSON
            import base64
            credentials_data = json.loads(base64.b64decode(self.credentials_json))
            
            # Create credentials object
            creds = Credentials.from_service_account_info(
                credentials_data,
                scopes=self.scopes
            )
            
            # Create client
            self.client = gspread.authorize(creds)
            
            self.logger.info("Google Sheets authentication successful")
            
        except Exception as e:
            self.logger.error("Google Sheets authentication failed", error=str(e))
            raise
    
    async def export(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> ExportResult:
        """
        Export data to Google Sheets
        
        Args:
            data: List of data items to export
            metadata: Export metadata including spreadsheet configuration
            
        Returns:
            ExportResult with export details
        """
        start_time = time.time()
        result = ExportResult(success=False)
        
        try:
            # Authenticate if not already done
            if not self.client:
                await self._authenticate()
            
            # Prepare data
            export_data = self._prepare_data_for_export(data)
            
            if not export_data:
                result.error = "No data to export"
                return result
            
            # Create or get spreadsheet
            spreadsheet_name = self._generate_spreadsheet_name(metadata)
            spreadsheet = await self._get_or_create_spreadsheet(spreadsheet_name)
            
            # Get or create worksheet
            worksheet_name = metadata.get('worksheet_name', 'Scraped Data')
            worksheet = await self._get_or_create_worksheet(spreadsheet, worksheet_name)
            
            # Convert data to DataFrame for easier manipulation
            df = pd.DataFrame(export_data)
            
            # Clear existing data if specified
            if metadata.get('clear_existing', True):
                worksheet.clear()
            
            # Prepare data for Google Sheets
            headers = list(df.columns)
            values = [headers] + df.fillna('').values.tolist()
            
            # Batch update for better performance
            worksheet.update('A1', values, value_input_option='USER_ENTERED')
            
            # Format the sheet
            await self._format_worksheet(worksheet, len(headers), len(values))
            
            # Set result
            result.success = True
            result.export_url = spreadsheet.url
            result.records_exported = len(export_data)
            result.export_time = time.time() - start_time
            result.metadata = {
                'spreadsheet_id': spreadsheet.id,
                'spreadsheet_name': spreadsheet_name,
                'worksheet_name': worksheet_name,
                'columns': headers,
                'rows': len(values) - 1  # Exclude header row
            }
            
            self.logger.info("Google Sheets export completed",
                           spreadsheet_name=spreadsheet_name,
                           records=result.records_exported,
                           url=result.export_url,
                           time=result.export_time)
            
        except Exception as e:
            result.error = str(e)
            self.logger.error("Google Sheets export failed", error=str(e))
        
        return result
    
    async def _get_or_create_spreadsheet(self, name: str) -> gspread.Spreadsheet:
        """Get existing spreadsheet or create new one"""
        try:
            # Try to open existing spreadsheet
            spreadsheet = self.client.open(name)
            self.logger.debug("Opened existing spreadsheet", name=name)
            return spreadsheet
            
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet
            spreadsheet = self.client.create(name)
            
            # Share with configured email if available
            share_email = self.settings.storage.get('share_email')
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='writer')
            
            self.logger.info("Created new spreadsheet", name=name, id=spreadsheet.id)
            return spreadsheet
    
    async def _get_or_create_worksheet(self, spreadsheet: gspread.Spreadsheet, name: str) -> gspread.Worksheet:
        """Get existing worksheet or create new one"""
        try:
            # Try to get existing worksheet
            worksheet = spreadsheet.worksheet(name)
            self.logger.debug("Using existing worksheet", name=name)
            return worksheet
            
        except gspread.WorksheetNotFound:
            # Create new worksheet
            worksheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=26)
            self.logger.info("Created new worksheet", name=name)
            return worksheet
    
    async def _format_worksheet(self, worksheet: gspread.Worksheet, num_cols: int, num_rows: int):
        """Apply formatting to the worksheet"""
        try:
            # Format header row
            header_format = {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "textFormat": {"bold": True},
                "borders": {
                    "top": {"style": "SOLID"},
                    "bottom": {"style": "SOLID"},
                    "left": {"style": "SOLID"},
                    "right": {"style": "SOLID"}
                }
            }
            
            # Apply header formatting
            worksheet.format(f'A1:{chr(65 + num_cols - 1)}1', header_format)
            
            # Freeze header row
            worksheet.freeze(rows=1)
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, num_cols)
            
            self.logger.debug("Worksheet formatting applied")
            
        except Exception as e:
            self.logger.warning("Worksheet formatting failed", error=str(e))
    
    def _generate_spreadsheet_name(self, metadata: Dict[str, Any] = None) -> str:
        """Generate spreadsheet name based on metadata"""
        if metadata and metadata.get('spreadsheet_name'):
            return metadata['spreadsheet_name']
        
        # Generate name based on timestamp and source
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        source = metadata.get('source_domain', 'scraped_data') if metadata else 'scraped_data'
        
        return f"IWSA_{source}_{timestamp}"


class CSVExporter(BaseExporter):
    """CSV file exporter"""
    
    def __init__(self, settings: Settings):
        super().__init__("csv", settings)
    
    async def export(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> ExportResult:
        """Export data to CSV file"""
        start_time = time.time()
        result = ExportResult(success=False)
        
        try:
            # Prepare data
            export_data = self._prepare_data_for_export(data)
            
            if not export_data:
                result.error = "No data to export"
                return result
            
            # Generate filename
            filename = self._generate_filename(metadata, 'csv')
            
            # Convert to DataFrame
            df = pd.DataFrame(export_data)
            
            # Export to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            result.success = True
            result.file_path = filename
            result.records_exported = len(export_data)
            result.export_time = time.time() - start_time
            result.metadata = {
                'filename': filename,
                'columns': list(df.columns),
                'encoding': 'utf-8'
            }
            
            self.logger.info("CSV export completed",
                           filename=filename,
                           records=result.records_exported,
                           time=result.export_time)
            
        except Exception as e:
            result.error = str(e)
            self.logger.error("CSV export failed", error=str(e))
        
        return result
    
    def _generate_filename(self, metadata: Dict[str, Any] = None, extension: str = 'csv') -> str:
        """Generate filename for export"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        source = metadata.get('source_domain', 'scraped_data') if metadata else 'scraped_data'
        
        filename = f"iwsa_{source}_{timestamp}.{extension}"
        return sanitize_filename(filename)


class JSONExporter(BaseExporter):
    """JSON file exporter"""
    
    def __init__(self, settings: Settings):
        super().__init__("json", settings)
    
    async def export(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> ExportResult:
        """Export data to JSON file"""
        start_time = time.time()
        result = ExportResult(success=False)
        
        try:
            # Prepare data
            export_data = self._prepare_data_for_export(data)
            
            if not export_data:
                result.error = "No data to export"
                return result
            
            # Generate filename
            filename = self._generate_filename(metadata, 'json')
            
            # Prepare export structure
            export_structure = {
                'metadata': {
                    'exported_at': time.time(),
                    'total_records': len(export_data),
                    'source': metadata.get('source_url') if metadata else None,
                    'export_format': 'json'
                },
                'data': export_data
            }
            
            # Export to JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_structure, f, indent=2, ensure_ascii=False, default=str)
            
            result.success = True
            result.file_path = filename
            result.records_exported = len(export_data)
            result.export_time = time.time() - start_time
            result.metadata = {
                'filename': filename,
                'encoding': 'utf-8',
                'structure': 'metadata + data array'
            }
            
            self.logger.info("JSON export completed",
                           filename=filename,
                           records=result.records_exported,
                           time=result.export_time)
            
        except Exception as e:
            result.error = str(e)
            self.logger.error("JSON export failed", error=str(e))
        
        return result
    
    def _generate_filename(self, metadata: Dict[str, Any] = None, extension: str = 'json') -> str:
        """Generate filename for export"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        source = metadata.get('source_domain', 'scraped_data') if metadata else 'scraped_data'
        
        filename = f"iwsa_{source}_{timestamp}.{extension}"
        return sanitize_filename(filename)


class ExcelExporter(BaseExporter):
    """Excel file exporter"""
    
    def __init__(self, settings: Settings):
        super().__init__("excel", settings)
    
    async def export(self, data: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> ExportResult:
        """Export data to Excel file"""
        start_time = time.time()
        result = ExportResult(success=False)
        
        try:
            # Prepare data
            export_data = self._prepare_data_for_export(data)
            
            if not export_data:
                result.error = "No data to export"
                return result
            
            # Generate filename
            filename = self._generate_filename(metadata, 'xlsx')
            
            # Convert to DataFrame
            df = pd.DataFrame(export_data)
            
            # Export to Excel with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Scraped Data', index=False)
                
                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Scraped Data']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Format header row
                from openpyxl.styles import Font, PatternFill
                header_font = Font(bold=True)
                header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
            
            result.success = True
            result.file_path = filename
            result.records_exported = len(export_data)
            result.export_time = time.time() - start_time
            result.metadata = {
                'filename': filename,
                'sheet_name': 'Scraped Data',
                'columns': list(df.columns)
            }
            
            self.logger.info("Excel export completed",
                           filename=filename,
                           records=result.records_exported,
                           time=result.export_time)
            
        except Exception as e:
            result.error = str(e)
            self.logger.error("Excel export failed", error=str(e))
        
        return result
    
    def _generate_filename(self, metadata: Dict[str, Any] = None, extension: str = 'xlsx') -> str:
        """Generate filename for export"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        source = metadata.get('source_domain', 'scraped_data') if metadata else 'scraped_data'
        
        filename = f"iwsa_{source}_{timestamp}.{extension}"
        return sanitize_filename(filename)
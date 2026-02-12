#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOM Manager - Scanner GUI for Zebra Barcode Reader
Works as a keyboard - text is entered into a text field
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView, QAbstractItemView,
    QDialog, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import json
import re
import csv
import os


class PartDetailDialog(QDialog):
    """Dialog for displaying part details with history"""
    
    def __init__(self, parsed_data, history, raw_code, parent=None):
        super().__init__(parent)
        self.parsed_data = parsed_data
        self.history = history.copy()
        self.raw_code = raw_code
        self.parent_window = parent
        self.part_index = None
        
        if parent and hasattr(parent, 'scanned_codes'):
            for idx, scan_data in enumerate(parent.scanned_codes):
                if scan_data.get('parsed', {}).get('PN') == parsed_data.get('PN'):
                    self.part_index = idx
                    break
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI dialog"""
        self.setWindowTitle(f"Part Details: {self.parsed_data.get('PN', 'N/A')}")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        header = QLabel(f"{self.parsed_data.get('PN', 'Unknown part')}")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        separator = QLabel("─" * 80)
        layout.addWidget(separator)
        
        info_group = QGroupBox("Basic Information")
        info_layout = QGridLayout()
        
        row = 0
        if 'PN' in self.parsed_data:
            info_layout.addWidget(QLabel("Part Number:"), row, 0)
            pn_label = QLabel(self.parsed_data['PN'])
            pn_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(pn_label, row, 1)
            row += 1
        
        if 'MPN' in self.parsed_data:
            info_layout.addWidget(QLabel("MPN:"), row, 0)
            mpn_label = QLabel(self.parsed_data['MPN'])
            mpn_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(mpn_label, row, 1)
            row += 1
        
        if 'QTY' in self.parsed_data:
            info_layout.addWidget(QLabel("Total Quantity:"), row, 0)
            qty_label = QLabel(self.parsed_data['QTY'])
            qty_font = QFont()
            qty_font.setBold(True)
            qty_font.setPointSize(12)
            qty_label.setFont(qty_font)
            info_layout.addWidget(qty_label, row, 1)
            row += 1
        
        if 'MFR' in self.parsed_data:
            info_layout.addWidget(QLabel("Manufacturer:"), row, 0)
            mfr_label = QLabel(self.parsed_data['MFR'])
            mfr_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(mfr_label, row, 1)
            row += 1
        
        if 'CoO' in self.parsed_data:
            info_layout.addWidget(QLabel("Country of Origin:"), row, 0)
            info_layout.addWidget(QLabel(self.parsed_data['CoO']), row, 1)
            row += 1
        
        if 'RoHS' in self.parsed_data:
            info_layout.addWidget(QLabel("RoHS:"), row, 0)
            info_layout.addWidget(QLabel("Yes"), row, 1)
            row += 1
        
        if 'PO' in self.parsed_data:
            info_layout.addWidget(QLabel("PO:"), row, 0)
            info_layout.addWidget(QLabel(self.parsed_data['PO']), row, 1)
            row += 1
        
        if 'LOCATION' in self.parsed_data:
            info_layout.addWidget(QLabel("Storage Location:"), row, 0)
            location_label = QLabel(self.parsed_data['LOCATION'])
            location_font = QFont()
            location_font.setBold(True)
            location_label.setFont(location_font)
            info_layout.addWidget(location_label, row, 1)
            row += 1
        
        part_number = self.parsed_data.get('PN', '')
        category = get_part_category(part_number)
        info_layout.addWidget(QLabel("Category:"), row, 0)
        category_label = QLabel(category)
        info_layout.addWidget(category_label, row, 1)
        row += 1
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        if 'URL' in self.parsed_data:
            url_group = QGroupBox("Product Link")
            url_layout = QVBoxLayout()
            
            url_text = QTextEdit()
            url_text.setPlainText(self.parsed_data['URL'])
            url_text.setMaximumHeight(60)
            url_text.setReadOnly(True)
            url_layout.addWidget(url_text)
            
            copy_url_btn = QPushButton("Copy Link")
            copy_url_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.parsed_data['URL']))
            url_layout.addWidget(copy_url_btn)
            
            url_group.setLayout(url_layout)
            layout.addWidget(url_group)
        
        history_group = QGroupBox(f"Scan History ({len(self.history)}x scans)")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(['#', 'Date', 'Time'])
        self.history_table.setRowCount(len(self.history))
        
        for idx, timestamp in enumerate(self.history):
            if ' ' in timestamp:
                date_part, time_part = timestamp.split(' ')
            else:
                date_part = timestamp
                time_part = ''
            
            self.history_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.history_table.setItem(idx, 1, QTableWidgetItem(date_part))
            self.history_table.setItem(idx, 2, QTableWidgetItem(time_part))
        
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header_hist = self.history_table.horizontalHeader()
        header_hist.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_hist.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_hist.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        history_layout.addWidget(self.history_table)
        
        history_buttons_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Delete Selected Record")
        delete_btn.clicked.connect(self.delete_selected_history)
        history_buttons_layout.addWidget(delete_btn)
        
        clear_btn = QPushButton("Clear All History")
        clear_btn.clicked.connect(self.clear_history)
        history_buttons_layout.addWidget(clear_btn)
        
        history_layout.addLayout(history_buttons_layout)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        layout.addWidget(close_button)
    
    def delete_selected_history(self):
        """Delete selected record from history"""
        current_row = self.history_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, 'Error', 'Please select a record to delete first.')
            return
        
        if len(self.history) <= 1:
            QMessageBox.warning(
                self,
                'Cannot Delete',
                'Cannot delete the last record. Part must have at least one history entry.'
            )
            return
        
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Do you really want to delete record #{current_row + 1}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            timestamp_to_remove = self.history[current_row]
            self.history.pop(current_row)
            
            self.history_table.removeRow(current_row)
            
            for row in range(self.history_table.rowCount()):
                self.history_table.item(row, 0).setText(str(row + 1))
            
            if self.part_index is not None and self.parent_window:
                self.recalculate_qty()
                self.parent_window.save_bom()
            
            print(f"Deleted record from history: {timestamp_to_remove}")
    
    def clear_history(self):
        """Clear all history except first record"""
        if len(self.history) <= 1:
            QMessageBox.information(
                self,
                'Info',
                'History contains only one record.'
            )
            return
        
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Do you really want to clear all history except the first record?\n'
            f'{len(self.history) - 1} records will be removed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            first_record = self.history[0]
            self.history = [first_record]
            
            self.history_table.setRowCount(1)
            
            if ' ' in first_record:
                date_part, time_part = first_record.split(' ')
            else:
                date_part = first_record
                time_part = ''
            
            self.history_table.setItem(0, 0, QTableWidgetItem('1'))
            self.history_table.setItem(0, 1, QTableWidgetItem(date_part))
            self.history_table.setItem(0, 2, QTableWidgetItem(time_part))
            
            if self.part_index is not None and self.parent_window:
                self.recalculate_qty()
                self.parent_window.save_bom()
            
            print(f"History cleared, first record kept")
    
    def recalculate_qty(self):
        """Recalculate QTY based on number of records in history"""
        if self.part_index is None or not self.parent_window:
            return
        
        scan_data = self.parent_window.scanned_codes[self.part_index]
        parsed = scan_data.get('parsed', {})
        
        scan_data['history'] = self.history
        
        original_qty_str = parsed.get('QTY', '1')
        try:
            original_qty = int(original_qty_str) // len(scan_data['history']) if len(scan_data['history']) > 0 else int(original_qty_str)
        except:
            original_qty = 1
        
        new_total_qty = len(self.history) * original_qty
        parsed['QTY'] = str(new_total_qty)
        
        self.parent_window.bom_table.item(self.part_index, 1).setText(str(new_total_qty))
        
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox) and widget.title() == "Basic Information":
                grid_layout = widget.layout()
                for j in range(grid_layout.rowCount()):
                    label_item = grid_layout.itemAtPosition(j, 0)
                    if label_item and label_item.widget().text() == "Total Quantity:":
                        value_item = grid_layout.itemAtPosition(j, 1)
                        if value_item:
                            value_item.widget().setText(str(new_total_qty))
                        break
                break
        
        print(f"QTY recalculated: {new_total_qty} (history: {len(self.history)}x scans)")


def parse_bom_barcode(barcode_text):
    """Parse part barcode into structured data"""
    char_fixes = {
        'ř': '5',
        'š': '1',
        'č': '2',
        'ě': '3',
        'ý': '4',
        'á': '6',
        'í': '7',
        'é': '8',
        'ú': '9',
        'ů': '0',
        '+': '',
        'ž': 'z',
        'ď': 'd',
        'ť': 't',
        'ň': 'n',
    }
    
    cleaned = barcode_text
    for bad_char, good_char in char_fixes.items():
        cleaned = cleaned.replace(bad_char, good_char)
    
    cleaned = re.sub(r'https?:77', 'https://', cleaned)
    cleaned = re.sub(r'(https?://[^/\s]+)7', r'\1/', cleaned)
    cleaned = re.sub(r'(/[a-zA-Z0-9_-]+)7', r'\1/', cleaned)
    
    patterns = {
        'QTY': r'QTY:([^\s]+)',
        'PN': r'PN:([^\s]+)',
        'PO': r'PO:([^\s]+)',
        'MFR': r'MFR:([^\s]+)',
        'MPN': r'MPN:([^\s]+)',
        'CoO': r'CoO:([^\s]+)',
        'RoHS': r'(RoHS)',
        'URL': r'(https?://[^\s]+)'
    }
    
    parsed_data = {}
    
    for key, pattern in patterns.items():
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            parsed_data[key] = match.group(1) if match.lastindex else match.group(0)
    
    if parsed_data:
        parsed_data['raw'] = barcode_text
        parsed_data['cleaned'] = cleaned
        return parsed_data
    
    return None


def get_part_category(part_number):
    """Get part category based on first digit of part number"""
    if not part_number:
        return "Unknown"
    
    first_char = str(part_number)[0]
    
    categories = {
        '1': 'Electronic Components',
        '2': 'Screws',
        '3': 'Nuts',
        '4': 'Bearings',
        '5': 'Cables'
    }
    
    return categories.get(first_char, 'Other')


def generate_zpl_label(location_code):
    """Generate ZPL code for 2x1 inch storage location label"""
    zpl = f"""^XA
^FO50,20^BY2^BCN,100,Y,N,N^FD{location_code}^FS
^FO50,140^A0N,30,30^FDStorage: {location_code}^FS
^XZ"""
    
    return zpl


class ScanningWindow(QDialog):
    """Separate window for barcode scanning"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Scanning Parts")
        self.setMinimumSize(800, 600)
        
        self.auto_process_timer = QTimer()
        self.auto_process_timer.setSingleShot(True)
        self.auto_process_timer.timeout.connect(self.auto_process_barcode)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("Barcode Scanning")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Scan parts with your Zebra barcode reader. Barcode will be processed automatically after 1 second.")
        layout.addWidget(info)
        
        input_group = QGroupBox("Barcode Input")
        input_layout = QVBoxLayout()
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Place cursor here and scan barcode...")
        self.barcode_input.textChanged.connect(self.on_barcode_text_changed)
        input_layout.addWidget(self.barcode_input)
        
        self.status_label = QLabel("Ready to scan")
        status_font = QFont()
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        input_layout.addWidget(self.status_label)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        layout.addWidget(QLabel("Last scan result:"))
        layout.addWidget(self.output_text)
        
        close_button = QPushButton("Close Window")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.barcode_input.setFocus()
    
    def on_barcode_text_changed(self, text):
        """Called when text in input field changes"""
        if text:
            self.status_label.setText(f"Reading... ({len(text)} characters)")
            self.auto_process_timer.start(1000)
        else:
            self.status_label.setText("Ready to scan")
            self.auto_process_timer.stop()
    
    def auto_process_barcode(self):
        """Automatic processing after 1 second"""
        raw_text = self.barcode_input.text().strip()
        
        if not raw_text:
            return
        
        print(f"AUTO_PROCESS: Automatic processing after 1 second")
        self.parent_window.process_barcode(raw_text)
        
        self.output_text.setPlainText(f"Scanned: {raw_text[:100]}...")
        self.status_label.setText("Processed! Ready for next scan")
        
        self.barcode_input.clear()
        self.barcode_input.setFocus()


class AllocatingWindow(QDialog):
    """Separate window for allocating storage locations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Allocating Storage Locations")
        self.setMinimumSize(800, 600)
        
        self.allocation_state = "waiting_for_part"
        self.selected_part_index = None
        
        self.auto_process_timer = QTimer()
        self.auto_process_timer.setSingleShot(True)
        self.auto_process_timer.timeout.connect(self.auto_process_allocation)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("Storage Location Allocation")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Step 1: Scan part barcode\nStep 2: Scan storage location barcode")
        layout.addWidget(info)
        
        input_group = QGroupBox("Barcode Input")
        input_layout = QVBoxLayout()
        
        self.allocate_barcode_input = QLineEdit()
        self.allocate_barcode_input.setPlaceholderText("Scan part or location...")
        self.allocate_barcode_input.textChanged.connect(self.on_allocate_text_changed)
        input_layout.addWidget(self.allocate_barcode_input)
        
        self.allocate_status = QLabel("Waiting to scan part...")
        status_font = QFont()
        status_font.setBold(True)
        self.allocate_status.setFont(status_font)
        input_layout.addWidget(self.allocate_status)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        self.allocate_output = QTextEdit()
        self.allocate_output.setReadOnly(True)
        self.allocate_output.setMaximumHeight(200)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.allocate_output)
        
        close_button = QPushButton("Close Window")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.allocate_barcode_input.setFocus()
    
    def on_allocate_text_changed(self, text):
        """Called when text in input field changes"""
        if text:
            self.auto_process_timer.start(1000)
    
    def auto_process_allocation(self):
        """Automatic processing after 1 second"""
        raw_text = self.allocate_barcode_input.text().strip()
        
        if not raw_text:
            return
        
        self.parent_window.process_allocation_barcode(raw_text, self)
        
        self.allocate_barcode_input.clear()
        self.allocate_barcode_input.setFocus()
    
    def closeEvent(self, event):
        """Reset state when window is closed"""
        self.allocation_state = "waiting_for_part"
        self.selected_part_index = None
        self.allocate_status.setText("Waiting to scan part...")
        super().closeEvent(event)


class PrintLabelsWindow(QDialog):
    """Separate window for printing labels"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Print Storage Labels")
        self.setMinimumSize(700, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        title = QLabel("Print Storage Labels")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Enter storage location code (e.g., A1, B23) to generate ZPL code for thermal printer.")
        layout.addWidget(info)
        
        input_group = QGroupBox("Location Code")
        input_layout = QVBoxLayout()
        
        self.print_location_input = QLineEdit()
        self.print_location_input.setPlaceholderText("Enter location code (e.g., A1, B23)...")
        input_layout.addWidget(self.print_location_input)
        
        generate_button = QPushButton("Generate ZPL")
        generate_button.clicked.connect(self.generate_label)
        input_layout.addWidget(generate_button)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        output_group = QGroupBox("ZPL Code (Copy and send to printer)")
        output_layout = QVBoxLayout()
        
        self.print_output = QTextEdit()
        self.print_output.setReadOnly(True)
        self.print_output.setPlaceholderText("ZPL code will appear here...")
        output_layout.addWidget(self.print_output)
        
        buttons_layout = QHBoxLayout()
        
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_zpl)
        buttons_layout.addWidget(copy_button)
        
        save_button = QPushButton("Save to File")
        save_button.clicked.connect(self.save_zpl)
        buttons_layout.addWidget(save_button)
        
        output_layout.addLayout(buttons_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        close_button = QPushButton("Close Window")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.print_location_input.setFocus()
    
    def generate_label(self):
        """Generate ZPL label"""
        location = self.print_location_input.text().strip().upper()
        
        if not location:
            QMessageBox.warning(self, "Error", "Please enter location code!")
            return
        
        zpl_code = generate_zpl_label(location)
        self.print_output.setPlainText(zpl_code)
        
        print(f"Generated ZPL for location: {location}")
    
    def copy_zpl(self):
        """Copy ZPL to clipboard"""
        zpl = self.print_output.toPlainText()
        
        if not zpl:
            QMessageBox.warning(self, "Error", "No ZPL code to copy! Generate label first.")
            return
        
        QApplication.clipboard().setText(zpl)
        QMessageBox.information(self, "Success", "ZPL code copied to clipboard!")
    
    def save_zpl(self):
        """Save ZPL to file"""
        zpl = self.print_output.toPlainText()
        
        if not zpl:
            QMessageBox.warning(self, "Error", "No ZPL code to save! Generate label first.")
            return
        
        location = self.print_location_input.text().strip().upper()
        filename = f"label_{location}.zpl"
        
        try:
            with open(filename, 'w') as f:
                f.write(zpl)
            QMessageBox.information(self, "Success", f"ZPL code saved to: {filename}")
            print(f"ZPL saved to file: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {str(e)}")


class BOMScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BOM Manager")
        self.setMinimumSize(1000, 700)
        
        self.scanned_codes = []
        self.is_processing = False
        
        self.bom_file = os.path.join(os.path.dirname(__file__), 'BOM_current.csv')
        
        self.scanning_window = None
        self.allocating_window = None
        self.print_window = None
        
        self.init_ui()
        self.load_bom()
        
    def init_ui(self):
        """Initialize user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        title = QLabel("BOM Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        buttons_layout = QHBoxLayout()
        
        start_scan_button = QPushButton("Start Scanning Parts")
        start_scan_button.clicked.connect(self.open_scanning_window)
        buttons_layout.addWidget(start_scan_button)
        
        start_allocate_button = QPushButton("Start Allocating Parts")
        start_allocate_button.clicked.connect(self.open_allocating_window)
        buttons_layout.addWidget(start_allocate_button)
        
        print_labels_button = QPushButton("Print Labels")
        print_labels_button.clicked.connect(self.open_print_window)
        buttons_layout.addWidget(print_labels_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.stats_label = QLabel("Statistics: 0 scanned, 0 successful, 0 errors")
        stats_font = QFont()
        stats_font.setBold(True)
        self.stats_label.setFont(stats_font)
        main_layout.addWidget(self.stats_label)
        
        table_group = QGroupBox("BOM - Bill of Materials")
        table_group_layout = QVBoxLayout()
        
        self.bom_table = QTableWidget()
        self.bom_table.setColumnCount(10)
        self.bom_table.setHorizontalHeaderLabels([
            '#', 'QTY', 'Part Number', 'MPN', 'Manufacturer', 'PO', 'CoO', 'RoHS', 'Storage', 'Time'
        ])
        
        self.bom_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bom_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bom_table.setAlternatingRowColors(True)
        self.bom_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = self.bom_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        
        self.bom_table.cellDoubleClicked.connect(self.on_table_double_click)
        
        table_group_layout.addWidget(self.bom_table)
        table_group.setLayout(table_group_layout)
        main_layout.addWidget(table_group)
    
    def open_scanning_window(self):
        """Open scanning window"""
        if self.scanning_window is None or not self.scanning_window.isVisible():
            self.scanning_window = ScanningWindow(self)
            self.scanning_window.show()
        else:
            self.scanning_window.activateWindow()
            self.scanning_window.barcode_input.setFocus()
    
    def open_allocating_window(self):
        """Open allocating window"""
        if self.allocating_window is None or not self.allocating_window.isVisible():
            self.allocating_window = AllocatingWindow(self)
            self.allocating_window.show()
        else:
            self.allocating_window.activateWindow()
            self.allocating_window.allocate_barcode_input.setFocus()
    
    def open_print_window(self):
        """Open print labels window"""
        if self.print_window is None or not self.print_window.isVisible():
            self.print_window = PrintLabelsWindow(self)
            self.print_window.show()
        else:
            self.print_window.activateWindow()
            self.print_window.print_location_input.setFocus()
    
    def process_barcode(self, raw_barcode):
        """Process scanned barcode"""
        if self.is_processing:
            print("PROCESS_BARCODE: Already processing, skipping...")
            return
        
        self.is_processing = True
        
        print(f"PROCESS_BARCODE: Method was called!")
        print(f"PROCESS_BARCODE: Raw barcode text: '{raw_barcode}'")
        print(f"PROCESS_BARCODE: Text length: {len(raw_barcode)}")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        parsed_data = parse_bom_barcode(raw_barcode)
        
        if not parsed_data:
            print("Part not found for barcode: {raw_barcode}")
            self.is_processing = False
            return
        
        part_number = parsed_data.get('PN', '')
        category = get_part_category(part_number)
        print(f"Category: {category}")
        
        existing_part = self.find_existing_part(parsed_data, raw_barcode)
        
        if existing_part is not None:
            self.increment_existing_part(existing_part, parsed_data, timestamp, raw_barcode)
        else:
            scan_data = {
                'raw': raw_barcode,
                'parsed': parsed_data,
                'timestamp': timestamp,
                'history': [timestamp]
            }
            
            self.scanned_codes.append(scan_data)
            
            row = self.bom_table.rowCount()
            self.bom_table.insertRow(row)
            
            for col in range(self.bom_table.columnCount()):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bom_table.setItem(row, col, item)
            
            self.bom_table.item(row, 0).setText(str(row + 1))
            
            if parsed_data:
                self.bom_table.item(row, 1).setText(parsed_data.get('QTY', ''))
                self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
                self.bom_table.item(row, 3).setText(parsed_data.get('MPN', ''))
                self.bom_table.item(row, 4).setText(parsed_data.get('MFR', ''))
                self.bom_table.item(row, 5).setText(parsed_data.get('PO', ''))
                self.bom_table.item(row, 6).setText(parsed_data.get('CoO', ''))
                self.bom_table.item(row, 7).setText('Yes' if 'RoHS' in parsed_data else '')
                self.bom_table.item(row, 8).setText(parsed_data.get('LOCATION', ''))
            else:
                self.bom_table.item(row, 2).setText(raw_barcode[:50])
            
            self.bom_table.item(row, 9).setText(timestamp.split()[1])
            
            self.bom_table.scrollToBottom()
            
            QTimer.singleShot(2000, lambda: self.reset_row_color(row))
        
        self.update_stats()
        self.save_bom()
        
        print(f"PROCESS_BARCODE: Successfully processed! Total scanned: {len(self.scanned_codes)}")
        
        QTimer.singleShot(100, lambda: setattr(self, 'is_processing', False))
    
    def find_existing_part(self, parsed_data, raw_barcode):
        """Find existing part in list by PN or MPN"""
        if not parsed_data:
            return None
        
        search_key = parsed_data.get('PN') or parsed_data.get('MPN')
        if not search_key:
            return None
        
        for idx, scan_data in enumerate(self.scanned_codes):
            existing_parsed = scan_data.get('parsed', {})
            existing_pn = existing_parsed.get('PN')
            existing_mpn = existing_parsed.get('MPN')
            
            if existing_pn == search_key or existing_mpn == search_key:
                return idx
        
        return None
    
    def increment_existing_part(self, part_index, new_parsed_data, timestamp, raw_barcode):
        """Add QTY from new scan to existing part"""
        scan_data = self.scanned_codes[part_index]
        parsed = scan_data.get('parsed', {})
        
        new_qty_str = new_parsed_data.get('QTY', '1')
        try:
            new_qty = int(new_qty_str)
        except:
            new_qty = 1
        
        current_qty_str = parsed.get('QTY', '0')
        try:
            current_qty = int(current_qty_str)
        except:
            current_qty = 0
        
        total_qty = current_qty + new_qty
        parsed['QTY'] = str(total_qty)
        
        if 'history' not in scan_data:
            scan_data['history'] = [scan_data['timestamp']]
        scan_data['history'].append(timestamp)
        
        self.bom_table.item(part_index, 1).setText(str(total_qty))
        
        for col in range(self.bom_table.columnCount()):
            item = self.bom_table.item(part_index, col)
            if item:
                item.setBackground(QColor("#C8E6C9"))
        
        row_to_reset = part_index
        QTimer.singleShot(2000, lambda: self.reset_row_color(row_to_reset))
        
        part_name = parsed.get('PN', 'Part')
        print(f"Part updated: {part_name} - added +{new_qty}, new quantity: {total_qty}")
    
    def process_allocation_barcode(self, raw_barcode, window):
        """Process barcode in allocation workflow"""
        if window.allocation_state == "waiting_for_part":
            parsed_data = parse_bom_barcode(raw_barcode)
            
            if not parsed_data:
                window.allocate_status.setText("Part NOT FOUND! Try again")
                window.allocate_output.setPlainText(f"Cannot parse: {raw_barcode}")
                print(f"Part not found for barcode: {raw_barcode}")
                return
            
            search_key = parsed_data.get('PN') or parsed_data.get('MPN')
            part_index = None
            
            for idx, scan_data in enumerate(self.scanned_codes):
                existing_parsed = scan_data.get('parsed', {})
                if existing_parsed.get('PN') == search_key or existing_parsed.get('MPN') == search_key:
                    part_index = idx
                    break
            
            if part_index is None:
                window.allocate_status.setText("Part NOT FOUND in BOM! Scan it in Scanning tab first")
                window.allocate_output.setPlainText(f"Part not in BOM: {search_key}")
                return
            
            window.selected_part_index = part_index
            window.allocation_state = "waiting_for_location"
            
            part_name = parsed_data.get('PN', 'Part')
            window.allocate_status.setText(f"Part selected! Now scan storage location")
            window.allocate_output.setPlainText(f"Part: {part_name}\nWaiting for location scan...")
            
            print(f"Part selected: {part_name} - waiting for location scan")
            
        elif window.allocation_state == "waiting_for_location":
            location_code = raw_barcode.strip().upper()
            
            scan_data = self.scanned_codes[window.selected_part_index]
            parsed = scan_data.get('parsed', {})
            parsed['LOCATION'] = location_code
            
            self.bom_table.item(window.selected_part_index, 8).setText(location_code)
            
            for col in range(self.bom_table.columnCount()):
                item = self.bom_table.item(window.selected_part_index, col)
                if item:
                    item.setBackground(QColor("#BBDEFB"))
            
            row_to_reset = window.selected_part_index
            QTimer.singleShot(3000, lambda: self.reset_row_color(row_to_reset))
            
            self.save_bom()
            
            part_name = parsed.get('PN', 'Part')
            window.allocate_status.setText(f"SUCCESS! {part_name} -> {location_code}")
            window.allocate_output.setPlainText(f"Assigned:\nPart: {part_name}\nLocation: {location_code}")
            
            print(f"Location assigned: {part_name} -> {location_code}")
            
            QTimer.singleShot(2000, lambda: self.reset_allocation_state(window))
    
    def reset_allocation_state(self, window):
        """Reset allocation workflow to initial state"""
        if window and window.isVisible():
            window.allocation_state = "waiting_for_part"
            window.selected_part_index = None
            window.allocate_status.setText("Waiting to scan part...")
            window.allocate_output.clear()
    
    def reset_row_color(self, row):
        """Reset row color to white"""
        if row is not None and row < self.bom_table.rowCount():
            for col in range(self.bom_table.columnCount()):
                item = self.bom_table.item(row, col)
                if item:
                    item.setBackground(QColor("#ffffff"))
    
    def on_table_double_click(self, row, column):
        """Show part details on double-click"""
        if row >= len(self.scanned_codes):
            return
        
        scan_data = self.scanned_codes[row]
        parsed_data = scan_data.get('parsed', {})
        history = scan_data.get('history', [scan_data['timestamp']])
        raw_code = scan_data.get('raw', '')
        
        dialog = PartDetailDialog(parsed_data, history, raw_code, self)
        dialog.exec()
    
    def update_stats(self):
        """Update statistics"""
        total = len(self.scanned_codes)
        successful = sum(1 for s in self.scanned_codes if s.get('parsed'))
        errors = total - successful
        
        self.stats_label.setText(f"Statistics: {total} scanned, {successful} successful, {errors} errors")
    
    def save_bom(self):
        """Save BOM to CSV"""
        try:
            with open(self.bom_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['QTY', 'Part Number', 'MPN', 'Manufacturer', 'PO', 'CoO', 'RoHS', 'URL', 'Storage Location', 'Time', 'Raw', 'History']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for scan_data in self.scanned_codes:
                    parsed = scan_data.get('parsed', {})
                    row_data = {
                        'QTY': parsed.get('QTY', ''),
                        'Part Number': parsed.get('PN', ''),
                        'MPN': parsed.get('MPN', ''),
                        'Manufacturer': parsed.get('MFR', ''),
                        'PO': parsed.get('PO', ''),
                        'CoO': parsed.get('CoO', ''),
                        'RoHS': 'Yes' if 'RoHS' in parsed else '',
                        'URL': parsed.get('URL', ''),
                        'Storage Location': parsed.get('LOCATION', ''),
                        'Time': scan_data.get('timestamp', ''),
                        'Raw': scan_data.get('raw', ''),
                        'History': json.dumps(scan_data.get('history', []))
                    }
                    writer.writerow(row_data)
            
            print(f"BOM automatically saved: {self.bom_file}")
        except Exception as e:
            print(f"Error saving BOM: {str(e)}")
    
    def load_bom(self):
        """Load BOM from CSV"""
        if not os.path.exists(self.bom_file):
            print(f"BOM file not found: {self.bom_file}")
            return
        
        try:
            with open(self.bom_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_data in reader:
                    parsed_data = {
                        'QTY': row_data.get('QTY', ''),
                        'PN': row_data.get('Part Number', ''),
                        'MPN': row_data.get('MPN', ''),
                        'MFR': row_data.get('Manufacturer', row_data.get('Výrobce', '')),
                        'PO': row_data.get('PO', ''),
                        'CoO': row_data.get('CoO', ''),
                        'URL': row_data.get('URL', ''),
                        'LOCATION': row_data.get('Storage Location', '')
                    }
                    
                    if row_data.get('RoHS') == 'Yes':
                        parsed_data['RoHS'] = 'RoHS'
                    
                    timestamp = row_data.get('Time', row_data.get('Čas', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    history_json = row_data.get('History', '[]')
                    try:
                        history = json.loads(history_json)
                    except:
                        history = [timestamp]
                    
                    scan_data = {
                        'raw': row_data.get('Raw', ''),
                        'parsed': parsed_data,
                        'timestamp': timestamp,
                        'history': history
                    }
                    
                    self.scanned_codes.append(scan_data)
                    
                    row = self.bom_table.rowCount()
                    self.bom_table.insertRow(row)
                    
                    for col in range(self.bom_table.columnCount()):
                        item = QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.bom_table.setItem(row, col, item)
                    
                    self.bom_table.item(row, 0).setText(str(row + 1))
                    self.bom_table.item(row, 1).setText(parsed_data.get('QTY', ''))
                    self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
                    self.bom_table.item(row, 3).setText(parsed_data.get('MPN', ''))
                    self.bom_table.item(row, 4).setText(parsed_data.get('MFR', ''))
                    self.bom_table.item(row, 5).setText(parsed_data.get('PO', ''))
                    self.bom_table.item(row, 6).setText(parsed_data.get('CoO', ''))
                    self.bom_table.item(row, 7).setText('Yes' if 'RoHS' in parsed_data else '')
                    self.bom_table.item(row, 8).setText(parsed_data.get('LOCATION', ''))
                    
                    time_str = timestamp.split()[1] if ' ' in timestamp else timestamp
                    self.bom_table.item(row, 9).setText(time_str)
            
            self.update_stats()
            print(f"Loaded {len(self.scanned_codes)} items from BOM")
        except Exception as e:
            print(f"Error loading BOM: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = BOMScanner()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

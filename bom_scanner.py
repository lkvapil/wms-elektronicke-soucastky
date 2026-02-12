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
    QDialog, QGridLayout, QTabWidget, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import json
import re
import csv
import os
import requests
import threading

try:
    from zebra import Zebra
    ZEBRA_AVAILABLE = True
except ImportError:
    ZEBRA_AVAILABLE = False
    print("Warning: zebra library not available. Direct printing will be disabled.")

try:
    from tme_api import TMEAPI
    TME_AVAILABLE = True
except ImportError:
    TME_AVAILABLE = False
    print("Warning: TME API module not available. TME integration will be disabled.")

try:
    from tme_api import TMEAPI
    TME_AVAILABLE = True
except ImportError:
    TME_AVAILABLE = False
    print("Warning: TME API module not available. TME integration will be disabled.")


class PartDetailDialog(QDialog):
    """Dialog for displaying part details with history"""
    
    def __init__(self, parsed_data, history, raw_code, parent=None):
        super().__init__(parent)
        self.parsed_data = parsed_data
        self.history = history.copy()  # Copy for editing
        self.raw_code = raw_code
        self.parent_window = parent
        self.part_index = None  # Part index in main table
        
        # Najít index partu v hlavní tabulce
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
        
        # Header with part name
        header = QLabel(f"📦 {self.parsed_data.get('PN', 'Unknown part')}")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Separator
        separator = QLabel("─" * 80)
        layout.addWidget(separator)
        
        # Grid layout for basic information
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
        
        if 'PO' in self.parsed_data:
            info_layout.addWidget(QLabel("PO:"), row, 0)
            po_label = QLabel(self.parsed_data['PO'])
            po_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(po_label, row, 1)
            row += 1
        
        if 'RoHS' in self.parsed_data:
            info_layout.addWidget(QLabel("RoHS:"), row, 0)
            info_layout.addWidget(QLabel("Yes"), row, 1)
            row += 1
        
        if 'URL' in self.parsed_data:
            info_layout.addWidget(QLabel("URL:"), row, 0)
            url_label = QLabel(f'<a href="{self.parsed_data["URL"]}">{self.parsed_data["URL"]}</a>')
            url_label.setOpenExternalLinks(True)
            url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            info_layout.addWidget(url_label, row, 1)
            row += 1
        
        if 'LOCATION' in self.parsed_data:
            info_layout.addWidget(QLabel("Storage Location:"), row, 0)
            location_label = QLabel(self.parsed_data['LOCATION'])
            location_font = QFont()
            location_font.setBold(True)
            location_font.setPointSize(11)
            location_label.setFont(location_font)
            location_label.setStyleSheet("color: #2196F3;")
            location_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_layout.addWidget(location_label, row, 1)
            row += 1
        
        # Add category based on part number
        if 'PN' in self.parsed_data:
            tme_api = self.parent_window.tme_api if self.parent_window else None
            category = get_part_category(self.parsed_data['PN'], self.parsed_data.get('VALUE'), tme_api)
            info_layout.addWidget(QLabel("Category:"), row, 0)
            category_label = QLabel(category)
            category_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            info_layout.addWidget(category_label, row, 1)
            row += 1
        
        # Add projects list
        projects = self.parsed_data.get('PROJECTS', [])
        info_layout.addWidget(QLabel("Projects:"), row, 0)
        if projects:
            projects_label = QLabel(", ".join(projects))
            projects_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            projects_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        else:
            projects_label = QLabel("No projects assigned")
            projects_label.setStyleSheet("color: #999;")
        info_layout.addWidget(projects_label, row, 1)
        row += 1
        
        # Add button to manage projects
        manage_projects_btn = QPushButton("Manage Projects")
        manage_projects_btn.clicked.connect(self.manage_projects)
        info_layout.addWidget(manage_projects_btn, row, 0)
        
        # Add button to manage storage locations
        manage_locations_btn = QPushButton("Manage Storage Locations")
        manage_locations_btn.clicked.connect(self.manage_storage_locations)
        info_layout.addWidget(manage_locations_btn, row, 1)
        row += 1
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Scan history - TABLE
        history_group = QGroupBox(f"Scan History ({len(self.history)}x scanned)")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(['#', 'Date', 'Time'])
        self.history_table.setRowCount(len(self.history))
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Nastavení šířek sloupců
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Naplnění historie
        for i, timestamp in enumerate(self.history):
            # Rozdělit datum a čas
            if ' ' in timestamp:
                date_part, time_part = timestamp.split(' ')
            else:
                date_part = timestamp
                time_part = ''
            
            self.history_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.history_table.setItem(i, 1, QTableWidgetItem(date_part))
            self.history_table.setItem(i, 2, QTableWidgetItem(time_part))
        
        history_layout.addWidget(self.history_table)
        
        # History management buttons
        history_buttons = QHBoxLayout()
        
        delete_history_btn = QPushButton("Delete Selected Record")
        delete_history_btn.clicked.connect(self.delete_selected_history)
        history_buttons.addWidget(delete_history_btn)
        
        clear_history_btn = QPushButton("Clear All History")
        clear_history_btn.clicked.connect(self.clear_history)
        history_buttons.addWidget(clear_history_btn)
        
        history_buttons.addStretch()
        
        history_layout.addLayout(history_buttons)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        layout.addWidget(close_button)
    
    def manage_projects(self):
        """Open dialog to manage projects for this part with checkboxes"""
        from PyQt6.QtWidgets import QCheckBox, QScrollArea
        
        current_projects = self.parsed_data.get('PROJECTS', [])
        
        # Get all available projects from parent window's projects_data
        all_projects = set()
        if self.parent_window and hasattr(self.parent_window, 'projects_data'):
            # Load from saved projects
            for project in self.parent_window.projects_data:
                project_name = project.get('name', '')
                if project_name:
                    all_projects.add(project_name)
            
            # Also include projects from BOM (in case there are unsaved ones)
            for scan_data in self.parent_window.scanned_codes:
                parsed = scan_data.get('parsed', {})
                projects = parsed.get('PROJECTS', [])
                all_projects.update(projects)
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Projects")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel(f"Select projects for part: {self.parsed_data.get('PN', 'Unknown')}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Check/uncheck projects to assign/remove this part:")
        layout.addWidget(info)
        
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Dictionary to store checkboxes
        checkboxes = {}
        
        # Add checkboxes for all existing projects
        if all_projects:
            for project in sorted(all_projects):
                checkbox = QCheckBox(project)
                checkbox.setChecked(project in current_projects)
                checkboxes[project] = checkbox
                scroll_layout.addWidget(checkbox)
        else:
            no_projects_label = QLabel("No projects available. Create a project first.")
            no_projects_label.setStyleSheet("color: #999;")
            scroll_layout.addWidget(no_projects_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connect buttons
        def save_changes():
            # Get selected projects
            new_projects = [name for name, checkbox in checkboxes.items() if checkbox.isChecked()]
            self.parsed_data['PROJECTS'] = new_projects
            
            # Update in parent window
            if self.part_index is not None and self.parent_window:
                self.parent_window.scanned_codes[self.part_index]['parsed']['PROJECTS'] = new_projects
                self.parent_window.save_bom()
                self.parent_window.refresh_projects_table()
            
            dialog.accept()
            
            # Refresh the part detail dialog
            self.accept()
            new_dialog = PartDetailDialog(self.parsed_data, self.history, self.raw_code, self.parent_window)
            new_dialog.exec()
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def manage_storage_locations(self):
        """Open dialog to manage storage locations for this part with checkboxes"""
        from PyQt6.QtWidgets import QCheckBox, QScrollArea
        
        # Get current location from BOM table (most accurate source)
        current_location = ''
        if self.part_index is not None and self.parent_window:
            storage_item = self.parent_window.bom_table.item(self.part_index, 9)
            if storage_item:
                current_location = storage_item.text()
        else:
            # Fallback to parsed_data
            current_location = self.parsed_data.get('LOCATION', '')
        
        # Get all available storage locations from parent window
        all_locations = []
        if self.parent_window and hasattr(self.parent_window, 'storage_locations_data'):
            for loc in self.parent_window.storage_locations_data:
                code = loc.get('code', '')
                if code:
                    all_locations.append(code)
        
        all_locations.sort()
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Storage Location")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel(f"Select storage location for part: {self.parsed_data.get('PN', 'Unknown')}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Select one storage location (radio buttons):")
        layout.addWidget(info)
        
        # Scroll area for radio buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Radio buttons group
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup
        button_group = QButtonGroup(dialog)
        
        # Add "No location" option
        no_location_radio = QRadioButton("(No location)")
        no_location_radio.setChecked(not current_location)
        button_group.addButton(no_location_radio)
        scroll_layout.addWidget(no_location_radio)
        
        # Dictionary to store radio buttons
        location_radios = {}
        
        # Add radio buttons for all existing locations
        if all_locations:
            for location in all_locations:
                radio = QRadioButton(location)
                radio.setChecked(location == current_location)
                button_group.addButton(radio)
                location_radios[location] = radio
                scroll_layout.addWidget(radio)
        else:
            no_locations_label = QLabel("No storage locations available. Create a location first in Storage tab.")
            no_locations_label.setStyleSheet("color: #999;")
            scroll_layout.addWidget(no_locations_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Connect buttons
        def save_changes():
            # Get selected location
            new_location = ''
            if no_location_radio.isChecked():
                new_location = ''
            else:
                for location, radio in location_radios.items():
                    if radio.isChecked():
                        new_location = location
                        break
            
            self.parsed_data['LOCATION'] = new_location
            
            # Update in parent window - find part in BOM table and update storage column
            if self.part_index is not None and self.parent_window:
                self.parent_window.scanned_codes[self.part_index]['parsed']['LOCATION'] = new_location
                
                # Update in BOM table (column 9 is Storage)
                part_number = self.parsed_data.get('PN', '')
                for row in range(self.parent_window.bom_table.rowCount()):
                    table_pn = self.parent_window.bom_table.item(row, 2)
                    if table_pn and table_pn.text() == part_number:
                        self.parent_window.bom_table.setItem(row, 9, QTableWidgetItem(new_location))
                        break
                
                self.parent_window.save_bom()
                self.parent_window.refresh_storage_table()
            
            dialog.accept()
            
            # Refresh the part detail dialog
            self.accept()
            new_dialog = PartDetailDialog(self.parsed_data, self.history, self.raw_code, self.parent_window)
            new_dialog.exec()
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
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
            # Remove from history
            timestamp_to_remove = self.history[current_row]
            self.history.pop(current_row)
            
            # Remove from table
            self.history_table.removeRow(current_row)
            
            # Renumber rows
            for row in range(self.history_table.rowCount()):
                self.history_table.item(row, 0).setText(str(row + 1))
            
            # Update QTY - subtract value from removed scan
            if self.part_index is not None and self.parent_window:
                self.recalculate_qty()
                self.parent_window.save_bom()
            
            print(f"🗑️ Deleted record from history: {timestamp_to_remove}")
    
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
            # Keep only first record
            first_record = self.history[0]
            self.history = [first_record]
            
            # Clear table and add only first record
            self.history_table.setRowCount(1)
            
            if ' ' in first_record:
                date_part, time_part = first_record.split(' ')
            else:
                date_part = first_record
                time_part = ''
            
            self.history_table.setItem(0, 0, QTableWidgetItem('1'))
            self.history_table.setItem(0, 1, QTableWidgetItem(date_part))
            self.history_table.setItem(0, 2, QTableWidgetItem(time_part))
            
            # Update QTY
            if self.part_index is not None and self.parent_window:
                self.recalculate_qty()
                self.parent_window.save_bom()
            
            print(f"🗑️ History cleared, first record kept")
    
    def recalculate_qty(self):
        """Recalculate QTY based on number of records in history"""
        if self.part_index is None or not self.parent_window:
            return
        
        scan_data = self.parent_window.scanned_codes[self.part_index]
        parsed = scan_data.get('parsed', {})
        
        # Update history in data
        scan_data['history'] = self.history
        
        # Original QTY from one scan (from barcode)
        original_qty_str = parsed.get('QTY', '1')
        try:
            # Try to get original QTY from first scan
            original_qty = int(original_qty_str) // len(scan_data['history']) if len(scan_data['history']) > 0 else int(original_qty_str)
        except:
            original_qty = 1
        
        # New total QTY = number of scans * original QTY
        new_total_qty = len(self.history) * original_qty
        parsed['QTY'] = str(new_total_qty)
        
        # Update in main table
        self.parent_window.bom_table.item(self.part_index, 1).setText(str(new_total_qty))
        
        # Update in dialog
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
        
        print(f"🔄 QTY recalculated: {new_total_qty} (history: {len(self.history)}x scans)")


def fix_czech_chars(text):
    """
    Fix common scanning errors from Czech keyboard layout
    
    When barcode scanner inputs numbers on Czech keyboard, they are shifted:
    - Shift+1 = +
    - Shift+2 = ě  
    - Shift+3 = š
    - Shift+4 = č
    - Shift+5 = ř
    - Shift+6 = ž
    - Shift+7 = ý
    - Shift+8 = á
    - Shift+9 = í
    - Shift+0 = é
    
    Special characters:
    - Slash / cannot be scanned (requires AltGr on Czech keyboard)
    - Scanner may send underscore _ instead (Shift+-)
    
    Args:
        text: Scanned text
        
    Returns:
        str: Cleaned text
    """
    char_fixes = {
        '+': '1',  # Shift+1
        'ě': '2',  # Shift+2
        'š': '3',  # Shift+3
        'č': '4',  # Shift+4
        'ř': '5',  # Shift+5
        'ž': '6',  # Shift+6
        'ý': '7',  # Shift+7
        'á': '8',  # Shift+8
        'í': '9',  # Shift+9
        'é': '0',  # Shift+0
        'ů': '0',  # Alternative for 0
    }
    
    cleaned = text
    for bad_char, good_char in char_fixes.items():
        cleaned = cleaned.replace(bad_char, good_char)
    
    # Special handling for slash replacement
    # Only replace underscore and regular dash with slash in likely TME symbols
    # (contains numbers and letters, looks like product code)
    if re.search(r'[A-Z]+\d+', cleaned, re.IGNORECASE):
        # Fix common scanning errors where / is misread as 7:
        # Pattern: DR38472.2X6 should be DR384/2.2X6
        # The "72." is misread "/" - replace digit+7+digit+dot with digit+/+digit+dot
        cleaned = re.sub(r'(\d)7(\d\.)', r'\1/\2', cleaned)
        
        # Now replace separators with slash, but NOT dots between digits (decimals) AND NOT in URLs
        cleaned = cleaned.replace('_', '/')  # Underscore to slash
        
        # IMPORTANT: Do NOT replace dots in URLs!
        # Only replace dots if NOT part of URL (check for http:// or www.)
        if not re.search(r'https?:', cleaned, re.IGNORECASE) and not re.search(r'www\.', cleaned, re.IGNORECASE):
            # Replace dot only if NOT between two digits (protect decimals like 2.2)
            cleaned = re.sub(r'\.(?!\d)', '/', cleaned)  # Dot not followed by digit
            cleaned = re.sub(r'(?<!\d)\.', '/', cleaned)  # Dot not preceded by digit
        # Replace single dash with slash only if surrounded by alphanumeric
        cleaned = re.sub(r'([A-Z0-9])-([A-Z0-9])', r'\1/\2', cleaned, flags=re.IGNORECASE)
    
    return cleaned


def shorten_footprint(footprint):
    """
    Shorten KiCad footprint names to essential info
    
    Examples:
        Diode_SMD:D_SOD-323 -> SOD-323
        Fuse:Fuse_0805_2012Metric -> 0805
        Capacitor_SMD:C_0805_2012Metric -> 0805
        Package_TO_SOT_SMD:SOT-23 -> SOT-23
    
    Args:
        footprint: Full KiCad footprint name
        
    Returns:
        str: Shortened footprint name
    """
    if not footprint:
        return ''
    
    # Remove library prefix (everything before :)
    if ':' in footprint:
        footprint = footprint.split(':', 1)[1]
    
    # Remove common prefixes
    prefixes_to_remove = ['D_', 'C_', 'R_', 'Fuse_', 'LED_', 'SW_']
    for prefix in prefixes_to_remove:
        if footprint.startswith(prefix):
            footprint = footprint[len(prefix):]
            break
    
    # Remove metric suffixes like _2012Metric, _3216Metric
    footprint = re.sub(r'_\d{4}Metric', '', footprint)
    
    # Extract just the package size if it's a standard component
    # Examples: 0805, 1206, SOT-23, etc.
    # Match patterns like 0805, 1206, SOT-23, QFN-44, etc.
    match = re.search(r'(\d{4}|[A-Z]+-\d+|SOT-\d+|QFN-\d+)', footprint)
    if match:
        return match.group(1)
    
    return footprint


def find_tme_symbol_fuzzy(scanned_text, tme_api):
    """
    Try to find TME symbol using fuzzy matching when exact match fails
    
    Args:
        scanned_text: Scanned text (may have slash substituted)
        tme_api: TMEAPI instance
        
    Returns:
        str or None: Found TME symbol or None
    """
    if not tme_api:
        return None
    
    # First, create variants with common substitutions
    variants = [
        scanned_text,
        scanned_text.replace('_', '/'),  # Underscore to slash
        scanned_text.replace('-', '/'),  # Dash to slash
        scanned_text.replace('.', '/'),  # Dot to slash
    ]
    
    # Fix common scanning errors where single digit becomes double
    # Example: DR38472.2X6 -> DR384/2.2X6 (47 -> 4, . -> /)
    # Pattern: number followed by 7 might be scanning artifact
    import re
    error_pattern = re.search(r'(\d)7(\d)', scanned_text)
    if error_pattern:
        # Try removing the 7
        fixed = scanned_text[:error_pattern.start()+1] + scanned_text[error_pattern.start()+2:]
        variants.append(fixed)
        variants.append(fixed.replace('.', '/'))
        variants.append(fixed.replace('_', '/'))
        variants.append(fixed.replace('-', '/'))
        print(f"Trying scan error fix: {scanned_text} -> {fixed}")
    
    # Try autocomplete with all variants
    for variant in variants:
        try:
            autocomplete = tme_api.autocomplete(variant)
            if autocomplete.get('Data', {}).get('Result'):
                results = autocomplete['Data']['Result']
                if results:
                    # Return first exact or similar match
                    for result in results:
                        similarity = result.get('MatchData', {}).get('Similarity')
                        if similarity in ['EXACT', 'SIMILAR']:
                            found_symbol = result.get('Product', {}).get('Symbol')
                            print(f"✓ TME autocomplete found: {found_symbol} (from variant: {variant})")
                            return found_symbol
                    # If no exact/similar, return first result
                    found_symbol = results[0].get('Product', {}).get('Symbol')
                    print(f"✓ TME autocomplete found: {found_symbol} (from variant: {variant})")
                    return found_symbol
        except Exception as e:
            print(f"TME autocomplete error for '{variant}': {e}")
    
    # Try search with all variants
    for variant in variants:
        if variant != scanned_text:
            try:
                search = tme_api.search_products(variant)
                if search.get('Data', {}).get('Amount', 0) > 0:
                    products = search['Data']['ProductList']
                    if products:
                        found_symbol = products[0].get('Symbol')
                        print(f"✓ TME search found: {found_symbol} (from variant: {variant})")
                        return found_symbol
            except Exception as e:
                print(f"TME search error for '{variant}': {e}")
    
    return None


def map_tme_category_to_general(tme_category):
    """
    Map specific TME category to specific component category
    
    Args:
        tme_category: Specific TME category (e.g., "SMD N channel transistors")
        
    Returns:
        str: Specific category (e.g., "Resistors", "Capacitors", etc.)
    """
    if not tme_category:
        return 'Unknown'
    
    category_lower = tme_category.lower()
    
    # Check for resistors
    if any(word in category_lower for word in [
        'resistor', 'resistance', 'potentiometer', 'trimmer', 'varistor', 'thermistor'
    ]):
        return 'Resistors'
    
    # Check for capacitors
    if any(word in category_lower for word in [
        'capacitor', 'condensator', 'electrolytic', 'ceramic', 'film', 'tantalum'
    ]):
        return 'Capacitors'
    
    # Check for LEDs (must be before diodes!)
    if any(word in category_lower for word in [
        'led', 'light emitting diode'
    ]):
        return 'LEDs'
    
    # Check for diodes (but not LEDs)
    if any(word in category_lower for word in [
        'diode', 'rectifier', 'zener', 'schottky', 'tvs', 'esd'
    ]) and 'led' not in category_lower:
        return 'Diodes'
    
    # Check for transistors
    if any(word in category_lower for word in [
        'transistor', 'mosfet', 'jfet', 'bjt', 'fet', 'igbt'
    ]):
        return 'Transistors'
    
    # Check for ICs
    if any(word in category_lower for word in [
        'ic', 'microcontroller', 'microprocessor', 'processor', 'cpu', 'mcu',
        'memory', 'flash', 'eeprom', 'logic', 'driver', 'regulator', 'converter',
        'amplifier', 'opamp', 'comparator'
    ]):
        return 'ICs'
    
    # Check for connectors
    if any(word in category_lower for word in [
        'connector', 'socket', 'header', 'terminal', 'plug'
    ]):
        return 'Connectors'
    
    # Check for inductors
    if any(word in category_lower for word in [
        'inductor', 'coil', 'choke', 'transformer'
    ]):
        return 'Inductors'
    
    # Check for crystals/oscillators
    if any(word in category_lower for word in [
        'crystal', 'oscillator', 'resonator'
    ]):
        return 'Crystals'
    
    # Check for fuses
    if any(word in category_lower for word in [
        'fuse', 'circuit breaker'
    ]):
        return 'Fuses'
    
    # Check for cables
    if any(word in category_lower for word in [
        'cable', 'wire', 'cord'
    ]):
        return 'Cables'
    
    # Mechanical
    if any(word in category_lower for word in [
        'screw', 'bolt', 'šroub'
    ]):
        return 'Screws'
    
    if any(word in category_lower for word in [
        'nut', 'matice'
    ]):
        return 'Nuts'
    
    if any(word in category_lower for word in [
        'bearing', 'ložisko'
    ]):
        return 'Bearings'
    
    # Default to Electronic Components if it contains common electronics terms
    if any(word in category_lower for word in [
        'smd', 'smt', 'through hole', 'dip', 'sot', 'soic', 'qfn'
    ]):
        return 'Electronic Components'
    
    # If nothing matches, return original TME category
    return tme_category


def generate_category_id(category, category_prefixes, category_counters):
    """
    Generate unique ID based on category prefix
    
    Args:
        category: Category name (e.g., "Electronic Components")
        category_prefixes: Dict mapping categories to prefixes
        category_counters: Dict tracking next ID number per category
    
    Returns:
        str: ID like "EC-001", "SC-042", etc.
    """
    # Get prefix for this category
    prefix = category_prefixes.get(category, "UN")  # Default to "UN" for unknown
    
    # Get and increment counter for this category
    if category not in category_counters:
        category_counters[category] = 1
    
    counter = category_counters[category]
    category_counters[category] += 1
    
    # Format: PREFIX-XXX (3 digits, zero-padded)
    return f"{prefix}-{counter:03d}"


def parse_bom_barcode(barcode_text):
    """
    Parses part barcode into structured data
    
    Format: QTY:value PN:value PO:value MFR:value MPN:value CoO:value RoHS URL
    
    Args:
        barcode_text: Text from barcode
        
    Returns:
        dict: Parsed data or None
    """
    # Fix common scanning errors (Czech characters -> numbers/characters)
    # TME barcodes also need this because Czech keyboard scans numbers as special chars
    cleaned = fix_czech_chars(barcode_text)
    
    # Special URL fixes for TME barcodes
    # TME scanner sends: https:77www7tme7eu7cz7details71N54087DIO
    # Should become:     https://www.tme.eu/cz/details/1N5408-DIO
    
    # Find TME URL and extract full product symbol (including everything after details)
    tme_url_match = re.search(
        r'https?[:/]+(?:www[.7])?tme[.7]eu[./7]*(?:cz[./7]+)?details[./7]+([A-Z0-9][A-Z0-9-./7]+)',
        cleaned,
        re.IGNORECASE
    )
    
    if tme_url_match:
        # Extract full product symbol
        raw_symbol = tme_url_match.group(1).strip()
        # Replace ALL /, 7, . with hyphens - Czech scanner can't type -
        # 1N5408/DIO -> 1N5408-DIO
        clean_symbol = raw_symbol.replace('/', '-').replace('7', '-').replace('.', '-')
        # Remove trailing separators
        clean_symbol = clean_symbol.rstrip('-7./')
        # Reconstruct proper TME URL
        cleaned = f'https://www.tme.eu/cz/details/{clean_symbol}'
    else:
        # Fallback: Try basic URL cleanup
        cleaned = re.sub(r'https?:77', 'https://', cleaned)
        cleaned = re.sub(r'www7', 'www.', cleaned)
        cleaned = re.sub(r'7(tme|eu|cz|com|org|net)', r'.\1', cleaned)
        cleaned = re.sub(r'(https?://[^\s]*?)7(cz|details|en|pl|de|fr)', r'\1/\2', cleaned)
        cleaned = re.sub(r'/details7([A-Z0-9])', r'/details/\1', cleaned)
    
    # FINAL FIX: TME product symbols - replace / with _, lowercase, keep . in numbers
    # DR384/2.2X6 -> dr384_2.2x6
    def fix_tme_symbol(match):
        symbol = match.group(1)
        # Replace ALL / with _ (not -)
        fixed = symbol.replace('/', '_')
        # Also replace 7 with _ (Czech keyboard issue)
        fixed = fixed.replace('7', '_')
        # Convert to lowercase
        fixed = fixed.lower()
        # Add trailing slash
        return f'/details/{fixed}/'
    
    cleaned = re.sub(r'/details/([A-Z0-9/.-]+?)(?:\s|$)', fix_tme_symbol, cleaned, flags=re.IGNORECASE)
    
    # Ensure /cz/ is present in TME URLs
    cleaned = re.sub(r'(https?://www\.tme\.eu)/details/', r'\1/cz/details/', cleaned, flags=re.IGNORECASE)
    
    # Attempt to extract data using regular expressions
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
    
    # FIX TME URL - rebuild from PN with smart separator detection
    if 'PN' in parsed_data and 'URL' in parsed_data and 'tme.eu' in parsed_data['URL'].lower():
        pn = parsed_data['PN']
        
        # Determine separator: if second part (after /) has letters at end → use '-', else '_'
        if '/' in pn:
            parts = pn.split('/')
            second_part = parts[-1]
            # If ends with letters (like DIO, DIODE) → use '-', else '_'
            if re.search(r'[A-Z]+$', second_part, re.IGNORECASE):
                separator = '-'
            else:
                separator = '_'
            tme_symbol = pn.replace('/', separator).lower()
        else:
            tme_symbol = pn.lower()
        
        parsed_data['URL'] = f"https://www.tme.eu/cz/details/{tme_symbol}/"
    
    # If we found at least some data, return it
    if parsed_data:
        parsed_data['raw'] = cleaned  # Store cleaned version, not original
        parsed_data['cleaned'] = cleaned
        parsed_data['original'] = barcode_text  # Keep original for reference
        return parsed_data
    
    return None


def get_part_category(part_number, value=None, tme_api=None):
    """
    Get part category - uses TME API if available, otherwise falls back to pattern matching
    
    Categories:
    1xx = Electronic Components
    2xx = Screws
    3xx = Nuts
    4xx = Bearings
    5xx = Cables
    
    Args:
        part_number: Part number (e.g., "155", "2010", "AO3401A")
        value: Product name/description (optional, for fallback)
        tme_api: TMEAPI instance (optional, for automatic category detection)
        
    Returns:
        str: Category name
    """
    if not part_number:
        return "Unknown"
    
    pn_str = str(part_number)
    
    print(f"🔍 Looking up category for: {pn_str}")
    
    # Check if it's a Prumex product (6-digit number) and has VALUE with category keywords
    if value and pn_str.isdigit() and len(pn_str) == 6:
        value_lower = str(value).lower()
        value_upper = str(value).upper()
        
        # Screws - check for keywords and prefixes
        if ('šroub' in value_lower or 'screw' in value_lower or 
            value_upper.startswith('S-') or value_upper.startswith('Š-') or
            'din' in value_lower or 'iso' in value_lower):
            print(f"   ✓ Prumex product detected: '{value}' → Screws")
            return 'Screws'
        # Nuts - check for keywords and M- prefix
        elif ('matice' in value_lower or 'nut' in value_lower or
              value_upper.startswith('M-') or value_upper.startswith('M ')):
            print(f"   ✓ Prumex product detected: '{value}' → Nuts")
            return 'Nuts'
        # Bearings
        elif 'ložisko' in value_lower or 'bearing' in value_lower:
            print(f"   ✓ Prumex product detected: '{value}' → Bearings")
            return 'Bearings'
    
    # Try TME API first if available
    if tme_api and TME_AVAILABLE:
        # Create search variants - try with and without separators
        search_variants = [
            pn_str,  # Original
            pn_str.replace('/', '-'),  # / → -
            pn_str.replace('-', '/'),  # - → /
            pn_str.replace('/', ''),   # Remove /
            pn_str.replace('-', ''),   # Remove -
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        search_variants = [x for x in search_variants if not (x in seen or seen.add(x))]
        
        print(f"   Trying {len(search_variants)} variants: {search_variants}")
        
        for variant in search_variants:
            try:
                # Search for product in TME - returns actual category from database
                print(f"   🌐 TME search_products('{variant}')...")
                result = tme_api.search_products(variant)
                
                amount = result.get('Data', {}).get('Amount', 0)
                print(f"      Found {amount} results")
                
                if result.get('Data', {}).get('ProductList') and amount > 0:
                    product = result['Data']['ProductList'][0]
                    tme_symbol = product.get('Symbol', '')
                    tme_category = product.get('Category', '')  # FIX: Category not CategoryName!
                    
                    print(f"      First result: {tme_symbol} → {tme_category}")
                    print(f"      🔍 Product keys: {list(product.keys())}")
                    print(f"      📦 Full product data: {product}")
                    
                    # Verify that TME found the correct part (symbol should be similar to part number)
                    if tme_symbol and tme_category:
                        # Check if TME symbol matches our part number (case-insensitive, ignore separators)
                        symbol_clean = tme_symbol.lower().replace('-', '').replace('_', '').replace('/', '')
                        pn_clean = pn_str.lower().replace('-', '').replace('_', '').replace('/', '')
                        
                        # If symbols match (or part number is contained in symbol), use TME category
                        if pn_clean in symbol_clean or symbol_clean in pn_clean:
                            print(f"📂 TME found: {tme_symbol} → Category: {tme_category}")
                            # Map TME category to general category
                            general_category = map_tme_category_to_general(tme_category)
                            print(f"   ✅ Mapped to general category: {general_category}")
                            return general_category
                        else:
                            print(f"⚠️ TME found different part: {tme_symbol} (searched for {variant}), trying next variant")
                            continue
            except Exception as e:
                print(f"⚠️ TME search failed for '{variant}': {e}")
                continue
        
        # If all search variants failed, try exact match with get_products
        print(f"   🌐 TME get_products(['{pn_str}'])...")
        try:
            result = tme_api.get_products([pn_str])
            if result.get('Data', {}).get('ProductList'):
                product = result['Data']['ProductList'][0]
                tme_symbol = product.get('Symbol', '')
                tme_category = product.get('Category', '')  # FIX: Category not CategoryName!
                
                print(f"      Result: {tme_symbol} → {tme_category}")
                
                if tme_symbol and tme_category:
                    print(f"📂 TME found (exact): {tme_symbol} → Category: {tme_category}")
                    # Map TME category to general category
                    general_category = map_tme_category_to_general(tme_category)
                    print(f"   ✅ Mapped to general category: {general_category}")
                    return general_category
        except Exception as e:
            print(f"⚠️ TME get_products failed: {e}")
    
    # If TME API didn't find anything, return "Unknown"
    # Don't try to guess category by prefixes or numbers - that's unreliable!
    print(f"⚠️ No TME category found for {pn_str}, returning Unknown")
    return 'Unknown'


def shorten_prumex_name(product_name):
    """
    Shorten Prumex product names - keep only important specs
    
    Example:
    "šroub válcová hlava inbus DIN 912 M2x10 nerez A2" -> "DIN 912 M2x10 A2"
    
    Args:
        product_name: Full product name from Prumex
        
    # Fallback: Check by first digit for numbered parts (only if value didn't help)
    first_char = pn_str[0] if pn_str else ''
    
    categories = {
        '1': 'Electronic Components',
        '2': 'Screws',
        '3': 'Nuts',
        '4': 'Bearings',
        '5': 'Cables'
    }
    
    if first_char in categories:
        return categories[first_char]
    
    # Final fallback: Common electronic component prefixes
    # 2N, AO, BC, BD, BF, etc. are common transistor/IC prefixes
    electronic_prefixes = [
        '1N', '2N', '3N', '4N',  # Diodes, transistors
        'AO', 'AP',  # Alpha & Omega, Advanced Power
        'BC', 'BD', 'BF', 'BS', 'BU', 'BT',  # Transistors
        'IR', 'FD', 'TP',  # International Rectifier, Fairchild, etc.
        'LM', 'TL', 'NE',  # ICs
        'STM', 'AT',  # Microcontrollers
    ]
    
    pn_upper = pn_str.upper()
    for prefix in electronic_prefixes:
        if pn_upper.startswith(prefix):
            return 'Electronic Components'
    
    Returns:
        str: Shortened name with specs only
    """
    if not product_name:
        return product_name
    
    # Remove common Czech prefixes
    name = product_name
    prefixes_to_remove = [
        r'^šroub\s+',
        r'^matice\s+',
        r'^podložka\s+',
        r'^válcová hlava\s+',
        r'^zapuštěná hlava\s+',
        r'^inbus\s+',
        r'^torx\s+',
        r'^imbus\s+',
        r'^\s*-\s*',
    ]
    
    for prefix in prefixes_to_remove:
        name = re.sub(prefix, '', name, flags=re.IGNORECASE)
    
    # Extract important parts: DIN/ISO numbers, dimensions, material
    # Pattern: DIN/ISO XXX, M dimensions, material codes
    important_parts = []
    
    # Find DIN/ISO/EN standards
    din_match = re.search(r'(DIN|ISO|EN)\s*\d+[A-Z0-9-]*', name, re.IGNORECASE)
    if din_match:
        important_parts.append(din_match.group(0))
    
    # Find dimensions (M2, M3x10, etc.)
    dim_match = re.search(r'M\d+[x×]\d+', name, re.IGNORECASE)
    if dim_match:
        important_parts.append(dim_match.group(0))
    elif re.search(r'M\d+', name):
        m_match = re.search(r'M\d+', name)
        important_parts.append(m_match.group(0))
    
    # Find material codes (A2, A4, 8.8, 10.9, pozink, etc.) - exclude "nerez"
    material_codes = re.findall(r'\b(A2|A4|pozink|zinek|8\.8|10\.9|12\.9)\b', name, re.IGNORECASE)
    if material_codes:
        important_parts.extend(material_codes)
    
    if important_parts:
        return ' '.join(important_parts)
    
    # Fallback: return first 50 chars if no pattern matched
    return name[:50].strip()


def sanitize_zpl(zpl_content):
    """
    Sanitize ZPL content by replacing unsupported characters
    """
    replacements = {
        "'": "'",
        # Czech characters
        "č": "c",
        "Č": "C",
        "ď": "d",
        "Ď": "D",
        "ě": "e",
        "Ě": "E",
        "ň": "n",
        "Ň": "N",
        "ř": "r",
        "Ř": "R",
        "š": "s",
        "Š": "S",
        "ť": "t",
        "Ť": "T",
        "ů": "u",
        "Ů": "U",
        "ý": "y",
        "Ý": "Y",
        "ž": "z",
        "Ž": "Z",
        # Scandinavian characters
        "ø": "o",
        "Ø": "O",
        "å": "a",
        "Å": "A",
        "æ": "ae",
        "Æ": "AE",
        # German characters
        "ä": "a",
        "Ä": "A",
        "ö": "o",
        "Ö": "O",
        "ü": "u",
        "Ü": "U",
        "ß": "ss",
        # French/Spanish characters
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "á": "a",
        "à": "a",
        "â": "a",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ñ": "n",
        "ç": "c",
    }
    
    for old_char, new_char in replacements.items():
        zpl_content = zpl_content.replace(old_char, new_char)
    
    # Remove any remaining characters that can't be encoded in cp437
    zpl_content = zpl_content.encode('cp437', errors='replace').decode('cp437')
    
    return zpl_content


def generate_zpl_label(location_code):
    """
    Generate ZPL code for 2x1 inch storage location label
    
    Label contains:
    - Barcode (Code 128)
    - Text: "Storage: [location]"
    
    Args:
        location_code: Storage location code (e.g., "A1", "B23")
        
    Returns:
        str: ZPL code ready to send to printer
    """
    # ZPL for 2x1 inch label at 203 dpi
    # Width: 2 inch = 406 dots
    # Height: 1 inch = 203 dots
    
    zpl = f"""^XA
^FO50,20^BY2^BCN,100,Y,N,N^FD{location_code}^FS
^XZ"""
    
    return zpl


def generate_zpl_label_4x6(location_code):
    """
    Generate ZPL code for 4x6 inch storage location label
    
    Label contains:
    - Large barcode (Code 128)
    - Text: "Storage Location"
    - Large location code text
    
    Args:
        location_code: Storage location code (e.g., "A1", "B23")
        
    Returns:
        str: ZPL code ready to send to printer
    """
    # ZPL for 4x6 inch label at 203 dpi
    # Width: 4 inch = 812 dots
    # Height: 6 inch = 1218 dots
    
    zpl = f"""^XA
^FO100,100^A0N,60,60^FDStorage Location^FS
^FO100,200^BY4^BCN,200,Y,N,N^FD{location_code}^FS
^XZ"""
    
    return zpl


class BOMScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BOM Manager - Scanner")
        
        # Data
        self.scanned_codes = []
        self.is_processing = False
        
        # Category prefix mapping and counters
        self.category_prefixes = {
            "Resistors": "RE",
            "Capacitors": "CP",
            "LEDs": "LD",
            "Diodes": "DI",
            "Transistors": "TR",
            "ICs": "IC",
            "Connectors": "CN",
            "Inductors": "IN",
            "Crystals": "CR",
            "Fuses": "FU",
            "Electronic Components": "EC",  # General fallback
            "Screws": "SC",
            "Nuts": "NU",
            "Bearings": "BE",
            "Cables": "CA",
            "Unknown": "UN"
        }
        self.category_counters = {}  # Tracks next ID number per category
        self.pending_api_calls = {}  # Track pending TME API calls by row
        
        # Files for saving data
        self.bom_file = os.path.join(os.path.dirname(__file__), 'BOM_current.csv')
        self.storage_file = os.path.join(os.path.dirname(__file__), 'storage_locations.json')
        self.projects_file = os.path.join(os.path.dirname(__file__), 'projects.json')
        
        # TME API configuration
        self.tme_api = None
        if TME_AVAILABLE:
            try:
                TME_TOKEN = "c551c199d493fe30e9c68da8223b947f9aa671cddb66a04fc0"
                TME_SECRET = "4ff75f1cb3075cca95b1"
                self.tme_api = TMEAPI(TME_TOKEN, TME_SECRET)
                print("✓ TME API initialized")
            except Exception as e:
                print(f"✗ TME API initialization failed: {e}")
        
        # Storage and projects data
        self.storage_locations_data = []  # List of storage location dicts
        self.projects_data = []  # List of project dicts
        
        # Timer for automatic processing after scanning
        self.auto_process_timer = QTimer()
        self.auto_process_timer.setSingleShot(True)
        self.auto_process_timer.timeout.connect(self.auto_process_barcode)
        
        # UI initialization
        self.init_ui()
        
        # Load existing data
        self.load_bom()
        self.load_storage_locations()
        self.load_projects()
        
        # Refresh tables after loading data
        self.refresh_storage_table()
        self.refresh_projects_table()
        
    def init_ui(self):
        """Initialize user interface"""
        # Create toolbar
        toolbar = self.addToolBar("Quick Actions")
        toolbar.setMovable(False)
        
        # Add toolbar actions
        scan_action = toolbar.addAction("Start Scanning Parts")
        scan_action.triggered.connect(self.open_scanning_tab)
        
        allocate_action = toolbar.addAction("Start Allocating Parts")
        allocate_action.triggered.connect(self.open_allocating_tab)
        
        print_action = toolbar.addAction("Print Labels")
        print_action.triggered.connect(self.open_print_labels_tab)
        
        toolbar.addSeparator()
        
        assign_project_action = toolbar.addAction("Assign to Project")
        assign_project_action.triggered.connect(self.open_assign_project_tab)
        
        project_overview_action = toolbar.addAction("Project Overview")
        project_overview_action.triggered.connect(self.open_project_overview_tab)
        
        toolbar.addSeparator()
        
        import_bom_action = toolbar.addAction("Import BOM as CSV")
        import_bom_action.triggered.connect(self.import_bom_from_csv)
        
        if TME_AVAILABLE and self.tme_api:
            search_tme_action = toolbar.addAction("Search TME")
            search_tme_action.triggered.connect(self.open_tme_search_dialog)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Main tab widget - 3 main tabs
        self.main_tab_widget = QTabWidget()
        main_layout.addWidget(self.main_tab_widget)
        
        # Tab 1: Parts (with sub-tabs)
        self.parts_tab = QWidget()
        self.init_parts_tab()
        self.main_tab_widget.addTab(self.parts_tab, "Parts")
        
        # Tab 2: Storage (with sub-tabs)
        self.storage_tab = QWidget()
        self.init_storage_tab()
        self.main_tab_widget.addTab(self.storage_tab, "Storage")
        
        # Tab 3: Projects (with sub-tabs)
        self.projects_tab = QWidget()
        self.init_projects_tab()
        self.main_tab_widget.addTab(self.projects_tab, "Projects")
        
        # Set default to Parts tab
        self.main_tab_widget.setCurrentIndex(0)
    
    def init_parts_tab(self):
        """Initialize Parts tab - just BOM Table"""
        # Parts tab has BOM Table directly (no sub-tabs)
        self.init_table_tab_direct(self.parts_tab)
        
        # Create scan tab as separate widget for toolbar access
        self.scan_tab = QWidget()
        self.init_scan_tab()
    
    def init_table_tab_direct(self, parent_widget):
        """Initialize BOM table directly in parent widget"""
        table_layout = QVBoxLayout(parent_widget)
        
        # Table for scanned parts - MAIN ELEMENT
        table_group = QGroupBox("BOM - Bill of Materials")
        table_group_layout = QVBoxLayout()
        
        # Filter row - NEW
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        
        self.category_filter = QComboBox()
        # Start with just "All", will be updated dynamically
        self.category_filter.addItems(["All"])
        self.category_filter.currentTextChanged.connect(self.filter_by_category)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addStretch()
        
        table_group_layout.addLayout(filter_layout)
        
        # Table management buttons at the top
        table_buttons_layout = QHBoxLayout()
        
        self.delete_row_button = QPushButton("Delete Row")
        self.delete_row_button.clicked.connect(self.delete_selected_row)
        table_buttons_layout.addWidget(self.delete_row_button)
        
        self.clear_list_button = QPushButton("Clear All")
        self.clear_list_button.clicked.connect(self.clear_list)
        table_buttons_layout.addWidget(self.clear_list_button)
        
        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        table_buttons_layout.addWidget(self.export_button)
        
        self.export_json_button = QPushButton("Export JSON")
        self.export_json_button.clicked.connect(self.export_to_json)
        table_buttons_layout.addWidget(self.export_json_button)
        
        table_group_layout.addLayout(table_buttons_layout)
        
        # Table
        self.bom_table = QTableWidget()
        self.bom_table.setColumnCount(13)
        self.bom_table.setHorizontalHeaderLabels([
            '#', 'QTY', 'Part Number', 'Value', 'Package', 'MPN', 'Manufacturer', 
            'LCSC', 'Footprint', 'Storage', 'Projects', 'PO', 'Time'
        ])
        
        # Table settings
        self.bom_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bom_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bom_table.setAlternatingRowColors(True)
        self.bom_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column width settings
        header = self.bom_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # QTY
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Part Number
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Value
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Package
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # MPN
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Manufacturer
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # LCSC
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Footprint
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Storage
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Projects
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents)  # PO
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.ResizeToContents)  # Time
        
        # Double-click function to show URL
        self.bom_table.cellDoubleClicked.connect(self.on_table_double_click)
        
        table_group_layout.addWidget(self.bom_table)
        table_group.setLayout(table_group_layout)
        table_layout.addWidget(table_group)
    
    def init_storage_tab(self):
        """Initialize Storage tab with storage locations table"""
        layout = QVBoxLayout(self.storage_tab)
        
        # Storage table
        table_group = QGroupBox("Storage Locations")
        table_layout = QVBoxLayout()
        
        # Buttons at the top
        buttons_layout = QHBoxLayout()
        
        create_storage_btn = QPushButton("Create Storage Location")
        create_storage_btn.clicked.connect(self.create_storage_location)
        buttons_layout.addWidget(create_storage_btn)
        
        delete_storage_btn = QPushButton("Delete Storage Location")
        delete_storage_btn.clicked.connect(self.delete_storage_location)
        buttons_layout.addWidget(delete_storage_btn)
        
        table_layout.addLayout(buttons_layout)
        
        # Table
        self.storage_table = QTableWidget()
        self.storage_table.setColumnCount(4)
        self.storage_table.setHorizontalHeaderLabels([
            'Location Code', 'Part Number', 'Quantity', 'Description'
        ])
        
        self.storage_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.storage_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.storage_table.setAlternatingRowColors(True)
        self.storage_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = self.storage_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Double-click to show storage details
        self.storage_table.cellDoubleClicked.connect(self.show_storage_details)
        
        table_layout.addWidget(self.storage_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Create allocate and print tabs as separate widgets for toolbar access
        self.allocate_tab = QWidget()
        self.init_allocate_tab()
        
        self.print_tab = QWidget()
        self.init_print_tab()
        
        # Initialize storage data list
        self.storage_locations = []
    
    def init_projects_tab(self):
        """Initialize Projects tab with projects table"""
        layout = QVBoxLayout(self.projects_tab)
        
        # Projects table
        table_group = QGroupBox("Projects")
        table_layout = QVBoxLayout()
        
        # Buttons at the top
        buttons_layout = QHBoxLayout()
        
        create_project_btn = QPushButton("Create Project")
        create_project_btn.clicked.connect(self.create_project)
        buttons_layout.addWidget(create_project_btn)
        
        delete_project_btn = QPushButton("Delete Project")
        delete_project_btn.clicked.connect(self.delete_project)
        buttons_layout.addWidget(delete_project_btn)
        
        table_layout.addLayout(buttons_layout)
        
        # Table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels([
            'Project Name', 'Parts Count', 'Total Quantity', 'Description'
        ])
        
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.projects_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.projects_table.setAlternatingRowColors(True)
        self.projects_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column widths
        header = self.projects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Double-click to show project details
        self.projects_table.cellDoubleClicked.connect(self.show_project_details)
        
        table_layout.addWidget(self.projects_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Initialize widgets for toolbar access
        self.project_barcode_input = QLineEdit()
        self.project_name_input = QLineEdit()
        self.project_assign_status = QLabel()
        self.projects_overview_text = QTextEdit()
        
        # Timer for auto-processing barcode
        self.project_auto_timer = QTimer()
        self.project_auto_timer.setSingleShot(True)
        self.project_auto_timer.timeout.connect(self.auto_select_project_part)
        self.selected_project_part = None
    
    def open_scanning_tab(self):
        """Open scanning dialog via toolbar"""
        # Create scanning dialog
        scan_dialog = QDialog(self)
        scan_dialog.setWindowTitle("Scanning Parts")
        scan_dialog.setMinimumSize(800, 500)
        
        scan_layout = QVBoxLayout(scan_dialog)
        
        # Add scan tab content to dialog
        self.init_scan_tab_in_dialog(scan_layout)
        
        scan_dialog.exec()
    
    def open_allocating_tab(self):
        """Open allocating dialog via toolbar"""
        # Create allocating dialog
        allocate_dialog = QDialog(self)
        allocate_dialog.setWindowTitle("Allocating Storage Locations")
        allocate_dialog.setMinimumSize(800, 500)
        
        allocate_layout = QVBoxLayout(allocate_dialog)
        
        title = QLabel("Storage Location Allocation")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        allocate_layout.addWidget(title)
        
        info = QLabel("Step 1: Scan part barcode\\nStep 2: Scan storage location barcode")
        allocate_layout.addWidget(info)
        
        input_group = QGroupBox("Barcode Input")
        input_layout = QVBoxLayout()
        
        dialog_allocate_input = QLineEdit()
        dialog_allocate_input.setPlaceholderText("Scan part or location...")
        input_layout.addWidget(dialog_allocate_input)
        
        dialog_status = QLabel("Waiting to scan part...")
        status_font = QFont()
        status_font.setBold(True)
        dialog_status.setFont(status_font)
        input_layout.addWidget(dialog_status)
        
        input_group.setLayout(input_layout)
        allocate_layout.addWidget(input_group)
        
        allocate_layout.addStretch()
        
        # Timer for auto-processing
        allocate_timer = QTimer()
        allocate_timer.setSingleShot(True)
        allocate_timer.setInterval(1000)
        
        # Variables to track state
        current_part = None
        
        def on_allocate_text_changed():
            """Reset timer when text changes"""
            allocate_timer.stop()
            text = dialog_allocate_input.text().strip()
            if text:
                allocate_timer.start()
        
        def auto_process_allocate():
            """Auto-process after timer expires"""
            nonlocal current_part
            text = dialog_allocate_input.text().strip()
            
            if not text:
                return
            
            # If no part selected yet, this is the part
            if current_part is None:
                # Parse barcode to get part number
                parsed = parse_bom_barcode(text)
                if parsed and 'PN' in parsed:
                    current_part = parsed['PN'].upper()
                    dialog_status.setText(f"Part scanned: {current_part}\n\nNow scan storage location...")
                    dialog_allocate_input.clear()
                else:
                    # If parsing failed, treat as simple location code
                    current_part = text.upper()
                    dialog_status.setText(f"Part: {current_part}\n\nNow scan storage location...")
                    dialog_allocate_input.clear()
            else:
                # This is the storage location - could be simple code or barcode
                # First fix Czech chars
                cleaned_text = fix_czech_chars(text)
                parsed = parse_bom_barcode(text)
                if parsed and 'PN' in parsed:
                    # It's another part barcode, use PN as location
                    location = parsed['PN'].upper()
                else:
                    # Simple location code
                    location = cleaned_text.upper()
                
                # Update BOM with storage location (column 9 is Storage)
                found = False
                for row in range(self.bom_table.rowCount()):
                    # Column 2 is Part Number (0=#, 1=QTY, 2=Part Number)
                    part_num = self.bom_table.item(row, 2).text() if self.bom_table.item(row, 2) else ""
                    if part_num == current_part:
                        self.bom_table.setItem(row, 9, QTableWidgetItem(location))
                        found = True
                        break
                
                if found:
                    # Check if location exists in storage_locations_data
                    location_exists = any(loc['code'] == location for loc in self.storage_locations_data)
                    if not location_exists:
                        # Storage doesn't exist - show error
                        dialog_status.setText(f"✗ Storage {location} not found\\nCreate it first in Storage tab")
                        QMessageBox.warning(allocate_dialog, "Error", f"Storage location '{location}' does not exist!\n\nPlease create it first in the Storage tab.")
                        current_part = None
                        dialog_allocate_input.clear()
                        return
                    
                    # Update in scanned_codes as well
                    for scan_data in self.scanned_codes:
                        if scan_data.get('parsed', {}).get('PN') == current_part:
                            scan_data['parsed']['LOCATION'] = location
                            break
                    
                    # Save to CSV
                    self.save_bom()
                    
                    self.refresh_storage_table()
                    
                    dialog_status.setText(f"✓ {current_part} allocated to {location}\\nScan next part...")
                    QMessageBox.information(allocate_dialog, "Success", f"Part {current_part} allocated to storage location {location}")
                else:
                    dialog_status.setText(f"✗ Part {current_part} not found in BOM\\nScan part again...")
                    QMessageBox.warning(allocate_dialog, "Error", f"Part {current_part} not found in BOM!")
                
                current_part = None
                dialog_allocate_input.clear()
        
        allocate_timer.timeout.connect(auto_process_allocate)
        dialog_allocate_input.textChanged.connect(on_allocate_text_changed)
        
        dialog_allocate_input.setFocus()
        allocate_dialog.exec()
    
    def open_print_labels_tab(self):
        """Open print labels dialog via toolbar"""
        from PyQt6.QtWidgets import QComboBox
        from PyQt6.QtPrintSupport import QPrinterInfo
        
        # Create print labels dialog
        print_dialog = QDialog(self)
        print_dialog.setWindowTitle("Print Storage Labels")
        print_dialog.setMinimumSize(700, 700)
        
        print_layout = QVBoxLayout(print_dialog)
        
        title = QLabel("Print Storage Labels")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        print_layout.addWidget(title)
        
        info = QLabel("Enter storage location code (e.g., A1, B23) to generate ZPL code for thermal printer.")
        print_layout.addWidget(info)
        
        # Printer selection
        printer_group = QGroupBox("Printer Settings")
        printer_layout = QVBoxLayout()
        
        printer_select_layout = QHBoxLayout()
        printer_select_layout.addWidget(QLabel("Printer:"))
        
        printer_combo = QComboBox()
        # Get available printers
        available_printers = QPrinterInfo.availablePrinterNames()
        if available_printers:
            printer_combo.addItems(available_printers)
        else:
            printer_combo.addItem("No printers found")
        
        # Load last selected printer
        settings = QSettings("BOMManager", "PrintLabels")
        last_printer = settings.value("last_printer", "")
        if last_printer and last_printer in available_printers:
            printer_combo.setCurrentText(last_printer)
        
        # Save printer selection when changed
        def save_printer_selection():
            settings.setValue("last_printer", printer_combo.currentText())
        printer_combo.currentTextChanged.connect(save_printer_selection)
        
        printer_select_layout.addWidget(printer_combo)
        
        printer_layout.addLayout(printer_select_layout)
        
        # Label format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Label Format:"))
        
        format_combo = QComboBox()
        format_combo.addItem("2x1 inch (50.8 x 25.4 mm)")
        format_combo.addItem("4x6 inch (101.6 x 152.4 mm)")
        
        # Load last selected format
        last_format = settings.value("last_format", "2x1 inch (50.8 x 25.4 mm)")
        format_combo.setCurrentText(last_format)
        
        # Save format selection when changed
        def save_format_selection():
            settings.setValue("last_format", format_combo.currentText())
        format_combo.currentTextChanged.connect(save_format_selection)
        
        format_layout.addWidget(format_combo)
        
        printer_layout.addLayout(format_layout)
        printer_group.setLayout(printer_layout)
        print_layout.addWidget(printer_group)
        
        input_group = QGroupBox("Storage Locations")
        input_layout = QVBoxLayout()
        
        # Get all storage locations
        all_locations = []
        for loc in self.storage_locations_data:
            code = loc.get('code', '')
            if code:
                all_locations.append(code)
        
        # Sort locations
        all_locations.sort()
        
        if not all_locations:
            no_locations_label = QLabel("No storage locations found. Create locations first in Storage tab.")
            input_layout.addWidget(no_locations_label)
        else:
            # Scroll area for checkboxes
            from PyQt6.QtWidgets import QScrollArea, QCheckBox
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            # Dictionary to store checkboxes
            location_checkboxes = {}
            
            # Create checkbox for each location
            for location in all_locations:
                checkbox = QCheckBox(location)
                scroll_layout.addWidget(checkbox)
                location_checkboxes[location] = checkbox
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            scroll.setMaximumHeight(300)
            input_layout.addWidget(scroll)
        
        input_group.setLayout(input_layout)
        print_layout.addWidget(input_group)
        
        output_group = QGroupBox("ZPL Code (Copy and send to printer)")
        output_layout = QVBoxLayout()
        
        dialog_print_output = QTextEdit()
        dialog_print_output.setReadOnly(True)
        dialog_print_output.setPlaceholderText("ZPL code will appear here...")
        output_layout.addWidget(dialog_print_output)
        
        buttons_layout = QHBoxLayout()
        
        copy_button = QPushButton("Copy to Clipboard")
        buttons_layout.addWidget(copy_button)
        
        save_button = QPushButton("Save to File")
        buttons_layout.addWidget(save_button)
        
        send_button = QPushButton("Send to Printer")
        if not ZEBRA_AVAILABLE:
            send_button.setEnabled(False)
            send_button.setToolTip("Zebra library not installed. Install with: pip install zebra")
        buttons_layout.addWidget(send_button)
        
        output_layout.addLayout(buttons_layout)
        output_group.setLayout(output_layout)
        print_layout.addWidget(output_group)
        
        # Connect functions
        def generate_label():
            if not all_locations:
                dialog_print_output.setPlainText("")
                return
            
            # Get checked locations
            selected_locations = []
            for location, checkbox in location_checkboxes.items():
                if checkbox.isChecked():
                    selected_locations.append(location)
            
            if not selected_locations:
                dialog_print_output.setPlainText("")
                return
            
            # Get selected format
            format_text = format_combo.currentText()
            is_4x6 = "4x6" in format_text
            
            # Generate ZPL for all selected locations
            all_zpl = ""
            for location in selected_locations:
                if is_4x6:
                    all_zpl += generate_zpl_label_4x6(location) + "\n"
                else:
                    all_zpl += generate_zpl_label(location) + "\n"
            
            dialog_print_output.setPlainText(all_zpl)
        
        # Auto-generate when checkboxes change
        if all_locations:
            for checkbox in location_checkboxes.values():
                checkbox.stateChanged.connect(generate_label)
        
        # Auto-generate when format changes
        format_combo.currentTextChanged.connect(generate_label)
        
        def copy_zpl():
            zpl = dialog_print_output.toPlainText()
            if not zpl:
                QMessageBox.warning(print_dialog, "Error", "No ZPL code to copy! Generate label first.")
                return
            QApplication.clipboard().setText(zpl)
            QMessageBox.information(print_dialog, "Success", "ZPL code copied to clipboard!")
        
        def save_zpl():
            zpl = dialog_print_output.toPlainText()
            if not zpl:
                QMessageBox.warning(print_dialog, "Error", "No ZPL code to save! Generate labels first.")
                return
            
            filename = f"labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zpl"
            try:
                with open(filename, 'w') as f:
                    f.write(zpl)
                QMessageBox.information(print_dialog, "Success", f"ZPL code saved to: {filename}")
            except Exception as e:
                QMessageBox.critical(print_dialog, "Error", f"Error saving file: {str(e)}")
        
        def send_to_printer():
            zpl = dialog_print_output.toPlainText()
            if not zpl:
                QMessageBox.warning(print_dialog, "Error", "No ZPL code to print! Generate labels first.")
                return
            
            printer_name = printer_combo.currentText()
            if printer_name == "No printers found":
                QMessageBox.warning(print_dialog, "Error", "No printer selected!")
                return
            
            # Count selected locations
            selected_count = sum(1 for cb in location_checkboxes.values() if cb.isChecked()) if all_locations else 0
            
            try:
                # Sanitize ZPL content
                sanitized_zpl = sanitize_zpl(zpl)
                
                # Send to printer
                z = Zebra(printer_name)
                z.output(sanitized_zpl)
                
                QMessageBox.information(print_dialog, "Success", f"{selected_count} label(s) sent to printer: {printer_name}")
            except Exception as e:
                QMessageBox.critical(print_dialog, "Error", f"Error sending to printer: {str(e)}")
        
        copy_button.clicked.connect(copy_zpl)
        save_button.clicked.connect(save_zpl)
        send_button.clicked.connect(send_to_printer)
        
        print_dialog.exec()
    
    def open_assign_project_tab(self):
        """Open assign project dialog via toolbar"""
        # Create assign project dialog
        assign_dialog = QDialog(self)
        assign_dialog.setWindowTitle("Assign Part to Project")
        assign_dialog.setMinimumSize(800, 500)
        
        assign_layout = QVBoxLayout(assign_dialog)
        
        title = QLabel("Assign Part to Project")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        assign_layout.addWidget(title)
        
        info = QLabel("Scan part barcode, then enter project name to assign")
        assign_layout.addWidget(info)
        
        input_group = QGroupBox("Assign Part to Project")
        input_layout = QVBoxLayout()
        
        dialog_barcode_input = QLineEdit()
        dialog_barcode_input.setPlaceholderText("Scan part barcode...")
        input_layout.addWidget(QLabel("Part Barcode:"))
        input_layout.addWidget(dialog_barcode_input)
        
        dialog_project_input = QLineEdit()
        dialog_project_input.setPlaceholderText("Enter project name (e.g., ProjectX, Robot2024)...")
        input_layout.addWidget(QLabel("Project Name:"))
        input_layout.addWidget(dialog_project_input)
        
        assign_btn = QPushButton("Assign to Project")
        input_layout.addWidget(assign_btn)
        
        dialog_status = QLabel("Ready to scan part")
        status_font = QFont()
        status_font.setBold(True)
        dialog_status.setFont(status_font)
        input_layout.addWidget(dialog_status)
        
        input_group.setLayout(input_layout)
        assign_layout.addWidget(input_group)
        
        assign_layout.addStretch()
        
        dialog_barcode_input.setFocus()
        assign_dialog.exec()
    
    def open_project_overview_tab(self):
        """Open project overview dialog via toolbar"""
        # Create project overview dialog
        overview_dialog = QDialog(self)
        overview_dialog.setWindowTitle("Project Overview")
        overview_dialog.setMinimumSize(800, 600)
        
        overview_layout = QVBoxLayout(overview_dialog)
        
        title = QLabel("Project Overview")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        overview_layout.addWidget(title)
        
        dialog_overview_text = QTextEdit()
        dialog_overview_text.setReadOnly(True)
        overview_layout.addWidget(dialog_overview_text)
        
        refresh_btn = QPushButton("Refresh Project List")
        overview_layout.addWidget(refresh_btn)
        
        # Populate with current project data
        def refresh_overview():
            projects_dict = {}
            
            for scan_data in self.scanned_codes:
                parsed = scan_data.get('parsed', {})
                part_name = parsed.get('PN', 'Unknown')
                qty = parsed.get('QTY', '0')
                location = parsed.get('LOCATION', 'Not assigned')
                projects = parsed.get('PROJECTS', [])
                
                for project in projects:
                    if project not in projects_dict:
                        projects_dict[project] = []
                    
                    projects_dict[project].append({
                        'part': part_name,
                        'qty': qty,
                        'location': location
                    })
            
            if not projects_dict:
                output = "No projects assigned yet.\\n\\nUse 'Assign to Project' to assign parts to projects."
            else:
                output = f"TOTAL PROJECTS: {len(projects_dict)}\\n\\n"
                output += "=" * 60 + "\\n\\n"
                
                for project_name, parts in sorted(projects_dict.items()):
                    output += f"PROJECT: {project_name}\\n"
                    output += "-" * 60 + "\\n"
                    output += f"Parts count: {len(parts)}\\n\\n"
                    
                    for part_info in parts:
                        output += f"  \u2022 {part_info['part']}\\n"
                        output += f"    Quantity: {part_info['qty']}\\n"
                        output += f"    Location: {part_info['location']}\\n\\n"
                    
                    output += "\\n"
            
            dialog_overview_text.setPlainText(output)
        
        refresh_btn.clicked.connect(refresh_overview)
        refresh_overview()  # Initial load
        
        overview_dialog.exec()
    
    def init_scan_tab(self):
        """Initialize scanning tab"""
        scan_layout = QVBoxLayout(self.scan_tab)
        
        # Scanning group - more compact
        scan_group = QGroupBox("Scanning")
        scan_group_layout = QHBoxLayout()
        
        scan_group_layout.addWidget(QLabel("Barcode:"))
        
        # Text field for scanning
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan or enter barcode...")
        font = QFont()
        font.setPointSize(12)
        self.barcode_input.setFont(font)
        
        # Connect events
        self.barcode_input.returnPressed.connect(self.process_barcode)
        self.barcode_input.textChanged.connect(self.on_text_changed)
        
        scan_group_layout.addWidget(self.barcode_input)
        
        self.clear_field_button = QPushButton("Clear")
        self.clear_field_button.clicked.connect(self.clear_input)
        scan_group_layout.addWidget(self.clear_field_button)
        
        self.manual_add_button = QPushButton("Add")
        self.manual_add_button.clicked.connect(self.manual_add)
        scan_group_layout.addWidget(self.manual_add_button)
        scan_group.setLayout(scan_group_layout)
        scan_layout.addWidget(scan_group)
        
        # Add stretch to push scanning controls to top
        scan_layout.addStretch()
        
        # Info label
        info_label = QLabel("Scan barcodes with your Zebra scanner or enter them manually")
        scan_layout.addWidget(info_label)
    
    def init_scan_tab_in_dialog(self, layout):
        """Initialize scanning interface in a dialog"""
        title = QLabel("Barcode Scanning")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel("Scan parts with your Zebra barcode reader")
        layout.addWidget(info)
        
        # Scanning group
        scan_group = QGroupBox("Barcode Input")
        scan_group_layout = QHBoxLayout()
        
        scan_group_layout.addWidget(QLabel("Barcode:"))
        
        # Text field for scanning
        barcode_input_dialog = QLineEdit()
        barcode_input_dialog.setPlaceholderText("Scan or enter barcode...")
        font = QFont()
        font.setPointSize(12)
        barcode_input_dialog.setFont(font)
        
        # Connect to main processing
        def process_and_clear():
            self.process_barcode_from_text(barcode_input_dialog.text())
            barcode_input_dialog.clear()
            barcode_input_dialog.setFocus()
        
        barcode_input_dialog.returnPressed.connect(process_and_clear)
        barcode_input_dialog.textChanged.connect(lambda: self.on_text_changed_dialog(barcode_input_dialog))
        
        scan_group_layout.addWidget(barcode_input_dialog)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(barcode_input_dialog.clear)
        scan_group_layout.addWidget(clear_button)
        
        add_button = QPushButton("Add")
        add_button.clicked.connect(process_and_clear)
        scan_group_layout.addWidget(add_button)
        
        scan_group.setLayout(scan_group_layout)
        layout.addWidget(scan_group)
        
        layout.addStretch()
        
        info_label = QLabel("After scanning, the dialog will close and part will be added to BOM table")
        layout.addWidget(info_label)
        
        barcode_input_dialog.setFocus()
    
    def process_barcode_from_text(self, text):
        """Process barcode from dialog input"""
        if text.strip():
            # Store text in main barcode_input so process_barcode can read it
            self.barcode_input.setText(text)
            self.process_barcode()
            # Clear both inputs after processing
            self.barcode_input.clear()
    
    def on_text_changed_dialog(self, input_widget):
        """Handle text change in dialog with auto-process after 1000ms"""
        text = input_widget.text()
        
        if len(text) > 500:
            input_widget.setText(text[:500])
            return
        
        if text.strip():
            # Create or reset timer for auto-processing
            if hasattr(self, 'scan_dialog_timer'):
                self.scan_dialog_timer.stop()
            else:
                self.scan_dialog_timer = QTimer()
                self.scan_dialog_timer.setSingleShot(True)
                
            # Store reference to input widget for clearing later
            self.scan_dialog_input = input_widget
            
            # Connect to processing function
            self.scan_dialog_timer.timeout.connect(lambda: self.auto_process_scan_dialog())
            
            # Start timer (1000ms = 1 second)
            self.scan_dialog_timer.start(1000)
    
    def auto_process_scan_dialog(self):
        """Auto-process barcode from dialog after timer"""
        if hasattr(self, 'scan_dialog_input'):
            text = self.scan_dialog_input.text()
            if text.strip():
                self.process_barcode_from_text(text)
                self.scan_dialog_input.clear()
                self.scan_dialog_input.setFocus()
    
    def on_allocate_text_changed(self):
        """Auto-process allocation barcode after 1000ms delay"""
        text = self.allocate_barcode_input.text()
        
        if len(text) > 500:
            self.allocate_barcode_input.setText(text[:500])
            return
        
        if text.strip():
            if hasattr(self, 'allocate_timer'):
                self.allocate_timer.stop()
            else:
                self.allocate_timer = QTimer()
                self.allocate_timer.setSingleShot(True)
                self.allocate_timer.timeout.connect(self.process_allocation_barcode)
            
            self.allocate_timer.start(1000)
    
    def process_allocation_barcode(self):
        """Process barcode in allocation workflow"""
        raw_barcode = self.allocate_barcode_input.text().strip()
        
        if not raw_barcode:
            return
        
        if self.allocation_state == "waiting_for_part":
            # Step 1: Scan part barcode
            self.process_part_selection(raw_barcode)
        elif self.allocation_state == "waiting_for_location":
            # Step 2: Scan location barcode
            self.process_location_assignment(raw_barcode)
        
        self.allocate_barcode_input.clear()
        self.allocate_barcode_input.setFocus()
    
    def process_part_selection(self, raw_barcode):
        """Select part by scanning its barcode"""
        # Parse barcode to get PN/MPN
        parsed_data = parse_bom_barcode(raw_barcode)
        
        if not parsed_data:
            # Try to match raw barcode directly
            search_key = raw_barcode
        else:
            search_key = parsed_data.get('PN') or parsed_data.get('MPN') or raw_barcode
        
        # Find part in scanned_codes
        found_index = None
        for idx, scan_data in enumerate(self.scanned_codes):
            existing_parsed = scan_data.get('parsed', {})
            existing_key = existing_parsed.get('PN') or existing_parsed.get('MPN')
            
            if existing_key == search_key or scan_data.get('code') == raw_barcode:
                found_index = idx
                break
        
        if found_index is not None:
            self.selected_part_index = found_index
            scan_data = self.scanned_codes[found_index]
            parsed = scan_data.get('parsed', {})
            
            # Update UI
            self.allocation_state = "waiting_for_location"
            self.allocate_status.setText("Part selected! Now scan STORAGE LOCATION...")
            
            # Show part info
            info_text = f"<b>Part Number:</b> {parsed.get('PN', 'N/A')}<br>"
            info_text += f"<b>MPN:</b> {parsed.get('MPN', 'N/A')}<br>"
            info_text += f"<b>QTY:</b> {parsed.get('QTY', 'N/A')}<br>"
            info_text += f"<b>Manufacturer:</b> {parsed.get('MFR', 'N/A')}"
            
            current_location = parsed.get('LOCATION', 'Not assigned')
            info_text += f"<br><b>Current Location:</b> <span style='color: #F44336;'>{current_location}</span>"
            
            self.current_part_info.setText(info_text)
            self.current_part_group.setVisible(True)
            
            print(f"📦 Part selected: {parsed.get('PN', 'N/A')} - waiting for location scan")
        else:
            # Part not found
            self.allocate_status.setText("Part NOT FOUND! Try scanning again...")
            print(f"Part not found for barcode: {raw_barcode}")
    
    def process_location_assignment(self, location_barcode):
        """Assign storage location to selected part"""
        if self.selected_part_index is None:
            return
        
        # Location barcode can be simple text/code
        location_code = location_barcode.strip()
        
        # Update part with location
        scan_data = self.scanned_codes[self.selected_part_index]
        parsed = scan_data.get('parsed', {})
        parsed['LOCATION'] = location_code
        
        # Update table
        self.bom_table.item(self.selected_part_index, 9).setText(location_code)
        
        # Highlight row
        for col in range(self.bom_table.columnCount()):
            item = self.bom_table.item(self.selected_part_index, col)
            if item:
                item.setBackground(QColor("#BBDEFB"))  # Blue for location update
        
        # Cancel highlight after 3 seconds
        row_to_reset = self.selected_part_index  # Save index before reset
        QTimer.singleShot(3000, lambda: self.reset_row_color(row_to_reset))
        
        # Save changes
        self.save_bom()
        
        # Show success message
        part_name = parsed.get('PN', 'Part')
        self.allocate_status.setText(f"SUCCESS! {part_name} -> {location_code}")
        
        print(f"Location assigned: {part_name} -> {location_code}")
        
        # Reset state after 2 seconds
        QTimer.singleShot(2000, self.reset_allocation_state)
    
    def reset_allocation_state(self):
        """Reset allocation workflow to initial state"""
        self.allocation_state = "waiting_for_part"
        self.selected_part_index = None
        self.allocate_status.setText("Waiting to scan part...")
        self.current_part_group.setVisible(False)
        self.allocate_barcode_input.setFocus()
    
    def clear_allocate_input(self):
        """Clear allocation input field"""
        self.allocate_barcode_input.clear()
        self.allocate_barcode_input.setFocus()
    
    def cancel_allocation(self):
        """Cancel current allocation and reset"""
        self.reset_allocation_state()
        print("🚫 Allocation cancelled")
    
    def init_allocate_tab(self):
        """Initialize allocation tab for assigning storage locations"""
        allocate_layout = QVBoxLayout(self.allocate_tab)
        
        # Instructions
        instructions = QLabel("Two-Step Process: 1. Scan Part -> 2. Scan Storage Location")
        instructions_font = QFont()
        instructions_font.setPointSize(13)
        instructions_font.setBold(True)
        instructions.setFont(instructions_font)
        allocate_layout.addWidget(instructions)
        
        # Status display
        self.allocate_status = QLabel("Waiting to scan part...")
        status_font = QFont()
        status_font.setPointSize(14)
        status_font.setBold(True)
        self.allocate_status.setFont(status_font)
        allocate_layout.addWidget(self.allocate_status)
        
        # Current part info (shown after scanning part)
        self.current_part_group = QGroupBox("Current Part")
        current_part_layout = QVBoxLayout()
        self.current_part_info = QLabel("No part selected")
        self.current_part_info.setStyleSheet("font-size: 12pt; padding: 10px;")
        current_part_layout.addWidget(self.current_part_info)
        self.current_part_group.setLayout(current_part_layout)
        self.current_part_group.setVisible(False)
        allocate_layout.addWidget(self.current_part_group)
        
        # Barcode input for allocation
        allocate_group = QGroupBox("Barcode Scanner")
        allocate_group_layout = QHBoxLayout()
        
        allocate_group_layout.addWidget(QLabel("Scan:"))
        
        self.allocate_barcode_input = QLineEdit()
        self.allocate_barcode_input.setPlaceholderText("Scan part or location barcode...")
        font = QFont()
        font.setPointSize(12)
        self.allocate_barcode_input.setFont(font)
        
        # Connect events
        self.allocate_barcode_input.returnPressed.connect(self.process_allocation_barcode)
        self.allocate_barcode_input.textChanged.connect(self.on_allocate_text_changed)
        
        allocate_group_layout.addWidget(self.allocate_barcode_input)
        
        clear_allocate_button = QPushButton("Clear")
        clear_allocate_button.clicked.connect(self.clear_allocate_input)
        allocate_group_layout.addWidget(clear_allocate_button)
        
        cancel_allocate_button = QPushButton("Cancel")
        cancel_allocate_button.clicked.connect(self.cancel_allocation)
        allocate_group_layout.addWidget(cancel_allocate_button)
        
        allocate_group.setLayout(allocate_group_layout)
        allocate_layout.addWidget(allocate_group)
        
        # Add stretch
        allocate_layout.addStretch()
        
        # Info label
        allocate_info_label = QLabel("Step 1: Scan the part barcode to select it\nStep 2: Scan the storage location barcode to assign")
        allocate_layout.addWidget(allocate_info_label)
        
        # Allocation state
        self.allocation_state = "waiting_for_part"  # Can be: waiting_for_part, waiting_for_location
        self.selected_part_index = None
    
    def init_print_tab(self):
        """Initialize label printing tab"""
        print_layout = QVBoxLayout(self.print_tab)
        
        # Title
        title = QLabel("ZPL Label Generator for Storage Locations")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        print_layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("Label Configuration")
        input_layout = QVBoxLayout()
        
        # Location code input
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Storage Location:"))
        
        self.print_location_input = QLineEdit()
        self.print_location_input.setPlaceholderText("Enter location code (e.g., A1, B23, SHELF-05)...")
        location_font = QFont()
        location_font.setPointSize(12)
        self.print_location_input.setFont(location_font)
        self.print_location_input.textChanged.connect(self.update_zpl_preview)
        location_layout.addWidget(self.print_location_input)
        
        input_layout.addLayout(location_layout)
        
        # Info about label size
        info_label = QLabel("Label Size: 2 x 1 inch (50.8 x 25.4 mm) | Resolution: 203 DPI")
        input_layout.addWidget(info_label)
        
        input_group.setLayout(input_layout)
        print_layout.addWidget(input_group)
        
        # ZPL Preview
        preview_group = QGroupBox("ZPL Code Preview")
        preview_layout = QVBoxLayout()
        
        self.zpl_preview = QTextEdit()
        self.zpl_preview.setReadOnly(True)
        self.zpl_preview.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11pt;")
        self.zpl_preview.setMaximumHeight(200)
        preview_layout.addWidget(self.zpl_preview)
        
        preview_group.setLayout(preview_layout)
        print_layout.addWidget(preview_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate ZPL Code")
        generate_btn.clicked.connect(self.generate_zpl)
        button_layout.addWidget(generate_btn)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_zpl_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_zpl_to_file)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        print_layout.addLayout(button_layout)
        
        # Part category info
        category_group = QGroupBox("Part Number Categories")
        category_layout = QVBoxLayout()
        
        categories_text = """
<b>Part numbering system:</b><br>
<b>1xx</b> - Electronic Components (e.g., 155 = component ID 55)<br>
<b>2xx</b> - Screws (e.g., 2010 = screw ID 010)<br>
<b>3xx</b> - Nuts (e.g., 345 = nut ID 45)<br>
<b>4xx</b> - Bearings (e.g., 4100 = bearing ID 100)<br>
<b>5xx</b> - Cables (e.g., 512 = cable ID 12)
        """
        
        category_label = QLabel(categories_text)
        category_layout.addWidget(category_label)
        
        category_group.setLayout(category_layout)
        print_layout.addWidget(category_group)
        
        # Add stretch
        print_layout.addStretch()
        
        # Initialize with empty preview
        self.update_zpl_preview()
        
    def update_zpl_preview(self):
        """Update ZPL preview when location input changes"""
        location = self.print_location_input.text().strip()
        if location:
            zpl = generate_zpl_label(location)
            self.zpl_preview.setPlainText(zpl)
        else:
            self.zpl_preview.setPlainText("Enter a location code to generate ZPL...")
    
    def generate_zpl(self):
        """Generate and display ZPL code"""
        location = self.print_location_input.text().strip()
        
        if not location:
            QMessageBox.warning(self, "Missing Input", "Please enter a storage location code.")
            return
        
        zpl = generate_zpl_label(location)
        self.zpl_preview.setPlainText(zpl)
        
        QMessageBox.information(
            self,
            "ZPL Generated",
            f"ZPL code generated for location: {location}\n\nYou can now copy it or save to file."
        )
    
    def copy_zpl_to_clipboard(self):
        """Copy ZPL code to clipboard"""
        zpl_text = self.zpl_preview.toPlainText()
        
        if not zpl_text or zpl_text.startswith("Enter a location"):
            QMessageBox.warning(self, "No ZPL Code", "Generate ZPL code first.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(zpl_text)
        
        QMessageBox.information(self, "Copied", "ZPL code copied to clipboard!")
    
    def save_zpl_to_file(self):
        """Save ZPL code to file"""
        zpl_text = self.zpl_preview.toPlainText()
        
        if not zpl_text or zpl_text.startswith("Enter a location"):
            QMessageBox.warning(self, "No ZPL Code", "Generate ZPL code first.")
            return
        
        location = self.print_location_input.text().strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"label_{location}_{timestamp}.zpl"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(zpl_text)
            
            QMessageBox.information(
                self,
                "File Saved",
                f"ZPL code saved to:\n{filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save file:\n{str(e)}"
            )
        
    def on_text_changed(self):
        """Automatic processing after 1000ms from last character (for readers without Enter)"""
        text = self.barcode_input.text()
        
        # Protection against too long text
        if len(text) > 500:
            self.barcode_input.setText(text[:500])
            return
        
        # If text is not empty, set timer for automatic processing
        if text.strip():
            self.auto_process_timer.stop()  # Cancel previous timer
            self.auto_process_timer.start(100)  # Start new timer for 500ms (0.5 second)
    
    def auto_process_barcode(self):
        """Automatic code processing after time delay"""
        if self.barcode_input.text().strip() and not self.is_processing:
            print("⏰ AUTO_PROCESS: Automatic processing after 1 second")
            self.process_barcode()
            
    def process_barcode(self):
        """Process scanned barcode from text field"""
        # Prevention of duplicate processing
        if self.is_processing:
            print("🚨 PROCESS_BARCODE: Already processing, skipping...")
            return
            
        self.is_processing = True
        print("🚨 PROCESS_BARCODE: Method was called!")
        
        raw_barcode = self.barcode_input.text().strip()
        
        print(f"🚨 PROCESS_BARCODE: Raw barcode text: '{raw_barcode}'")
        print(f"🚨 PROCESS_BARCODE: Text length: {len(raw_barcode)}")
        
        if not raw_barcode:
            print("🚨 PROCESS_BARCODE: Empty text, skipping")
            self.is_processing = False
            return
        
        # FIX: Apply Czech keyboard fixes FIRST
        raw_barcode = fix_czech_chars(raw_barcode)
        print(f"🚨 PROCESS_BARCODE: After fix_czech_chars: '{raw_barcode}'")
        
        # Code processing
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Attempt to parse BOM data
        parsed_data = parse_bom_barcode(raw_barcode)
        
        # If not parsed OR no PN was found, try to identify source
        if not parsed_data or not parsed_data.get('PN'):
            is_prumex_id = raw_barcode.isdigit() and len(raw_barcode) == 6
            
            # Check if it's a Prumex ID (6-digit number)
            if is_prumex_id:
                print(f"🔍 Detected Prumex ID: {raw_barcode}")
                # Try to fetch from prumex.cz via search
                try:
                    import re
                    import json
                    # Step 1: Search for the product
                    search_url = f"https://www.prumex.cz/hledani/?q={raw_barcode}"
                    print(f"🔎 Searching Prumex: {search_url}")
                    response = requests.get(search_url, timeout=10)
                    
                    if response.status_code == 200:
                        html = response.text
                        
                        # Step 2: Extract product data from JSON in dataLayer
                        # Prumex uses JavaScript and stores products in dataLayer
                        json_match = re.search(r'"products":\[(.*?)\]\}\}\);', html, re.DOTALL)
                        
                        product_url = None
                        product_name = None
                        
                        if json_match:
                            try:
                                # Parse JSON data
                                json_str = '[' + json_match.group(1) + ']'
                                products_data = json.loads(json_str)
                                
                                if products_data and len(products_data) > 0:
                                    # Take first product and extract all data from JSON
                                    first_product = products_data[0]
                                    product_url = first_product.get('url', '').replace('\\/', '/')
                                    product_name = first_product.get('name', '')
                                    sku = first_product.get('sku', raw_barcode)
                                    brand = first_product.get('brand', 'Prumex')
                                    price = first_product.get('price', '')
                                    availability = first_product.get('availability', '')
                                    
                                    # Get description from categories if available
                                    categories = first_product.get('categories', [])
                                    description = ' > '.join(categories) if categories else product_name
                                    
                                    print(f"✓ Found product in JSON: {product_name}")
                                    print(f"✓ URL: {product_url}")
                                    print(f"📋 SKU: {sku}")
                                    print(f"🏭 Brand: {brand}")
                                    print(f"💰 Price: {price}")
                                    print(f"📦 Availability: {availability}")
                                    print(f"📂 Categories: {description}")
                                    
                                    # Create parsed_data directly from JSON with ALL available info
                                    if not parsed_data:
                                        parsed_data = {}
                                    
                                    parsed_data['PN'] = raw_barcode  # Scanned ID
                                    parsed_data['MPN'] = sku  # Real SKU from Prumex
                                    # Set MFR - if it's "Nezařazené", use "Unknown" instead
                                    if brand and brand.lower() != 'nezařazené':
                                        parsed_data['MFR'] = brand
                                    else:
                                        parsed_data['MFR'] = 'Unknown'
                                    parsed_data['VALUE'] = shorten_prumex_name(product_name)
                                    parsed_data['URL'] = product_url
                                    parsed_data['raw'] = raw_barcode
                                    parsed_data['cleaned'] = raw_barcode
                                    if not parsed_data.get('QTY'):
                                        parsed_data['QTY'] = '1'
                                    
                                    # Add price and availability to CoO field (temporary storage)
                                    extra_info = []
                                    if price:
                                        extra_info.append(f"Price: {price}")
                                    if availability:
                                        extra_info.append(f"Stock: {availability}")
                                    if extra_info:
                                        parsed_data['CoO'] = ' | '.join(extra_info)
                                    
                                    print(f"✓ Prumex product successfully parsed!")
                                    print(f"✓ All data extracted from JSON")
                            except json.JSONDecodeError as je:
                                print(f"⚠️ JSON parse error: {je}")
                        
                        # Only try HTML fallback if JSON parsing completely failed
                        if not parsed_data:
                            product_link_match = re.search(r'href="(/produkt/[^"]+)"', html)
                        else:
                            product_link_match = None
                        
                        # Only fetch product page if we didn't get data from JSON
                        if not parsed_data and product_link_match:
                            if not product_url:
                                product_path = product_link_match.group(1)
                                product_url = f"https://www.prumex.cz{product_path}"
                                print(f"✓ Found product link: {product_url}")
                            
                            # Step 3: Fetch the actual product page to get article code
                            product_response = requests.get(product_url, timeout=10)
                            if product_response.status_code == 200:
                                product_html = product_response.text
                                
                                # Extract article code (Kód artiklu) which is the real Prumex ID
                                article_code_match = re.search(r'Kód artiklu:.*?<dd[^>]*>\s*(\d+)\s*</dd>', product_html, re.DOTALL | re.IGNORECASE)
                                if article_code_match:
                                    article_code = article_code_match.group(1).strip()
                                    print(f"✓ Found Article Code (Kód artiklu): {article_code}")
                                    # Use article code as PN if it matches what we searched for
                                    if article_code == raw_barcode:
                                        print(f"✓ Article code matches scanned barcode!")
                                
                                # Extract product name (in <h1> tag)
                                name_match = re.search(r'<h1[^>]*>(.*?)</h1>', product_html, re.DOTALL)
                                product_name = name_match.group(1).strip() if name_match else ''
                                product_name = re.sub(r'<[^>]+>', '', product_name).strip()  # Remove HTML tags
                                
                                # Extract SKU (Katalogové číslo)
                                sku_match = re.search(r'Katalogové číslo:.*?<dd[^>]*>(.*?)</dd>', product_html, re.DOTALL | re.IGNORECASE)
                                sku = sku_match.group(1).strip() if sku_match else raw_barcode
                                sku = re.sub(r'<[^>]+>', '', sku).strip()
                                
                                if not parsed_data:
                                    parsed_data = {}
                                
                                parsed_data['PN'] = raw_barcode  # Keep scanned barcode as PN
                                parsed_data['MPN'] = sku
                                parsed_data['MFR'] = 'Prumex'
                                parsed_data['VALUE'] = shorten_prumex_name(product_name)
                                parsed_data['URL'] = product_url
                                parsed_data['raw'] = raw_barcode
                                parsed_data['cleaned'] = raw_barcode
                                if not parsed_data.get('QTY'):
                                    parsed_data['QTY'] = '1'
                                
                                print(f"✓ Prumex product: {product_name}")
                                print(f"📋 SKU: {sku}")
                            else:
                                print(f"⚠️ Could not fetch product page (HTTP {product_response.status_code})")
                        
                        # Final fallback only if still no data
                        if not parsed_data:
                            print(f"⚠️ No product data found, creating minimal entry")
                            parsed_data = {}
                            parsed_data['PN'] = raw_barcode
                            parsed_data['MPN'] = raw_barcode
                            parsed_data['MFR'] = 'Prumex'
                            parsed_data['VALUE'] = f"Prumex ID: {raw_barcode}"
                            parsed_data['raw'] = raw_barcode
                            parsed_data['cleaned'] = raw_barcode
                            if not parsed_data.get('QTY'):
                                parsed_data['QTY'] = '1'
                    else:
                        print(f"⚠️ Prumex search failed (HTTP {response.status_code})")
                        parsed_data = {}
                        parsed_data['PN'] = raw_barcode
                        parsed_data['MPN'] = raw_barcode
                        parsed_data['MFR'] = 'Prumex'
                        parsed_data['VALUE'] = f"Prumex ID: {raw_barcode} (search failed)"
                        parsed_data['raw'] = raw_barcode
                        parsed_data['cleaned'] = raw_barcode
                        parsed_data['QTY'] = '1'
                except Exception as e:
                    print(f"⚠️ Error fetching from Prumex: {e}")
                    import traceback
                    traceback.print_exc()
                    parsed_data = {}
                    parsed_data['PN'] = raw_barcode
                    parsed_data['MPN'] = raw_barcode
                    parsed_data['MFR'] = 'Prumex'
                    parsed_data['VALUE'] = f"Prumex ID: {raw_barcode} (error)"
                    parsed_data['raw'] = raw_barcode
                    parsed_data['cleaned'] = raw_barcode
                    parsed_data['QTY'] = '1'
            
            # Only try TME if it's NOT a Prumex ID
            if not is_prumex_id and (not parsed_data or not parsed_data.get('PN')):
                print(f"🔍 No PN found, trying TME fuzzy search for: '{raw_barcode}'")
                tme_symbol = find_tme_symbol_fuzzy(raw_barcode, self.tme_api)
            else:
                tme_symbol = None
            
            if tme_symbol:
                print(f"✓ TME fuzzy match found: {tme_symbol}")
                
                # Create parsed_data if it doesn't exist
                if not parsed_data:
                    parsed_data = {}
                
                parsed_data['PN'] = tme_symbol
                
                # Try to get more info from TME
                try:
                    products = self.tme_api.get_products([tme_symbol])
                    if products.get('Data', {}).get('ProductList'):
                        product = products['Data']['ProductList'][0]
                        description = product.get('Description', '')
                        print(f"📦 TME Product Description: {description}")
                        
                        # Get detailed parameters
                        params_response = self.tme_api.get_parameters([tme_symbol])
                        if params_response.get('Data', {}).get('ProductList'):
                            param_product = params_response['Data']['ProductList'][0]
                            parameters = param_product.get('ParameterList', [])
                            
                            # Build detailed description from parameters
                            param_values = []
                            for param in parameters:
                                param_name = param.get('ParameterName', '')
                                param_value = param.get('ParameterValue', '')
                                if param_value:
                                    param_values.append(f"{param_name}: {param_value}")
                            
                            if param_values:
                                description = '; '.join(param_values)
                                print(f"📋 TME Parameters: {description}")
                        
                        if not parsed_data.get('MFR'):
                            parsed_data['MFR'] = product.get('Producer', '')
                        if not parsed_data.get('MPN'):
                            parsed_data['MPN'] = product.get('OriginalSymbol', '')
                        # Always set VALUE from TME description/parameters
                        parsed_data['VALUE'] = description
                        # Generate proper TME URL
                        parsed_data['URL'] = f"https://www.tme.eu/cz/details/{tme_symbol}/"
                        if not parsed_data.get('QTY'):
                            parsed_data['QTY'] = '1'  # Default quantity
                        # Store cleaned text
                        parsed_data['raw'] = raw_barcode
                        parsed_data['cleaned'] = raw_barcode
                        
                        print(f"✓ Parsed data VALUE: {parsed_data.get('VALUE', 'NONE')}")
                        print(f"✓ TME URL: {parsed_data['URL']}")
                except Exception as e:
                    print(f"Error fetching TME product details: {e}")
        
        # Check if part already exists
        existing_index = self.find_existing_part(parsed_data, raw_barcode)
        
        if existing_index is not None:
            # Part already exists - increase quantity by QTY from new scan
            new_qty = parsed_data.get('QTY', '1') if parsed_data else '1'
            self.increment_existing_part(existing_index, timestamp, new_qty)
            return
        
        scan_data = {
            'code': raw_barcode,
            'timestamp': timestamp,
            'length': len(raw_barcode),
            'parsed': parsed_data,
            'history': [timestamp]  # Add history
        }
        
        # Add to list
        self.scanned_codes.append(scan_data)
        
        # Detail display
        if parsed_data:
            detail_text = "📦 PART - PARSED DATA\n"
            detail_text += "=" * 50 + "\n\n"
            
            # Main information
            if 'PN' in parsed_data:
                category = get_part_category(parsed_data['PN'], parsed_data.get('VALUE'), self.tme_api)
                detail_text += f"📝 Part Number:    {parsed_data['PN']}\n"
                detail_text += f"🏷️  Category:       {category}\n"
            if 'MPN' in parsed_data:
                detail_text += f"🏷️  MPN:            {parsed_data['MPN']}\n"
            if 'QTY' in parsed_data:
                detail_text += f"📊 Quantity:       {parsed_data['QTY']}\n"
            if 'MFR' in parsed_data:
                detail_text += f"🏭 Manufacturer:   {parsed_data['MFR']}\n"
            if 'CoO' in parsed_data:
                detail_text += f"🌍 Country of Origin: {parsed_data['CoO']}\n"
            if 'PO' in parsed_data:
                detail_text += f"PO:             {parsed_data['PO']}\n"
            if 'RoHS' in parsed_data:
                detail_text += f"RoHS:           Yes\n"
            if 'URL' in parsed_data:
                detail_text += f"\n🔗 URL:\n   {parsed_data['URL']}\n"
            
            detail_text += "\n" + "-" * 50 + "\n"
            if 'cleaned' in parsed_data:
                detail_text += f"📄 Cleaned text:\n{parsed_data['cleaned']}\n"
            detail_text += "\n" + "-" * 50 + "\n"
            if 'raw' in parsed_data:
                detail_text += f"📝 Original text:\n{parsed_data['raw']}"
            else:
                detail_text += f"📝 Raw barcode:\n{raw_barcode}"
        else:
            detail_text = f"📄 RAW DATA (not parsed)\n"
            detail_text += "=" * 50 + "\n\n"
            detail_text += raw_barcode
        
        # Show detail in console
        if parsed_data:
            print(f"\n{'='*60}")
            print(detail_text)
            print(f"{'='*60}\n")
        
        # Add to table
        row = self.bom_table.rowCount()
        self.bom_table.insertRow(row)
        
        # Highlight new row
        for col in range(self.bom_table.columnCount()):
            item = QTableWidgetItem()
            item.setBackground(QColor("#e8f5e9"))  # Light green
            self.bom_table.setItem(row, col, item)
        
        # Get part number
        part_number = parsed_data.get('PN', '') if parsed_data else ''
        
        # Set temporary ID (will be updated when TME API returns)
        self.bom_table.item(row, 0).setText("...")  # Placeholder
        
        if parsed_data:
            self.bom_table.item(row, 1).setText(parsed_data.get('QTY', ''))
            self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
            self.bom_table.item(row, 3).setText(parsed_data.get('VALUE', ''))
            self.bom_table.item(row, 4).setText(shorten_footprint(parsed_data.get('FOOTPRINT', '')))
            self.bom_table.item(row, 5).setText(parsed_data.get('MPN', ''))
            self.bom_table.item(row, 6).setText(parsed_data.get('MFR', ''))
            self.bom_table.item(row, 7).setText(parsed_data.get('LCSC', ''))
            self.bom_table.item(row, 8).setText(parsed_data.get('FOOTPRINT', ''))
            self.bom_table.item(row, 9).setText(parsed_data.get('LOCATION', ''))
            projects = parsed_data.get('PROJECTS', [])
            self.bom_table.item(row, 10).setText(', '.join(projects) if projects else '')
            self.bom_table.item(row, 11).setText(parsed_data.get('PO', ''))
        else:
            # If cannot parse, put raw data in PN
            self.bom_table.item(row, 2).setText(raw_barcode[:50])
        
        self.bom_table.item(row, 12).setText(timestamp.split()[1])  # Time only
        
        # Scroll to end
        self.bom_table.scrollToBottom()
        
        # Cancel highlight after 2 seconds
        QTimer.singleShot(2000, lambda: self.reset_row_color(row))
        
        # Start async TME API call for category and ID (only if we have part number)
        if part_number:
            value = parsed_data.get('VALUE', '') if parsed_data else ''
            self.fetch_category_async(row, part_number, value)
        else:
            # No part number - use Unknown category immediately
            part_id = generate_category_id("Unknown", self.category_prefixes, self.category_counters)
            self.bom_table.item(row, 0).setText(part_id)
        
        # Update statistics
        self.update_stats()
        
        # Automatic save to CSV
        self.save_bom()
        
        # Clear field
        self.barcode_input.clear()
        
        # Return focus
        self.barcode_input.setFocus()
        
        print(f"PROCESS_BARCODE: Successfully processed! Total scanned: {len(self.scanned_codes)}")
        
        # Reset processing flag
        QTimer.singleShot(100, lambda: setattr(self, 'is_processing', False))
    
    def fetch_category_async(self, row, part_number, value=None):
        """Fetch category from TME API in background thread and update ID"""
        def worker():
            try:
                # Call TME API to get category
                category = get_part_category(part_number, value, self.tme_api) if self.tme_api else "Unknown"
                return category
            except Exception as e:
                print(f"Error fetching category for {part_number}: {e}")
                return "Unknown"
        
        def on_complete(category):
            try:
                # Generate ID based on category
                part_id = generate_category_id(category, self.category_prefixes, self.category_counters)
                
                # Update table cell with actual ID
                if row < self.bom_table.rowCount():
                    self.bom_table.item(row, 0).setText(part_id)
                    print(f"✓ Updated row {row} with ID {part_id} (category: {category})")
                
                # Save after ID update
                self.save_bom()
            except Exception as e:
                print(f"Error updating ID for row {row}: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=lambda: on_complete(worker()), daemon=True)
        thread.start()
    
    def find_existing_part(self, parsed_data, raw_barcode):
        """Find existing part in list by PN or MPN"""
        if not parsed_data:
            return None
        
        # Comparison key - prefer PN, then MPN
        search_key = parsed_data.get('PN') or parsed_data.get('MPN')
        if not search_key:
            return None
        
        # Search in existing parts
        for idx, scan_data in enumerate(self.scanned_codes):
            existing_parsed = scan_data.get('parsed')
            
            # Skip if parsed data is missing or None
            if not existing_parsed:
                continue
                
            existing_key = existing_parsed.get('PN') or existing_parsed.get('MPN')
            
            if existing_key == search_key:
                return idx
        
        return None
    
    def increment_existing_part(self, index, timestamp, qty_to_add):
        """Increase quantity of existing part by QTY from new scan and add to history"""
        scan_data = self.scanned_codes[index]
        parsed = scan_data.get('parsed', {})
        
        # Convert qty_to_add to number
        try:
            add_amount = int(qty_to_add)
        except (ValueError, TypeError):
            add_amount = 1  # If cannot convert, add 1
        
        # Increase QTY by quantity from new scan
        current_qty = parsed.get('QTY', '0')
        try:
            new_qty = int(current_qty) + add_amount
        except ValueError:
            new_qty = add_amount  # If cannot convert current, set to new quantity
        
        parsed['QTY'] = str(new_qty)
        scan_data['parsed'] = parsed
        
        # Add to history
        if 'history' not in scan_data:
            scan_data['history'] = [scan_data['timestamp']]
        scan_data['history'].append(timestamp)
        
        # Update table
        self.bom_table.item(index, 1).setText(str(new_qty))
        
        # Update projects column if needed
        projects = parsed.get('PROJECTS', [])
        if self.bom_table.item(index, 10):
            self.bom_table.item(index, 10).setText(', '.join(projects) if projects else '')
        
        # Highlight row
        for col in range(self.bom_table.columnCount()):
            item = self.bom_table.item(index, col)
            if item:
                item.setBackground(QColor("#fff9c4"))  # Yellow for update
        
        # Cancel highlight after 2 seconds
        QTimer.singleShot(2000, lambda: self.reset_row_color(index))
        
        # Scroll to row
        self.bom_table.scrollToItem(self.bom_table.item(index, 0))
        
        # Update and save
        self.update_stats()
        self.save_bom()
        
        # Clear field and return focus
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        
        print(f"🔄 Part updated: {parsed.get('PN', 'N/A')} - added +{add_amount}, new quantity: {new_qty}")
        
        # Reset processing flag
        self.is_processing = False
    
    def reset_row_color(self, row):
        """Reset row color to white"""
        if row is not None and row < self.bom_table.rowCount():
            for col in range(self.bom_table.columnCount()):
                item = self.bom_table.item(row, col)
                if item:
                    item.setBackground(QColor("#ffffff"))
    
    def on_table_double_click(self, row, column):
        """Show detail and history when double-clicking on row"""
        if row < len(self.scanned_codes):
            scan_data = self.scanned_codes[row]
            parsed = scan_data.get('parsed', {})
            
            # Get current storage location from BOM table (column 9)
            storage_item = self.bom_table.item(row, 9)
            if storage_item:
                parsed['LOCATION'] = storage_item.text()
            
            history = scan_data.get('history', [scan_data.get('timestamp')])
            
            # Open dialog with detail
            dialog = PartDetailDialog(parsed, history, scan_data.get('code', ''), self)
            dialog.exec()
    
    def update_category_filter(self):
        """Update category filter dropdown with categories currently in BOM"""
        # Collect all unique categories from BOM
        categories = set()
        
        for scan_data in self.scanned_codes:
            parsed = scan_data.get('parsed', {})
            if not parsed:
                continue
            
            part_number = parsed.get('PN')
            value = parsed.get('VALUE')
            
            if part_number:
                category = get_part_category(part_number, value, self.tme_api)
                categories.add(category)
        
        # Sort categories alphabetically
        sorted_categories = sorted(categories)
        
        # Remember current selection
        current_category = self.category_filter.currentText()
        
        # Update dropdown
        self.category_filter.blockSignals(True)  # Prevent triggering filter while updating
        self.category_filter.clear()
        self.category_filter.addItem("All")
        self.category_filter.addItems(sorted_categories)
        
        # Restore selection if still available
        index = self.category_filter.findText(current_category)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)
        else:
            self.category_filter.setCurrentIndex(0)  # Default to "All"
        
        self.category_filter.blockSignals(False)
    
    def filter_by_category(self, category):
        """Filter BOM table by part category"""
        for row in range(self.bom_table.rowCount()):
            # Get Part Number and Value from row
            pn_item = self.bom_table.item(row, 2)  # Column 2 = Part Number
            value_item = self.bom_table.item(row, 3)  # Column 3 = Value
            
            if not pn_item:
                continue
            
            part_number = pn_item.text()
            value = value_item.text() if value_item else None
            part_category = get_part_category(part_number, value, self.tme_api)
            
            # Show/hide row based on filter
            if category == "All" or part_category == category:
                self.bom_table.setRowHidden(row, False)
            else:
                self.bom_table.setRowHidden(row, True)
        
        print(f"🔍 Filter applied: {category}")
    
    def delete_selected_row(self):
        """Delete selected row from table"""
        current_row = self.bom_table.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self,
                'Confirmation',
                f'Do you really want to delete row #{current_row + 1}?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.bom_table.removeRow(current_row)
                del self.scanned_codes[current_row]
                
                # Renumber rows
                for row in range(self.bom_table.rowCount()):
                    self.bom_table.item(row, 0).setText(str(row + 1))
                
                self.update_stats()
                # Save changes
                self.save_bom()
        else:
            QMessageBox.warning(
                self,
                'Error',
                'Please select a row to delete first.'
            )
    
    def save_bom(self):
        """Automatic BOM save to CSV file"""
        try:
            with open(self.bom_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Header - added Projects column
                writer.writerow(['QTY', 'Part Number', 'Value', 'MPN', 'Manufacturer', 'PO', 'CoO', 'RoHS', 'URL', 'Storage Location', 'Projects', 'Time', 'Raw', 'History'])
                
                # Data
                for scan_data in self.scanned_codes:
                    parsed = scan_data.get('parsed', {})
                    history = scan_data.get('history', [scan_data.get('timestamp')])
                    history_str = '|'.join(history)  # History separated by |
                    
                    # Projects as comma-separated string
                    projects = parsed.get('PROJECTS', [])
                    projects_str = ','.join(projects) if projects else ''
                    
                    row = [
                        parsed.get('QTY', ''),
                        parsed.get('PN', ''),
                        parsed.get('VALUE', ''),
                        parsed.get('MPN', ''),
                        parsed.get('MFR', ''),
                        parsed.get('PO', ''),
                        parsed.get('CoO', ''),
                        'Yes' if 'RoHS' in parsed else 'No',
                        parsed.get('URL', ''),
                        parsed.get('LOCATION', ''),  # Storage location
                        projects_str,  # Projects
                        scan_data.get('timestamp', ''),
                        scan_data.get('code', ''),
                        history_str
                    ]
                    writer.writerow(row)
            
            print(f"💾 BOM automatically saved: {self.bom_file}")
            
            # Update category filter with current categories
            self.update_category_filter()
            
        except Exception as e:
            print(f"Error saving BOM: {str(e)}")
    
    def load_bom(self):
        """Load BOM from file on startup"""
        if not os.path.exists(self.bom_file):
            print(f"ℹ️  BOM file does not exist, a new one will be created: {self.bom_file}")
            return
        
        try:
            with open(self.bom_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                
                for row_data in reader:
                    # Reconstruct parsed data from CSV
                    try:
                        # Support both old (Czech) and new (English) column names
                        parsed_data = {
                            'QTY': row_data.get('QTY', ''),
                            'PN': row_data.get('Part Number', ''),
                            'VALUE': row_data.get('Value', ''),
                            'MPN': row_data.get('MPN', ''),
                            'MFR': row_data.get('Manufacturer', row_data.get('Výrobce', '')),  # Support old Czech name
                            'PO': row_data.get('PO', ''),
                            'CoO': row_data.get('CoO', ''),
                            'URL': row_data.get('URL', ''),
                            'LOCATION': row_data.get('Storage Location', '')  # New column
                        }
                        
                        rohs_value = row_data.get('RoHS', '')
                        if rohs_value in ['Yes', 'Ano']:  # Support both English and Czech
                            parsed_data['RoHS'] = 'Yes'
                        
                        # Load projects
                        projects_str = row_data.get('Projects', '')
                        if projects_str:
                            parsed_data['PROJECTS'] = [p.strip() for p in projects_str.split(',') if p.strip()]
                        else:
                            parsed_data['PROJECTS'] = []
                        
                        # Remove empty values (but keep PROJECTS even if empty)
                        parsed_data = {k: v for k, v in parsed_data.items() if v or k == 'PROJECTS'}
                        
                        # Support both old (Čas) and new (Time) column names
                        timestamp = row_data.get('Time', row_data.get('Čas', ''))
                        
                        # Load history
                        history_str = row_data.get('History', timestamp)
                        history = history_str.split('|') if history_str else [timestamp]
                        
                        scan_data = {
                            'code': row_data.get('Raw', ''),
                            'timestamp': timestamp,
                            'length': len(row_data.get('Raw', '')),
                            'parsed': parsed_data,
                            'history': history
                        }
                    except Exception as row_error:
                        print(f"⚠️ Skipping invalid row: {row_error}")
                        continue
                    
                    self.scanned_codes.append(scan_data)
                    
                    # Add to table
                    row = self.bom_table.rowCount()
                    self.bom_table.insertRow(row)
                    
                    # Create items
                    for col in range(self.bom_table.columnCount()):
                        self.bom_table.setItem(row, col, QTableWidgetItem())
                    
                    # Get category for ID generation
                    part_number = parsed_data.get('PN', '')
                    value = parsed_data.get('VALUE', '')
                    category = get_part_category(part_number, value, self.tme_api) if part_number else "Unknown"
                    
                    # Generate category-based ID
                    part_id = generate_category_id(category, self.category_prefixes, self.category_counters)
                    
                    # Fill data
                    self.bom_table.item(row, 0).setText(part_id)  # Category-based ID
                    self.bom_table.item(row, 1).setText(parsed_data.get('QTY', ''))
                    self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
                    self.bom_table.item(row, 3).setText(parsed_data.get('VALUE', ''))
                    self.bom_table.item(row, 4).setText(shorten_footprint(parsed_data.get('FOOTPRINT', '')))
                    self.bom_table.item(row, 5).setText(parsed_data.get('MPN', ''))
                    self.bom_table.item(row, 6).setText(parsed_data.get('MFR', ''))
                    self.bom_table.item(row, 7).setText(parsed_data.get('LCSC', ''))
                    self.bom_table.item(row, 8).setText(parsed_data.get('FOOTPRINT', ''))
                    self.bom_table.item(row, 9).setText(parsed_data.get('LOCATION', ''))
                    projects = parsed_data.get('PROJECTS', [])
                    self.bom_table.item(row, 10).setText(', '.join(projects) if projects else '')
                    self.bom_table.item(row, 11).setText(parsed_data.get('PO', ''))
                    
                    # Debug: Print storage location
                    if parsed_data.get('LOCATION'):
                        print(f"📍 Loaded part {parsed_data.get('PN')} with storage: {parsed_data.get('LOCATION')}")
                    
                    # Display time only (support both old and new column names)
                    time_str = timestamp.split()[1] if ' ' in timestamp else timestamp
                    self.bom_table.item(row, 12).setText(time_str)
            
            self.update_stats()
            print(f"Loaded {len(self.scanned_codes)} items from BOM")
            
        except Exception as e:
            print(f"Error loading BOM: {str(e)}")
            QMessageBox.warning(
                self,
                'Loading Error',
                f'Failed to load existing BOM:\n{str(e)}'
            )
    
    def load_storage_locations(self):
        """Load storage locations from JSON file on startup"""
        if not os.path.exists(self.storage_file):
            print(f"ℹ️  Storage file does not exist, will be created on first save")
            self.storage_locations_data = []
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                self.storage_locations_data = json.load(f)
            print(f"Loaded {len(self.storage_locations_data)} storage locations")
        except Exception as e:
            print(f"Error loading storage locations: {str(e)}")
            self.storage_locations_data = []
    
    def save_storage_locations(self):
        """Save storage locations to JSON file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.storage_locations_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.storage_locations_data)} storage locations")
        except Exception as e:
            print(f"Error saving storage locations: {str(e)}")
            QMessageBox.warning(self, 'Save Error', f'Failed to save storage locations:\n{str(e)}')
    
    def load_projects(self):
        """Load projects from JSON file on startup"""
        if not os.path.exists(self.projects_file):
            print(f"ℹ️  Projects file does not exist, will be created on first save")
            self.projects_data = []
            return
        
        try:
            with open(self.projects_file, 'r', encoding='utf-8') as f:
                self.projects_data = json.load(f)
            print(f"Loaded {len(self.projects_data)} projects")
        except Exception as e:
            print(f"Error loading projects: {str(e)}")
            self.projects_data = []
    
    def save_projects(self):
        """Save projects to JSON file"""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(self.projects_data)} projects")
        except Exception as e:
            print(f"Error saving projects: {str(e)}")
            QMessageBox.warning(self, 'Save Error', f'Failed to save projects:\n{str(e)}')
        
    def manual_add(self):
        """Manual code addition (same as process_barcode)"""
        self.process_barcode()
        
    def clear_input(self):
        """Clear input field"""
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        
    def clear_list(self):
        """Clear entire list"""
        reply = QMessageBox.question(
            self,
            'Confirmation',
            'Do you really want to clear the entire BOM table?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scanned_codes.clear()
            self.bom_table.setRowCount(0)
            self.update_stats()
            
            # Also delete BOM file
            if os.path.exists(self.bom_file):
                os.remove(self.bom_file)
                print(f"🗑️ BOM file deleted: {self.bom_file}")
    
    def import_bom_from_csv(self):
        """Import BOM from KiCad CSV file"""
        from PyQt6.QtWidgets import QComboBox, QDialogButtonBox
        
        # First, show project selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Project for BOM Import")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel("Select a project to assign imported BOM parts:")
        layout.addWidget(info_label)
        
        # Project selection
        project_combo = QComboBox()
        project_combo.addItem("-- No Project --", None)
        
        # Add existing projects
        for project in self.projects_data:
            project_combo.addItem(project.get('name', 'Unknown'), project.get('name'))
        
        # Option to create new project
        project_combo.addItem("+ Create New Project +", "CREATE_NEW")
        
        layout.addWidget(project_combo)
        
        # New project name input (initially hidden)
        new_project_label = QLabel("New project name:")
        new_project_input = QLineEdit()
        new_project_label.setVisible(False)
        new_project_input.setVisible(False)
        layout.addWidget(new_project_label)
        layout.addWidget(new_project_input)
        
        # Show/hide new project input based on selection
        def on_combo_changed(index):
            is_new = project_combo.currentData() == "CREATE_NEW"
            new_project_label.setVisible(is_new)
            new_project_input.setVisible(is_new)
            if is_new:
                new_project_input.setFocus()
        
        project_combo.currentIndexChanged.connect(on_combo_changed)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Show dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get selected project
        selected_project = None
        if project_combo.currentData() == "CREATE_NEW":
            selected_project = new_project_input.text().strip()
            if not selected_project:
                QMessageBox.warning(self, "Error", "Please enter a project name!")
                return
            
            # Check if project already exists
            for project in self.projects_data:
                if project.get('name') == selected_project:
                    QMessageBox.warning(self, "Error", f"Project '{selected_project}' already exists!")
                    return
            
            # Create new project
            self.projects_data.append({
                'name': selected_project,
                'description': f"Project {selected_project}"
            })
            self.save_projects()
        elif project_combo.currentData() is not None:
            selected_project = project_combo.currentData()
        
        # Now select CSV file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select KiCad BOM CSV file",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            imported_count = 0
            skipped_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                
                for row in csv_reader:
                    # Skip rows marked as DNP or excluded from BOM
                    # Check both English and Czech column names
                    dnp = row.get('DNP', '').strip()
                    exclude_en = row.get('Exclude from BOM', '').strip()
                    exclude_cz = row.get('Vyloučit z BOM', '').strip()
                    
                    if dnp or exclude_en or exclude_cz:
                        skipped_count += 1
                        continue
                    
                    # Parse reference designators
                    references = [ref.strip() for ref in row.get('Reference', '').split(',')]
                    qty = row.get('Qty', '1')
                    value = row.get('Value', '')
                    footprint = row.get('Footprint', '')
                    datasheet = row.get('Datasheet', '')
                    
                    # Create parsed data structure
                    parsed_data = {
                        'PN': value,  # Use Value as Part Number
                        'VALUE': value,  # Store value separately
                        'QTY': qty,
                        'MPN': value,  # Also use as MPN
                        'FOOTPRINT': footprint,
                        'REFERENCES': ', '.join(references),
                    }
                    
                    # Add project assignment if selected
                    if selected_project:
                        parsed_data['PROJECTS'] = [selected_project]
                    
                    if datasheet and datasheet != '~':
                        parsed_data['URL'] = datasheet
                    
                    # Create scan data entry
                    scan_data = {
                        'raw': f"KiCad Import: {value}",
                        'parsed': parsed_data,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'history': []
                    }
                    
                    # Check if part already exists
                    existing_index = None
                    for idx, existing in enumerate(self.scanned_codes):
                        if existing['parsed'].get('PN') == value:
                            existing_index = idx
                            break
                    
                    if existing_index is not None:
                        # Update quantity if part exists
                        old_qty = int(self.scanned_codes[existing_index]['parsed'].get('QTY', '0'))
                        new_qty = old_qty + int(qty)
                        self.scanned_codes[existing_index]['parsed']['QTY'] = str(new_qty)
                        
                        # Add project to existing part if not already there
                        if selected_project:
                            if 'PROJECTS' not in self.scanned_codes[existing_index]['parsed']:
                                self.scanned_codes[existing_index]['parsed']['PROJECTS'] = []
                            if selected_project not in self.scanned_codes[existing_index]['parsed']['PROJECTS']:
                                self.scanned_codes[existing_index]['parsed']['PROJECTS'].append(selected_project)
                        
                        # Update table
                        self.bom_table.item(existing_index, 1).setText(str(new_qty))
                    else:
                        # Add new part
                        self.scanned_codes.append(scan_data)
                        
                        # Add to table
                        row = self.bom_table.rowCount()
                        self.bom_table.insertRow(row)
                        
                        # Create items
                        for col in range(self.bom_table.columnCount()):
                            item = QTableWidgetItem()
                            self.bom_table.setItem(row, col, item)
                        
                        # Get category for ID generation
                        part_number = parsed_data.get('PN', '')
                        value = parsed_data.get('VALUE', '')
                        category = get_part_category(part_number, value, self.tme_api) if part_number else "Unknown"
                        
                        # Generate category-based ID
                        part_id = generate_category_id(category, self.category_prefixes, self.category_counters)
                        
                        # Fill data
                        self.bom_table.item(row, 0).setText(part_id)  # Category-based ID
                        self.bom_table.item(row, 1).setText(parsed_data.get('QTY', ''))
                        self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
                        self.bom_table.item(row, 3).setText(parsed_data.get('VALUE', ''))
                        self.bom_table.item(row, 4).setText(shorten_footprint(parsed_data.get('FOOTPRINT', '')))
                        self.bom_table.item(row, 5).setText(parsed_data.get('MPN', ''))
                        self.bom_table.item(row, 6).setText(parsed_data.get('MFR', ''))
                        self.bom_table.item(row, 7).setText(parsed_data.get('LCSC', ''))
                        self.bom_table.item(row, 8).setText(parsed_data.get('FOOTPRINT', ''))
                        self.bom_table.item(row, 9).setText(parsed_data.get('LOCATION', ''))
                        projects = parsed_data.get('PROJECTS', [])
                        self.bom_table.item(row, 10).setText(', '.join(projects) if projects else '')
                        self.bom_table.item(row, 11).setText(parsed_data.get('PO', ''))
                        self.bom_table.item(row, 12).setText(scan_data['timestamp'].split()[1])  # Time only
                    
                    imported_count += 1
            
            # Save changes
            self.update_stats()
            self.save_bom()
            
            # Refresh projects table if project was assigned
            if selected_project:
                self.refresh_projects_table()
            
            # Show success message
            msg = f"Successfully imported {imported_count} parts from BOM."
            if skipped_count > 0:
                msg += f"\n{skipped_count} parts skipped (DNP or excluded)."
            if selected_project:
                msg += f"\n\nAll parts assigned to project: {selected_project}"
            
            QMessageBox.information(
                self,
                'Import Successful',
                msg
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                'Import Error',
                f'Failed to import BOM:\n{str(e)}'
            )
    
    def export_to_csv(self):
        """Export BOM to CSV file"""
        if not self.scanned_codes:
            QMessageBox.warning(
                self,
                'Empty Table',
                'No scanned parts available for export.'
            )
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BOM_{timestamp}.csv"
        
        try:
            import csv
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['#', 'QTY', 'Part Number', 'MPN', 'Manufacturer', 'PO', 'CoO', 'RoHS', 'Storage', 'URL', 'Time'])
                
                # Data
                for idx, scan_data in enumerate(self.scanned_codes, 1):
                    parsed = scan_data.get('parsed', {})
                    row = [
                        idx,
                        parsed.get('QTY', ''),
                        parsed.get('PN', ''),
                        parsed.get('MPN', ''),
                        parsed.get('MFR', ''),
                        parsed.get('PO', ''),
                        parsed.get('CoO', ''),
                        'Yes' if 'RoHS' in parsed else 'No',
                        parsed.get('LOCATION', ''),  # Storage location
                        parsed.get('URL', ''),
                        scan_data.get('timestamp', '')
                    ]
                    writer.writerow(row)
            
            QMessageBox.information(
                self,
                'Export Successful',
                f'BOM was exported to file:\n{filename}'
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                'Export Error',
                f'Failed to export data:\n{str(e)}'
            )
            
    def update_stats(self):
        """Update statistics (removed - stats label no longer exists)"""
        pass
        
    def export_to_json(self):
        """Export scanned codes to JSON file"""
        if not self.scanned_codes:
            QMessageBox.warning(
                self,
                'Empty List',
                'No scanned codes available for export.'
            )
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scanned_codes_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scanned_codes, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                'Export Successful',
                f'Scanned codes were exported to file:\n{filename}'
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                'Export Error',
                f'Failed to export data:\n{str(e)}'
            )
    
    def on_project_barcode_changed(self, text):
        """Handle barcode text change in project tab"""
        if text:
            self.project_auto_timer.start(1000)
    
    def auto_select_project_part(self):
        """Auto-select part after barcode scan"""
        raw_barcode = self.project_barcode_input.text().strip()
        
        if not raw_barcode:
            return
        
        parsed_data = parse_bom_barcode(raw_barcode)
        
        if not parsed_data:
            self.project_assign_status.setText("Cannot parse barcode!")
            return
        
        # Find part in BOM
        search_key = parsed_data.get('PN') or parsed_data.get('MPN')
        part_index = None
        
        for idx, scan_data in enumerate(self.scanned_codes):
            existing_parsed = scan_data.get('parsed', {})
            if existing_parsed.get('PN') == search_key or existing_parsed.get('MPN') == search_key:
                part_index = idx
                break
        
        if part_index is None:
            self.project_assign_status.setText(f"Part {search_key} not found in BOM!")
            return
        
        self.selected_project_part = part_index
        part_name = parsed_data.get('PN', 'Unknown')
        self.project_assign_status.setText(f"Part selected: {part_name} - Enter project name")
        self.project_name_input.setFocus()
    
    def assign_part_to_project(self):
        """Assign selected part to project"""
        if self.selected_project_part is None:
            QMessageBox.warning(self, "Error", "Please scan a part first!")
            return
        
        project_name = self.project_name_input.text().strip()
        
        if not project_name:
            QMessageBox.warning(self, "Error", "Please enter project name!")
            return
        
        # Get part data
        scan_data = self.scanned_codes[self.selected_project_part]
        parsed = scan_data.get('parsed', {})
        
        # Initialize PROJECTS list if not exists
        if 'PROJECTS' not in parsed:
            parsed['PROJECTS'] = []
        
        # Add project if not already in list
        if project_name not in parsed['PROJECTS']:
            parsed['PROJECTS'].append(project_name)
            
            # Save to file
            self.save_bom()
            
            part_name = parsed.get('PN', 'Unknown')
            self.project_assign_status.setText(f"SUCCESS! {part_name} assigned to {project_name}")
            
            print(f"Part {part_name} assigned to project: {project_name}")
            
            QMessageBox.information(
                self,
                "Success",
                f"Part {part_name} has been assigned to project '{project_name}'\n\nTotal projects: {len(parsed['PROJECTS'])}"
            )
        else:
            self.project_assign_status.setText(f"Part already in project {project_name}")
            QMessageBox.information(self, "Info", f"Part is already assigned to project '{project_name}'")
        
        # Clear inputs
        self.project_barcode_input.clear()
        self.project_name_input.clear()
        self.selected_project_part = None
        self.project_barcode_input.setFocus()
    
    def refresh_project_overview(self):
        """Refresh project overview display"""
        # Collect all projects and their parts
        projects_dict = {}
        
        for scan_data in self.scanned_codes:
            parsed = scan_data.get('parsed', {})
            part_name = parsed.get('PN', 'Unknown')
            qty = parsed.get('QTY', '0')
            location = parsed.get('LOCATION', 'Not assigned')
            projects = parsed.get('PROJECTS', [])
            
            for project in projects:
                if project not in projects_dict:
                    projects_dict[project] = []
                
                projects_dict[project].append({
                    'part': part_name,
                    'qty': qty,
                    'location': location
                })
        
        # Format output
        if not projects_dict:
            output = "No projects assigned yet.\n\nUse 'Assign to Project' tab to assign parts to projects."
        else:
            output = f"TOTAL PROJECTS: {len(projects_dict)}\n\n"
            output += "=" * 60 + "\n\n"
            
            for project_name, parts in sorted(projects_dict.items()):
                output += f"PROJECT: {project_name}\n"
                output += "-" * 60 + "\n"
                output += f"Parts count: {len(parts)}\n\n"
                
                for part_info in parts:
                    output += f"  • {part_info['part']}\n"
                    output += f"    Quantity: {part_info['qty']}\n"
                    output += f"    Location: {part_info['location']}\n\n"
                
                output += "\n"
        
        self.projects_overview_text.setPlainText(output)
    
    def refresh_storage_table(self):
        """Refresh storage locations table from storage_locations_data and BOM data"""
        self.storage_table.setRowCount(0)
        
        # Track if we added new locations
        added_new = False
        
        # Build locations_dict from saved storage locations
        locations_dict = {}
        for storage_loc in self.storage_locations_data:
            location_code = storage_loc.get('code', '')
            locations_dict[location_code] = {
                'parts': [],  # List of (part_number, qty) tuples
                'description': storage_loc.get('description', 'Empty location')
            }
        
        # Aggregate parts from BOM by storage location
        for row in range(self.bom_table.rowCount()):
            # Get storage location from column 8
            location_item = self.bom_table.item(row, 8)
            if not location_item:
                continue
            
            location = location_item.text().strip()
            if not location:
                continue
            
            # Get part number (column 2) and quantity (column 1)
            part_item = self.bom_table.item(row, 2)
            qty_item = self.bom_table.item(row, 1)
            
            if part_item:
                part_number = part_item.text()
                qty = qty_item.text() if qty_item else '0'
                
                if location not in locations_dict:
                    # Location exists in BOM but not in saved storage - add it
                    locations_dict[location] = {
                        'parts': [(part_number, qty)],
                        'description': f"Storage for {part_number}"
                    }
                    # Also add to storage_locations_data
                    self.storage_locations_data.append({
                        'code': location,
                        'description': f"Storage for {part_number}"
                    })
                    added_new = True
                else:
                    # Add part to existing location
                    locations_dict[location]['parts'].append((part_number, qty))
        
        # Save if we added new locations
        if added_new:
            self.save_storage_locations()
        
        # Populate table
        for location_code, info in sorted(locations_dict.items()):
            row = self.storage_table.rowCount()
            self.storage_table.insertRow(row)
            
            # Calculate total parts and quantity
            parts_list = info['parts']
            parts_count = len(parts_list)
            total_qty = sum(int(qty) if qty.isdigit() else 0 for _, qty in parts_list)
            
            # Display summary
            if parts_count == 0:
                part_summary = "Empty"
                qty_summary = "0"
            elif parts_count == 1:
                part_summary = parts_list[0][0]
                qty_summary = parts_list[0][1]
            else:
                part_summary = f"{parts_count} different parts"
                qty_summary = str(total_qty)
            
            self.storage_table.setItem(row, 0, QTableWidgetItem(location_code))
            self.storage_table.setItem(row, 1, QTableWidgetItem(part_summary))
            self.storage_table.setItem(row, 2, QTableWidgetItem(qty_summary))
            self.storage_table.setItem(row, 3, QTableWidgetItem(info['description']))
    
    def create_storage_location(self):
        """Create new storage location"""
        from PyQt6.QtWidgets import QInputDialog
        
        location_code, ok = QInputDialog.getText(
            self,
            "Create Storage Location",
            "Enter location code (e.g., A1, B23):"
        )
        
        if ok and location_code:
            location_code = location_code.strip().upper()
            
            # Check if already exists
            if any(loc['code'] == location_code for loc in self.storage_locations_data):
                QMessageBox.warning(self, "Error", f"Storage location {location_code} already exists!")
                return
            
            # Get description
            description, ok = QInputDialog.getText(
                self,
                "Storage Description",
                f"Enter description for {location_code}:"
            )
            
            if ok:
                # Add to storage_locations_data
                self.storage_locations_data.append({
                    'code': location_code,
                    'description': description.strip()
                })
                
                # Save to JSON
                self.save_storage_locations()
                
                # Refresh table
                self.refresh_storage_table()
                
                QMessageBox.information(self, "Success", f"Storage location {location_code} created!")
    
    def show_storage_details(self, row, column):
        """Show detailed view of all parts in selected storage location with editable description"""
        location_code = self.storage_table.item(row, 0).text()
        
        # Get current description from storage_locations_data
        current_description = ""
        for storage_loc in self.storage_locations_data:
            if storage_loc.get('code') == location_code:
                current_description = storage_loc.get('description', '')
                break
        
        # Find all parts in this storage location from BOM
        parts_in_storage = []
        total_qty = 0
        
        for row_idx in range(self.bom_table.rowCount()):
            location_item = self.bom_table.item(row_idx, 8)
            if location_item and location_item.text() == location_code:
                part_num = self.bom_table.item(row_idx, 2).text() if self.bom_table.item(row_idx, 2) else ''
                mpn = self.bom_table.item(row_idx, 3).text() if self.bom_table.item(row_idx, 3) else ''
                mfr = self.bom_table.item(row_idx, 4).text() if self.bom_table.item(row_idx, 4) else ''
                qty = self.bom_table.item(row_idx, 1).text() if self.bom_table.item(row_idx, 1) else '0'
                
                parts_in_storage.append({
                    'part': part_num,
                    'mpn': mpn,
                    'mfr': mfr,
                    'qty': qty
                })
                
                if qty.isdigit():
                    total_qty += int(qty)
        
        # Create details dialog
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle(f"Storage Location: {location_code}")
        details_dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(details_dialog)
        
        # Title
        title = QLabel(f"Storage Location: {location_code}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description section
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        
        description_input = QLineEdit()
        description_input.setText(current_description)
        description_input.setPlaceholderText("Enter storage location description...")
        desc_layout.addWidget(description_input)
        
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # Summary
        info = QLabel(f"Total: {len(parts_in_storage)} part(s), {total_qty} piece(s)")
        info_font = QFont()
        info_font.setBold(True)
        info.setFont(info_font)
        layout.addWidget(info)
        
        # Table with parts
        parts_table = QTableWidget()
        parts_table.setColumnCount(4)
        parts_table.setHorizontalHeaderLabels(['Part Number', 'MPN', 'Manufacturer', 'Quantity'])
        parts_table.setRowCount(len(parts_in_storage))
        
        for idx, part in enumerate(parts_in_storage):
            parts_table.setItem(idx, 0, QTableWidgetItem(part['part']))
            parts_table.setItem(idx, 1, QTableWidgetItem(part['mpn']))
            parts_table.setItem(idx, 2, QTableWidgetItem(part['mfr']))
            parts_table.setItem(idx, 3, QTableWidgetItem(part['qty']))
        
        # Table settings
        parts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        parts_table.setAlternatingRowColors(True)
        parts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = parts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(parts_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Close")
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Save function
        def save_description():
            new_description = description_input.text().strip()
            
            # Update in storage_locations_data
            for storage_loc in self.storage_locations_data:
                if storage_loc.get('code') == location_code:
                    storage_loc['description'] = new_description
                    break
            
            # Save to JSON file
            self.save_storage_locations()
            
            # Refresh storage table
            self.refresh_storage_table()
            
            QMessageBox.information(details_dialog, "Success", "Description updated!")
            details_dialog.accept()
        
        save_btn.clicked.connect(save_description)
        close_btn.clicked.connect(details_dialog.accept)
        
        details_dialog.exec()
    
    def delete_storage_location(self):
        """Delete selected storage location"""
        current_row = self.storage_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a storage location to delete!")
            return
        
        location_code = self.storage_table.item(current_row, 0).text()
        
        # Check if storage contains any parts
        has_parts = False
        for row in range(self.bom_table.rowCount()):
            storage_item = self.bom_table.item(row, 8)
            if storage_item and storage_item.text() == location_code:
                has_parts = True
                break
        
        if has_parts:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"Storage location '{location_code}' contains parts and cannot be deleted!\n\nPlease remove all parts from this location first."
            )
            return
        
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Delete storage location "{location_code}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from storage_locations_data
            self.storage_locations_data = [
                loc for loc in self.storage_locations_data 
                if loc.get('code') != location_code
            ]
            
            # Save to JSON file
            self.save_storage_locations()
            
            # Remove from all parts
            for scan_data in self.scanned_codes:
                parsed = scan_data.get('parsed', {})
                if parsed.get('LOCATION') == location_code:
                    parsed['LOCATION'] = ''
                    
                    # Update BOM table
                    for bom_row in range(self.bom_table.rowCount()):
                        if self.bom_table.item(bom_row, 2).text() == parsed.get('PN', ''):
                            self.bom_table.item(bom_row, 8).setText('')
                            break
            
            self.save_bom()
            
            # Refresh table
            self.refresh_storage_table()
            
            QMessageBox.information(self, "Success", f"Storage location '{location_code}' deleted!")
    
    def refresh_projects_table(self):
        """Refresh projects table from projects_data and BOM data"""
        self.projects_table.setRowCount(0)
        
        # Track if we added new projects
        added_new = False
        
        # Build projects_dict from saved projects
        projects_dict = {}
        for project in self.projects_data:
            project_name = project.get('name', '')
            projects_dict[project_name] = {
                'parts': [],
                'total_qty': 0,
                'description': project.get('description', f"Project {project_name}")
            }
        
        # Update with actual part assignments from BOM
        for scan_data in self.scanned_codes:
            parsed = scan_data.get('parsed', {})
            part_projects = parsed.get('PROJECTS', [])
            
            for project_name in part_projects:
                if project_name not in projects_dict:
                    # Project exists in BOM but not in saved projects - add it
                    projects_dict[project_name] = {
                        'parts': [],
                        'total_qty': 0,
                        'description': f"Project {project_name}"
                    }
                    # Also add to projects_data
                    self.projects_data.append({
                        'name': project_name,
                        'description': f"Project {project_name}"
                    })
                    added_new = True
                
                part_number = parsed.get('PN', 'Unknown')
                qty = int(parsed.get('QTY', '0'))
                
                projects_dict[project_name]['parts'].append(part_number)
                projects_dict[project_name]['total_qty'] += qty
        
        # Save if we added new projects
        if added_new:
            self.save_projects()
        
        # Populate table
        for project_name, info in sorted(projects_dict.items()):
            row = self.projects_table.rowCount()
            self.projects_table.insertRow(row)
            
            self.projects_table.setItem(row, 0, QTableWidgetItem(project_name))
            self.projects_table.setItem(row, 1, QTableWidgetItem(str(len(info['parts']))))
            self.projects_table.setItem(row, 2, QTableWidgetItem(str(info['total_qty'])))
            self.projects_table.setItem(row, 3, QTableWidgetItem(info['description']))
    
    def create_project(self):
        """Create new project"""
        from PyQt6.QtWidgets import QInputDialog
        
        project_name, ok = QInputDialog.getText(
            self,
            'Create Project',
            'Enter project name:'
        )
        
        if ok and project_name:
            project_name = project_name.strip()
            
            # Check if project already exists in saved data
            for project in self.projects_data:
                if project.get('name') == project_name:
                    QMessageBox.warning(self, "Error", f"Project '{project_name}' already exists!")
                    return
            
            # Add to projects_data
            self.projects_data.append({
                'name': project_name,
                'description': f"Project {project_name}"
            })
            
            # Save to JSON file
            self.save_projects()
            
            # Refresh table
            self.refresh_projects_table()
            
            QMessageBox.information(self, "Success", f"Project '{project_name}' created!")
    
    def delete_project(self):
        """Delete selected project"""
        current_row = self.projects_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a project to delete!")
            return
        
        project_name = self.projects_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self,
            'Confirmation',
            f'Delete project "{project_name}"?\n\nThis will remove the project from all parts.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from projects_data
            self.projects_data = [
                proj for proj in self.projects_data 
                if proj.get('name') != project_name
            ]
            
            # Save to JSON file
            self.save_projects()
            
            # Remove from all parts
            for scan_data in self.scanned_codes:
                parsed = scan_data.get('parsed', {})
                projects = parsed.get('PROJECTS', [])
                
                if project_name in projects:
                    projects.remove(project_name)
                    parsed['PROJECTS'] = projects
            
            self.save_bom()
            
            # Refresh table
            self.refresh_projects_table()
            
            QMessageBox.information(self, "Success", f"Project '{project_name}' deleted!")
    
    def show_project_details(self, row, column):
        """Show details of selected project with editable description"""
        project_name = self.projects_table.item(row, 0).text()
        
        # Get current description from projects_data
        current_description = ""
        for project in self.projects_data:
            if project.get('name') == project_name:
                current_description = project.get('description', '')
                break
        
        # Collect parts for this project
        parts_info = []
        
        for scan_data in self.scanned_codes:
            parsed = scan_data.get('parsed', {})
            projects = parsed.get('PROJECTS', [])
            
            if project_name in projects:
                parts_info.append({
                    'part': parsed.get('PN', 'Unknown'),
                    'qty': parsed.get('QTY', '0'),
                    'location': parsed.get('LOCATION', 'Not assigned')
                })
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Project Details: {project_name}")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel(f"Project: {project_name}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description section
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout()
        
        description_input = QLineEdit()
        description_input.setText(current_description)
        description_input.setPlaceholderText("Enter project description...")
        desc_layout.addWidget(description_input)
        
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        info = QLabel(f"Total parts: {len(parts_info)}")
        layout.addWidget(info)
        
        # Parts table
        parts_table = QTableWidget()
        parts_table.setColumnCount(3)
        parts_table.setHorizontalHeaderLabels(['Part Number', 'Quantity', 'Location'])
        parts_table.setRowCount(len(parts_info))
        
        for idx, part in enumerate(parts_info):
            parts_table.setItem(idx, 0, QTableWidgetItem(part['part']))
            parts_table.setItem(idx, 1, QTableWidgetItem(part['qty']))
            parts_table.setItem(idx, 2, QTableWidgetItem(part['location']))
        
        layout.addWidget(parts_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Close")
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Save function
        def save_description():
            new_description = description_input.text().strip()
            
            # Update in projects_data
            for project in self.projects_data:
                if project.get('name') == project_name:
                    project['description'] = new_description
                    break
            
            # Save to JSON file
            self.save_projects()
            
            # Refresh projects table
            self.refresh_projects_table()
            
            QMessageBox.information(dialog, "Success", "Description updated!")
            dialog.accept()
        
        save_btn.clicked.connect(save_description)
        close_btn.clicked.connect(dialog.accept)
        
        dialog.exec()
    
    def open_tme_search_dialog(self):
        """Open TME search dialog"""
        if not self.tme_api:
            QMessageBox.warning(self, "TME API Error", "TME API is not available!")
            return
        
        from PyQt6.QtWidgets import QLineEdit, QListWidget, QPushButton, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Search TME Products")
        dialog.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.tme_search_input = QLineEdit()
        self.tme_search_input.setPlaceholderText("Enter part number or description (e.g., 1N4007, resistor 100k)")
        search_btn = QPushButton("Search")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.tme_search_input)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        # Results list
        results_label = QLabel("Search Results:")
        layout.addWidget(results_label)
        
        self.tme_results_list = QListWidget()
        self.tme_results_list.setMinimumHeight(200)
        layout.addWidget(self.tme_results_list)
        
        # Product details
        details_label = QLabel("Product Details:")
        layout.addWidget(details_label)
        
        self.tme_product_details = QTextEdit()
        self.tme_product_details.setReadOnly(True)
        self.tme_product_details.setMinimumHeight(200)
        layout.addWidget(self.tme_product_details)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_to_bom_btn = QPushButton("Add to BOM")
        add_to_bom_btn.setEnabled(False)
        close_btn = QPushButton("Close")
        button_layout.addStretch()
        button_layout.addWidget(add_to_bom_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        # Store current search results
        self.current_tme_results = []
        
        def perform_search():
            search_text = self.tme_search_input.text().strip()
            if not search_text:
                QMessageBox.warning(dialog, "Input Error", "Please enter search text!")
                return
            
            # Show loading
            self.tme_results_list.clear()
            self.tme_results_list.addItem("Searching...")
            self.tme_product_details.clear()
            
            try:
                result = self.tme_api.search_products(search_text)
                
                if result.get('Status') == 'OK':
                    products = result.get('Data', {}).get('ProductList', [])
                    self.current_tme_results = products
                    
                    self.tme_results_list.clear()
                    if products:
                        for product in products:
                            symbol = product.get('Symbol', 'N/A')
                            desc = product.get('Description', 'N/A')[:60]
                            self.tme_results_list.addItem(f"{symbol} - {desc}")
                        results_label.setText(f"Search Results ({len(products)} found):")
                    else:
                        self.tme_results_list.addItem("No products found")
                        results_label.setText("Search Results (0 found):")
                else:
                    self.tme_results_list.clear()
                    self.tme_results_list.addItem(f"Error: {result.get('Error', 'Unknown error')}")
                    
            except Exception as e:
                self.tme_results_list.clear()
                self.tme_results_list.addItem(f"Error: {str(e)}")
        
        def show_product_details():
            selected_row = self.tme_results_list.currentRow()
            if selected_row < 0 or selected_row >= len(self.current_tme_results):
                return
            
            product = self.current_tme_results[selected_row]
            symbol = product.get('Symbol')
            
            # Get detailed info
            try:
                details_result = self.tme_api.get_products(symbol)
                params_result = self.tme_api.get_parameters(symbol)
                stock_result = self.tme_api.get_prices_and_stocks(symbol)
                
                details_text = "<h3>Product Information</h3>"
                
                if details_result.get('Status') == 'OK':
                    prod_list = details_result.get('Data', {}).get('ProductList', [])
                    if prod_list:
                        p = prod_list[0]
                        details_text += f"<b>Symbol:</b> {p.get('Symbol', 'N/A')}<br>"
                        details_text += f"<b>Producer:</b> {p.get('Producer', 'N/A')}<br>"
                        details_text += f"<b>Description:</b> {p.get('Description', 'N/A')}<br>"
                        details_text += f"<b>Category:</b> {p.get('CategoryName', 'N/A')}<br>"
                        details_text += f"<b>Original Symbol:</b> {p.get('OriginalSymbol', 'N/A')}<br>"
                        
                        # Photo
                        photo_url = p.get('Photo')
                        if photo_url:
                            details_text += f"<b>Photo:</b> <a href='{photo_url}'>{photo_url}</a><br>"
                
                # Stock and price
                if stock_result.get('Status') == 'OK':
                    stock_data = stock_result.get('Data', {})
                    prod_list = stock_data.get('ProductList', [])
                    if prod_list:
                        p = prod_list[0]
                        details_text += f"<br><h3>Availability</h3>"
                        details_text += f"<b>In Stock:</b> {p.get('Amount', 'N/A')} pcs<br>"
                        
                        price_list = p.get('PriceList', [])
                        if price_list:
                            details_text += f"<br><b>Prices ({stock_data.get('Currency', 'EUR')}):</b><br>"
                            for price in price_list[:5]:
                                details_text += f"  {price.get('Amount')}+ pcs: {price.get('PriceValue')}<br>"
                
                # Parameters
                if params_result.get('Status') == 'OK':
                    prod_list = params_result.get('Data', {}).get('ProductList', [])
                    if prod_list:
                        params = prod_list[0].get('ParameterList', [])
                        if params:
                            details_text += "<br><h3>Parameters</h3>"
                            for param in params:
                                name = param.get('ParameterName', 'N/A')
                                value = param.get('ParameterValue', 'N/A')
                                details_text += f"<b>{name}:</b> {value}<br>"
                
                self.tme_product_details.setHtml(details_text)
                add_to_bom_btn.setEnabled(True)
                
            except Exception as e:
                self.tme_product_details.setText(f"Error loading details: {str(e)}")
        
        def add_to_bom():
            selected_row = self.tme_results_list.currentRow()
            if selected_row < 0 or selected_row >= len(self.current_tme_results):
                return
            
            product = self.current_tme_results[selected_row]
            symbol = product.get('Symbol')
            
            try:
                # Get full product info
                details_result = self.tme_api.get_products(symbol)
                params_result = self.tme_api.get_parameters(symbol)
                stock_result = self.tme_api.get_prices_and_stocks(symbol)
                
                # Create parsed data
                parsed_data = {
                    'PN': symbol,
                    'MPN': '',
                    'MFR': '',
                    'QTY': '1',
                }
                
                if details_result.get('Status') == 'OK':
                    prod_list = details_result.get('Data', {}).get('ProductList', [])
                    if prod_list:
                        p = prod_list[0]
                        parsed_data['VALUE'] = p.get('OriginalSymbol', symbol)
                        parsed_data['MPN'] = p.get('OriginalSymbol', '')
                        parsed_data['MFR'] = p.get('Producer', '')
                        parsed_data['URL'] = f"https://www.tme.eu/cz/details/{symbol}/"
                
                # Extract parameters
                if params_result.get('Status') == 'OK':
                    prod_list = params_result.get('Data', {}).get('ProductList', [])
                    if prod_list:
                        params = prod_list[0].get('ParameterList', [])
                        for param in params:
                            param_name = param.get('ParameterName', '').lower()
                            param_value = param.get('ParameterValue', '')
                            
                            # Try to extract package/footprint info
                            if 'package' in param_name or 'case' in param_name or 'housing' in param_name:
                                if not parsed_data.get('FOOTPRINT'):
                                    parsed_data['FOOTPRINT'] = param_value
                
                # Add stock info
                if stock_result.get('Status') == 'OK':
                    stock_data = stock_result.get('Data', {})
                    prod_list = stock_data.get('ProductList', [])
                    if prod_list:
                        p = prod_list[0]
                        parsed_data['TME_STOCK'] = str(p.get('Amount', '0'))
                
                # Add to scanned codes
                scan_data = {
                    'raw': f"TME: {symbol}",
                    'parsed': parsed_data,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'history': []
                }
                
                self.scanned_codes.append(scan_data)
                
                # Add to table
                row = self.bom_table.rowCount()
                self.bom_table.insertRow(row)
                
                for col in range(self.bom_table.columnCount()):
                    item = QTableWidgetItem()
                    self.bom_table.setItem(row, col, item)
                
                # Fill data
                self.bom_table.item(row, 0).setText(str(row + 1))
                self.bom_table.item(row, 1).setText(parsed_data.get('QTY', '1'))
                self.bom_table.item(row, 2).setText(parsed_data.get('PN', ''))
                self.bom_table.item(row, 3).setText(parsed_data.get('VALUE', ''))
                self.bom_table.item(row, 4).setText(shorten_footprint(parsed_data.get('FOOTPRINT', '')))
                self.bom_table.item(row, 5).setText(parsed_data.get('MPN', ''))
                self.bom_table.item(row, 6).setText(parsed_data.get('MFR', ''))
                self.bom_table.item(row, 7).setText(symbol)  # LCSC column for TME symbol
                self.bom_table.item(row, 8).setText(parsed_data.get('FOOTPRINT', ''))
                self.bom_table.item(row, 9).setText(parsed_data.get('LOCATION', ''))
                self.bom_table.item(row, 10).setText('')  # Projects
                self.bom_table.item(row, 11).setText('')  # PO
                self.bom_table.item(row, 12).setText(scan_data['timestamp'].split()[1])
                
                # Save
                self.save_bom()
                
                QMessageBox.information(dialog, "Success", f"Added {symbol} to BOM!")
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to add product:\n{str(e)}")
        
        # Connect signals
        search_btn.clicked.connect(perform_search)
        self.tme_search_input.returnPressed.connect(perform_search)
        self.tme_results_list.currentRowChanged.connect(show_product_details)
        add_to_bom_btn.clicked.connect(add_to_bom)
        close_btn.clicked.connect(dialog.accept)
        
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    
    window = BOMScanner()
    window.showMaximized()  # Fullscreen/maximized window
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

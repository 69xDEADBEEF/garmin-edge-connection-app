#!/usr/bin/env python3
import sys
import os
import dbus
import time
import mount
import pyudev
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QMessageBox, QWidget, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class GarminDeviceManager:
    GARMIN_USB_VENDOR_ID = 0x091E  # Garmin's USB Vendor ID
    GARMIN_MOUNTPOINT = "/mnt/garmin"

    def __init__(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')

    def detect_usb_devices(self) -> List[Dict]:
        """Detect Garmin USB devices"""
        garmin_devices = []
        for device in self.context.list_devices(subsystem='block', DEVTYPE='partition'):
            if device.get('ID_VENDOR_ID', '') == hex(self.GARMIN_USB_VENDOR_ID)[2:]:
                garmin_devices.append({
                    'device_path': device.device_node,
                    'mount_path': self.GARMIN_MOUNTPOINT,
                    'label': device.get('ID_FS_LABEL', 'Garmin Device')
                })
        return garmin_devices

    def mount_device(self, device_path: str, mount_point: str) -> bool:
        """Mount Garmin USB device"""
        try:
            os.makedirs(mount_point, exist_ok=True)
            mount.mount(device_path, mount_point)
            return True
        except Exception as e:
            print(f"Mount error: {e}")
            return False

    def extract_fit_files(self, mount_point: str) -> List[str]:
        """Find and return FIT files from mounted device"""
        fit_files = []
        for root, _, files in os.walk(mount_point):
            fit_files.extend([
                os.path.join(root, f) 
                for f in files if f.lower().endswith('.fit')
            ])
        return fit_files

class BluetoothPairingManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.adapter_path = self._get_bluetooth_adapter()
        self.adapter = dbus.Interface(
            self.bus.get_object('org.bluez', self.adapter_path),
            'org.bluez.Adapter1'
        )

    def _get_bluetooth_adapter(self):
        """Find the default Bluetooth adapter path"""
        obj_manager = dbus.Interface(
            self.bus.get_object('org.bluez', '/'),
            'org.freedesktop.DBus.ObjectManager'
        )
        objects = obj_manager.GetManagedObjects()
        
        for path, interfaces in objects.items():
            if 'org.bluez.Adapter1' in interfaces:
                return path
        raise Exception("No Bluetooth adapter found")

    def discover_garmin_devices(self, duration: int = 10) -> List[Dict]:
        """Discover Garmin Bluetooth devices"""
        try:
            self.adapter.StartDiscovery()
            time.sleep(duration)
            self.adapter.StopDiscovery()

            obj_manager = dbus.Interface(
                self.bus.get_object('org.bluez', '/'),
                'org.freedesktop.DBus.ObjectManager'
            )
            objects = obj_manager.GetManagedObjects()

            garmin_devices = []
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    device = interfaces['org.bluez.Device1']
                    if 'Garmin' in device.get('Name', ''):
                        garmin_devices.append({
                            'address': device.get('Address', ''),
                            'name': device.get('Name', '')
                        })
            return garmin_devices
        except Exception as e:
            print(f"Bluetooth discovery error: {e}")
            return []

    def pair_device(self, device_address: str) -> bool:
        """Pair with a Garmin Bluetooth device"""
        try:
            device_path = f"/org/bluez/hci0/dev_{device_address.replace(':', '_')}"
            device = dbus.Interface(
                self.bus.get_object('org.bluez', device_path),
                'org.bluez.Device1'
            )
            device.Pair()
            return True
        except Exception as e:
            print(f"Pairing error: {e}")
            return False

class GarminConnectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Garmin Device Connection")
        self.setGeometry(100, 100, 800, 600)

        self.bluetooth_manager = BluetoothPairingManager()
        self.usb_device_manager = GarminDeviceManager()

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Tabs for different connection methods
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Bluetooth Tab
        bluetooth_tab = QWidget()
        bluetooth_layout = QVBoxLayout()
        bluetooth_tab.setLayout(bluetooth_layout)

        self.bluetooth_device_list = QListWidget()
        self.bluetooth_discover_btn = QPushButton("Discover Garmin Bluetooth Devices")
        self.bluetooth_discover_btn.clicked.connect(self.discover_bluetooth_devices)
        
        bluetooth_layout.addWidget(self.bluetooth_discover_btn)
        bluetooth_layout.addWidget(self.bluetooth_device_list)
        self.bluetooth_device_list.itemDoubleClicked.connect(self.pair_bluetooth_device)

        # USB Tab
        usb_tab = QWidget()
        usb_layout = QVBoxLayout()
        usb_tab.setLayout(usb_layout)

        self.usb_device_list = QListWidget()
        self.usb_discover_btn = QPushButton("Discover Garmin USB Devices")
        self.usb_discover_btn.clicked.connect(self.discover_usb_devices)
        
        usb_layout.addWidget(self.usb_discover_btn)
        usb_layout.addWidget(self.usb_device_list)
        self.usb_device_list.itemDoubleClicked.connect(self.mount_usb_device)

        self.tab_widget.addTab(bluetooth_tab, "Bluetooth")
        self.tab_widget.addTab(usb_tab, "USB")

    def discover_bluetooth_devices(self):
        """Discover Garmin Bluetooth devices"""
        self.bluetooth_device_list.clear()
        devices = self.bluetooth_manager.discover_garmin_devices()
        
        for device in devices:
            self.bluetooth_device_list.addItem(
                f"{device['address']} - {device['name']}"
            )

    def pair_bluetooth_device(self, item):
        """Pair with selected Bluetooth device"""
        device_info = item.text()
        device_address = device_info.split(" - ")[0]
        
        if self.bluetooth_manager.pair_device(device_address):
            QMessageBox.information(
                self, 
                "Pairing Successful", 
                f"Paired with {device_address}"
            )

    def discover_usb_devices(self):
        """Discover Garmin USB devices"""
        self.usb_device_list.clear()
        devices = self.usb_device_manager.detect_usb_devices()
        
        for device in devices:
            self.usb_device_list.addItem(
                f"{device['device_path']} - {device['label']}"
            )

    def mount_usb_device(self, item):
        """Mount selected USB device and extract FIT files"""
        device_info = item.text()
        device_path = device_info.split(" - ")[0]
        
        mount_point = f"{self.usb_device_manager.GARMIN_MOUNTPOINT}"
        
        if self.usb_device_manager.mount_device(device_path, mount_point):
            fit_files = self.usb_device_manager.extract_fit_files(mount_point)
            
            if fit_files:
                QMessageBox.information(
                    self, 
                    "USB Device Mounted", 
                    f"Found {len(fit_files)} FIT files"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "No FIT Files", 
                    "No FIT files found on device"
                )

def main():
    app = QApplication(sys.argv)
    connection_app = GarminConnectionApp()
    connection_app.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

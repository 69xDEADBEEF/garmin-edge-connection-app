#!/bin/bash


# Debian Package Build Script for Garmin Connection App

# Create package directory structure
mkdir -p garmin-connection-app/DEBIAN
mkdir -p garmin-connection-app/usr/local/bin
mkdir -p garmin-connection-app/usr/local/share/garmin-connection-app
mkdir -p garmin-connection-app/usr/share/applications
mkdir -p garmin-connection-app/usr/share/icons/hicolor/scalable/apps

# Copy main application script
cp garmin_connection_app.py garmin-connection-app/usr/local/share/garmin-connection-app/

# Create launcher script
cat > garmin-connection-app/usr/local/bin/garmin-connection-app << 'EOF'
#!/bin/bash
python3 /usr/local/share/garmin-connection-app/garmin_connection_app.py
EOF
chmod +x garmin-connection-app/usr/local/bin/garmin-connection-app

# Create desktop entry
cat > garmin-connection-app/usr/share/applications/garmin-connection-app.desktop << 'EOF'
[Desktop Entry]
Name=Garmin Connection App
Comment=Garmin Device Connection and FIT File Extractor
Exec=garmin-connection-app
Icon=garmin-connection-app
Terminal=false
Type=Application
Categories=Utility;Sports;
EOF

# Create application icon (simple SVG)
cat > garmin-connection-app/usr/share/icons/hicolor/scalable/apps/garmin-connection-app.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#1E90FF"/>
  <path d="M22,22 L42,22 L42,42 L22,42 Z" fill="white"/>
  <circle cx="32" cy="32" r="10" fill="#1E90FF"/>
</svg>
EOF

# Create Debian control file
cat > garmin-connection-app/DEBIAN/control << 'EOF'
Package: garmin-connection-app
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.7), 
         python3-pyqt5, 
         python3-dbus, 
         python3-pyudev, 
         bluez, 
         udisks2
Recommends: blueman
Maintainer: https://github.com/69xDEADBEEF
Description: Garmin Edge 1040 Connection and FIT File Extractor
 A tool to connect to Garmin Edge 1040 devices (and possibly others)  via Bluetooth or USB
 and extract ride data and FIT files.
EOF

# Create postinst script for additional setup
cat > garmin-connection-app/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

# Ensure user can access Bluetooth and USB devices
addgroup --system garmin-device-access 2>/dev/null || true
usermod -a -G bluetooth,dialout,garmin-device-access $SUDO_USER

# Update desktop database
update-desktop-database /usr/share/applications

# Update icon cache
gtk-update-icon-cache -f -t /usr/share/icons/hicolor

exit 0
EOF
chmod +x garmin-connection-app/DEBIAN/postinst

# Build the Debian package
dpkg-deb --build garmin-connection-app

# Optional: sign the package
# dpkg-sig -k YOUR_GPG_KEY garmin-connection-app.deb

# Clean up
rm -rf garmin-connection-app


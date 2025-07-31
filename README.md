# Galaksio 2 - Modern Galaxy Workflow Interface

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Galaxy 25.0](https://img.shields.io/badge/Galaxy-25.0-brightgreen.svg)](https://docs.galaxyproject.org/en/latest/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://hub.docker.com/)

> A modern, responsive web interface for running Galaxy workflows with enhanced user experience and accessibility.

## 🌟 What's New in Version 0.4.0

### 🎨 Modern Web Design
- **Fully Responsive Interface**: Works seamlessly on desktop, tablet, and mobile devices
- **Mobile-First Design**: Touch-friendly interface with bottom navigation for mobile users
- **Modern UI Components**: Card-based layouts, smooth animations, and intuitive navigation
- **Enhanced Accessibility**: Full keyboard navigation, screen reader support, and ARIA labels
- **Dark Mode Support**: Automatic dark mode based on system preferences
- **Progressive Web App**: PWA capabilities for offline functionality and app-like experience

### 🚀 Performance & Compatibility
- **Galaxy 25.0 Ready**: Full compatibility with the latest Galaxy Project version
- **Python 3.9+ Support**: Updated to use modern Python versions (dropped Python 3.8 support)
- **BioBlend 1.6.0 Integration**: Updated to latest BioBlend for enhanced API compatibility
- **Optimized Loading**: Fast loading times with lazy loading and optimized assets
- **Enhanced Security**: Modern security practices, CORS support, and secure session management

### 💡 User Experience Improvements
- **Interactive Dashboard**: Real-time statistics and system monitoring
- **Advanced Search & Filtering**: Powerful search capabilities with tag-based filtering
- **Toast Notifications**: Modern notification system instead of intrusive alerts
- **Loading States**: Beautiful loading indicators and empty states
- **Quick Actions**: Fast access to common workflow operations
- **Workflow Cards**: Visual workflow representation with metadata and statistics

### 🔧 Technical Enhancements
- **Enhanced Authentication**: Improved Galaxy API authentication with better error handling
- **Real-time Workflow Tracking**: Live workflow execution status with progress monitoring
- **Chunked File Uploads**: Support for large file uploads with progress tracking
- **Comprehensive Error Handling**: User-friendly error messages with actionable suggestions
- **Modern Security Headers**: CORS, CSP, and security headers for modern browsers
- **Background Cleanup**: Automatic cleanup of old workflows and uploads
- **Health Monitoring**: Built-in health checks and system monitoring

## 📸 Screenshots

### Desktop Interface
![Desktop Interface](https://raw.githubusercontent.com/cmehdi213/galaksio/master/docs/screenshots/desktop.png)
*Modern desktop interface with sidebar navigation and workflow cards*

### Mobile Interface
![Mobile Interface](https://raw.githubusercontent.com/cmehdi213/galaksio/master/docs/screenshots/mobile.png)
*Responsive mobile design with bottom navigation and touch-friendly controls*

### Installation Wizard
![Installation Wizard](https://raw.githubusercontent.com/cmehdi213/galaksio/master/docs/screenshots/wizard.png)
*Step-by-step installation wizard with progress indicators*

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.9 or later
- **Node.js**: 16+ (for development)
- **Docker**: 20+ (optional, for containerized deployment)
- **Modern Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Installation

#### Option 1: Standard Installation
1. **Install system dependencies**:
```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip git build-essential

# For CentOS/RHEL
sudo yum install -y python3 python3-pip git gcc

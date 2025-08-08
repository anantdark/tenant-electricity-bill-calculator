# ⚡ Tenant Electricity Bill Calculator

**A modern, comprehensive solution for managing multi-tenant electricity consumption and billing**

[![Docker Build](https://github.com/anantdark/tenant-electricity-bill-calculator/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/anantdark/tenant-electricity-bill-calculator/actions/workflows/docker-publish.yml)


[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/anantdark/tenant-electricity-bill-calculator)

> Transform your multi-tenant electricity management with automated calculations, beautiful reports, and intelligent analytics.

---

## 🚀 Features at a Glance

### 📊 **Smart Dashboard**
- **Real-time status ticker** showing current balances, readings, and suggestions
- **Interactive metrics** with monthly estimates and consumption analytics
- **Visual charts** for usage patterns and cost analysis
- **Next recharge suggestions** based on balance analysis

### 📝 **Dual Interface Options**
- **🌐 Modern Web Interface** - Intuitive, responsive design with dark theme
- **💻 Command-Line Interface** - Perfect for automation and quick operations

### 🧮 **Intelligent Calculations**
- **Proportional cost distribution** based on actual consumption ratios
- **Automatic deduction calculations** from tenant balances
- **Real-time consumption tracking** with historical baselines
- **Per-unit cost analysis** based on recent data

### 📈 **Advanced Analytics**
- **Monthly consumption estimates** based on last 3 months
- **Tenant-wise usage breakdown** with visual charts
- **Cost per unit calculations** with trend analysis
- **Interactive data visualization** with Chart.js

### 📄 **Professional Reports**
- **Styled PDF generation** with comprehensive transaction history
- **Customizable date ranges** for targeted reporting
- **Professional formatting** using ReportLab
- **Automatic report generation** after data entry

### 🔄 **Data Management**
- **Multiple CSV file support** with easy switching
- **Import/Export functionality** for data portability
- **Transaction history browser** with search and filtering
- **Revert functionality** to undo recent entries
- **Git sync integration** for automated backups

### 🌟 **Modern Features**
- **Responsive design** that works on all devices
- **File upload support** for CSV data import
- **Local/Cloud mode** toggle for different use cases
- **Health checks** and monitoring support
- **Security best practices** with non-root containers

---

## 🖼️ Screenshots

### Web Interface Dashboard
*Clean, modern interface with real-time status and metrics*

### Record Readings Interface  
*Streamlined data entry with validation and suggestions*

### Analytics & Charts
*Comprehensive usage analytics with interactive visualizations*

---

## 🏃‍♂️ Quick Start

### 🐳 Docker (Recommended)

**Production deployment:**
```bash
git clone https://github.com/anantdark/tenant-electricity-bill-calculator.git
cd tenant-electricity-bill-calculator
docker-compose up -d
```
→ Access at `http://localhost:5000`

**Development with live reload:**
```bash
docker-compose --profile dev up tenant-electricity-calculator-dev
```
→ Access at `http://localhost:5001`

### ☁️ Vercel (Serverless)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/anantdark/tenant-electricity-bill-calculator)

One-click deployment to Vercel's global CDN with automatic HTTPS.

### 💻 Local Development

```bash
git clone https://github.com/anantdark/tenant-electricity-bill-calculator.git
cd tenant-electricity-bill-calculator
pip install -r requirements.txt
python app.py  # Web interface at http://localhost:5000
python main.py # CLI interface
```

---

## 📘 Usage Guide

### 🌐 Web Interface

#### 1. **Dashboard Overview**
- View current tenant balances and meter readings
- See next suggested recharge based on balance analysis
- Monitor usage metrics and monthly estimates
- Access quick actions: Record, Browse, Sync, Settings

#### 2. **Recording New Data**
```
Navigation: Dashboard → Record
```
- Enter meter readings for all three tenants (Ground Floor, First Floor, Second Floor)
- Specify which tenant is making a recharge and the amount
- System automatically:
  - Calculates consumption since last readings
  - Distributes previous recharge costs proportionally
  - Updates all balances based on usage ratios
  - Generates PDF report (optional)

#### 3. **Browsing Transaction History**
```
Navigation: Dashboard → Browse
```
- Search transactions by type, tenant, date, or amount
- Filter by READING or RECHARGE types
- Sort by timestamp, tenant, or consumption
- Paginated results with configurable page sizes
- Export filtered data

#### 4. **Analytics & Reports**
- **Monthly Estimates**: Based on last 3 months consumption data
- **Per-unit Cost**: Calculated from recharge amounts and usage
- **Visual Charts**: Toggle between total usage and tenant-wise views
- **PDF Reports**: Generate comprehensive transaction reports

#### 5. **Data Synchronization**
```
Navigation: Dashboard → Sync
```
- Connect to Git repository for automated backups
- Push/pull data changes with commit messages
- Track remote repository status
- Configure Personal Access Tokens for HTTPS repos

#### 6. **Configuration**
```
Navigation: Dashboard → Settings
```
- Select default CSV file or upload new data
- Configure Git integration settings
- Manage application preferences
- Toggle local/cloud modes

### 💻 Command-Line Interface

#### 1. **Starting the CLI**
```bash
python main.py
```

#### 2. **Main Menu Options**
- **Option 1**: Record Readings and Recharge
- **Option 2**: Display Current State
- **Option 3**: View Transaction History  
- **Option 4**: Exit

#### 3. **Recording Data via CLI**
```
1. Enter meter readings for all tenants
2. Select tenant making the recharge
3. Enter recharge amount
4. System automatically calculates and updates balances
```

---

## 🔧 How It Works

### The Calculation Logic

The application uses a **proportional distribution system** based on actual consumption:

#### Example Scenario:
```
Initial State:
├── Ground Floor: 1000 units, Balance: Rs.0
├── First Floor: 2000 units, Balance: Rs.0  
└── Second Floor: 3000 units, Balance: Rs.0

First Floor recharges Rs.1200

Later readings:
├── Ground Floor: 1020 units (+20 units)
├── First Floor: 2030 units (+30 units)
└── Second Floor: 3050 units (+50 units)

When next recharge occurs:
├── Total consumption: 100 units
├── Ground Floor pays: 20% × Rs.1200 = Rs.240
├── First Floor pays: 30% × Rs.1200 = Rs.360
└── Second Floor pays: 50% × Rs.1200 = Rs.600
```

### Key Principles:
1. **Consumption-based billing**: Costs distributed by actual usage ratios
2. **Recharge timing**: Deductions occur when the next recharge is recorded
3. **Balance tracking**: Real-time balance updates for all tenants
4. **Historical accuracy**: Maintains complete transaction history

---

## 🛠️ Installation & Deployment

### Prerequisites
- **Python 3.11+** (for local development)
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (for version control and sync features)

### Deployment Options

#### 🐳 Docker Production
```bash
# Clone repository
git clone https://github.com/anantdark/tenant-electricity-bill-calculator.git
cd tenant-electricity-bill-calculator

# Start production stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop stack  
docker-compose down
```

#### 🔧 Docker Development
```bash
# Start development environment with live reload
docker-compose --profile dev up tenant-electricity-calculator-dev

# Access development server
open http://localhost:5001
```

#### ☁️ Vercel Serverless
1. Fork this repository
2. Connect to Vercel dashboard
3. Deploy with automatic builds on push
4. Configure environment variables if needed

#### 📦 GitHub Container Registry
```bash
# Use pre-built images
docker pull ghcr.io/anantdark/tenant-electricity-bill-calculator:main
docker run -p 5000:5000 ghcr.io/anantdark/tenant-electricity-bill-calculator:main
```

#### 🖥️ Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start web server
python app.py

# Or use CLI
python main.py
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` |
| `FLASK_DEBUG` | Enable debug mode | `0` |
| `DEPLOYED` | Cloud deployment flag | `false` |
| `VERCEL` | Vercel platform flag | Not set |

---

## 📁 Project Structure

```
tenant-electricity-bill-calculator/
├── 📱 Web Application
│   ├── app.py              # Flask web server
│   ├── templates/          # HTML templates
│   ├── static/             # CSS and assets
│   └── api/                # Vercel serverless functions
├── 💻 CLI Application  
│   └── main.py             # Command-line interface
├── 📊 Reports & Analytics
│   └── report.py           # PDF generation
├── 🐳 Docker Configuration
│   ├── Dockerfile          # Container definition
│   ├── docker-compose.yml  # Multi-service setup
│   └── DOCKER_README.md    # Docker documentation  
├── ☁️ Cloud Deployment
│   ├── vercel.json         # Vercel configuration
│   └── .github/workflows/  # CI/CD automation
├── 📄 Data Files
│   ├── transactions.csv    # Main data file
│   ├── uploads/           # Uploaded CSV files
│   └── outputs/           # Generated reports
└── 📚 Documentation
    └── README.md          # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
# Fork and clone the repo
git clone https://github.com/anantdark/tenant-electricity-bill-calculator.git
cd tenant-electricity-bill-calculator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies  
pip install -r requirements.txt

# Start development server
python app.py
```

### Reporting Issues
- Use the [GitHub Issues](https://github.com/anantdark/tenant-electricity-bill-calculator/issues) page
- Include screenshots for UI-related issues
- Provide steps to reproduce bugs
- Suggest enhancements with use cases

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **📚 Documentation**: Check the [Wiki](https://github.com/anantdark/tenant-electricity-bill-calculator/wiki)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/anantdark/tenant-electricity-bill-calculator/issues)  
- **💬 Discussions**: [GitHub Discussions](https://github.com/anantdark/tenant-electricity-bill-calculator/discussions)
- **📧 Contact**: Create an issue for direct support

---

## 🙏 Acknowledgments

- **Flask** - Web framework
- **ReportLab** - PDF generation  
- **Chart.js** - Interactive charts
- **Docker** - Containerization
- **Vercel** - Serverless deployment platform

---

<div align="center">

**⚡ Simplifying multi-tenant electricity management, one calculation at a time.**

[⭐ Star this repo](https://github.com/anantdark/tenant-electricity-bill-calculator) • [🐛 Report Bug](https://github.com/anantdark/tenant-electricity-bill-calculator/issues) • [✨ Request Feature](https://github.com/anantdark/tenant-electricity-bill-calculator/issues)

</div>
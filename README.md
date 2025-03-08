# ⚡ Tenant Electricity Bill Calculator ⚡

```ascii
 _______                       _      _______ _           _        _      
|__   __|                     | |    |  ____| |         | |      (_)     
   | | ___ _ __   __ _ _ __  | |_   | |__  | | ___  ___| |_ _ __ _  ___ 
   | |/ _ \ '_ \ / _` | '_ \ | __|  |  __| | |/ _ \/ __| __| '__| |/ __|
   | |  __/ | | | (_| | | | || |_   | |____| |  __/ (__| |_| |  | | (__ 
   |_|\___|_| |_|\__,_|_| |_| \__|  |______|_|\___|\___|\__|_|  |_|\___|
                                                                      
 ____  _ _ _    _____      _            _       _             
|  _ \(_) | |  / ____|    | |          | |     | |            
| |_) |_| | | | |     __ _| | ___ _   _| | __ _| |_ ___  _ __ 
|  _ <| | | | | |    / _` | |/ __| | | | |/ _` | __/ _ \| '__|
| |_) | | | | | |___| (_| | | (__| |_| | | (_| | || (_) | |   
|____/|_|_|_|  \_____\__,_|_|\___|\__,_|_|\__,_|\__\___/|_|   
```

A colorful, user-friendly command-line application to manage and calculate electricity bills for shared accommodations with multiple tenants.

## 🌟 Features

- 📊 Track electricity meter readings for multiple tenants
- 💰 Record electricity recharges and automatically distribute costs
- 📈 Calculate consumption based on meter readings
- 💸 Maintain balance sheets for each tenant
- 📝 Keep transaction history for all readings and recharges
- 📱 View tenant dashboard with current balances and recommendations
- 🗓️ Support for custom dates when recording readings or recharges

## 📋 Table of Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Examples](#-examples)
- [How It Works](#-how-it-works)
- [Data Storage](#-data-storage)
- [Tips](#-tips)
- [Contributing](#-contributing)
- [License](#-license)

## 🔌 Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Setup

1. Clone this repository or download the source code:

```bash
git clone https://github.com/yourusername/tenant-electricity-bill-calculator.git
cd tenant-electricity-bill-calculator
```

2. Install the required dependencies:

```bash
pip install colorama
```

## 🚀 Usage

Run the application by executing the main script:

```bash
python main.py
```

This will display the main menu with the following options:

```
============================================================
               ELECTRICITY BILLING SYSTEM
============================================================
Current time: 2023-07-15 14:30:45

1. Enter new meter readings
2. Record a recharge
3. View transaction history
4. View tenant dashboard
5. Exit

Enter your choice (1-5):
```

## 📝 Examples

### Initial Setup

When you run the application for the first time, you'll need to enter the initial meter readings for each tenant. These will serve as the baseline for future consumption calculations.

### Recording Meter Readings

```
============================================================
               ELECTRICITY METER READING INPUT
============================================================

Enter current meter readings:
Ground Floor current reading (previous: 1000.00): 1050.00
First Floor current reading (previous: 2000.00): 2080.00
Second Floor current reading (previous: 3000.00): 3070.00

Do you want to record a recharge with these readings? (y/n): y

Enter the recharge information:
Recharge amount (Rs.): 1000
Which tenant paid for the recharge (1-3)? 2
```

After entering the readings and recharge information, the application will display:

```
============================================================
               ELECTRICITY CONSUMPTION SUMMARY
============================================================
Tenant               Consumption (kWh)    Cost (Rs.)   
------------------------------------------------------------
Ground Floor         50.00 kWh           Rs.250.00
First Floor          80.00 kWh           Rs.400.00
Second Floor         70.00 kWh           Rs.350.00
TOTAL                200.00 kWh          Rs.1000.00

============================================================
                    CURRENT BALANCES
============================================================
Tenant               Balance (Rs.)    Status      
------------------------------------------------------------
Ground Floor         -Rs.250.00       
First Floor          +Rs.600.00       PAID
Second Floor         -Rs.350.00       

============================================================
RECOMMENDATION: Second Floor should pay the next recharge.
============================================================
```

### Recording a Recharge Only

You can also record a recharge without entering new meter readings:

```
============================================================
               ELECTRICITY RECHARGE INPUT
============================================================

Current balances:
1. Ground Floor: Balance = Rs.-250.00
2. First Floor: Balance = Rs.600.00
3. Second Floor: Balance = Rs.-350.00

Enter the recharge information:
Recharge amount (Rs.): 500
Which tenant paid for the recharge (1-3)? 3
```

### Viewing Transaction History

The application keeps a detailed history of all readings and recharges:

```
============================================================
                  TRANSACTION HISTORY
============================================================

Date: 2023-07-01 10:15:30
Type: READING
Tenant: Ground Floor
Reading: 1000.00
Consumption: 0.00 kWh

Date: 2023-07-01 10:15:30
Type: READING
Tenant: First Floor
Reading: 2000.00
Consumption: 0.00 kWh

...

Date: 2023-07-15 14:30:45
Type: RECHARGE
Tenant: First Floor
Amount: Rs.1000.00
Balances: Ground Floor: Rs.-250.00; First Floor: Rs.600.00; Second Floor: Rs.-350.00
```

### Tenant Dashboard

The dashboard provides a quick overview of the current status:

```
============================================================
                    TENANT DASHBOARD
============================================================

Current balances:
Ground Floor: -Rs.250.00
First Floor: +Rs.600.00
Second Floor: -Rs.350.00

Last recharge: Rs.1000.00 by First Floor on 2023-07-15 14:30:45
Last meter readings:
Ground Floor: 1050.00 on 2023-07-15 14:30:45
First Floor: 2080.00 on 2023-07-15 14:30:45
Second Floor: 3070.00 on 2023-07-15 14:30:45

Recommendation: Second Floor should pay the next recharge.
```

## 🔍 How It Works

The application works on a simple principle:

1. **Meter Readings**: Each tenant's electricity consumption is tracked through meter readings.

2. **Consumption Calculation**: The application calculates consumption by subtracting the previous reading from the current reading.

3. **Cost Distribution**: When a recharge is recorded, the cost is distributed proportionally based on each tenant's consumption.

4. **Balance Tracking**: The application maintains a balance for each tenant:
   - Negative balance means the tenant owes money
   - Positive balance means the tenant has credit

5. **Recommendations**: The system recommends which tenant should pay for the next recharge based on who has the most negative balance.

## 💾 Data Storage

All data is stored in CSV format in the `electricity_data` directory:

- `transactions.csv`: Contains all meter readings and recharges with timestamps

The application automatically creates this directory and file if they don't exist.

## 💡 Tips

- **Regular Readings**: For the most accurate cost distribution, enter meter readings regularly (e.g., monthly).
  
- **Recharge with Readings**: It's best to record a recharge at the same time as entering new meter readings.
  
- **Custom Dates**: If you forgot to enter readings on the actual date, you can use the custom date feature.
  
- **Backup Data**: Occasionally backup the `electricity_data` directory to prevent data loss.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPLv3) - a copyleft license that requires anyone who distributes your code or a derivative work to make the source available under the same terms.

Key points of GPLv3:
- You can use, modify, and distribute the software freely
- If you distribute modified versions, you must make your source modifications available
- Changes made must be tracked and dated
- The license prevents the software from being incorporated into proprietary programs

For more details, see the [GNU GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.en.html).

```ascii
 _____ _                 _          __             _   _      _             
|_   _| |__   __ _ _ __ | | _____  / _| ___  _ __ | | | |___ (_)_ __   __ _ 
  | | | '_ \ / _` | '_ \| |/ / __|| |_ / _ \| '__|| | | / __|| | '_ \ / _` |
  | | | | | | (_| | | | |   <\__ \|  _| (_) | |   | |_| \__ \| | | | | (_| |
  |_| |_| |_|\__,_|_| |_|_|\_\___/|_|  \___/|_|    \___/|___/|_|_| |_|\__, |
                                                                       |___/ 
```

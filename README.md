# Electricity Calculator for Tenant Recharges

This application calculates tenant recharge balances based on electricity meter readings. It tracks electricity consumption for three tenants (Ground Floor, First Floor, and Second Floor), calculates charges based on consumption ratios, and manages recharge balances.

## Features

- Track electricity meter readings for multiple tenants
- Record readings for all tenants at once
- Integrated recharge recording with readings
- Calculate consumption since last reading
- Accurately track consumption between recharges
- Distribute electricity costs based on consumption ratios
- Manage recharge balances for each tenant
- View complete transaction history
- Store all transactions in a CSV file for record keeping
- Import sample data to quickly get started

## How It Works

The application is based on the following principles:

1. Each tenant has a meter reading and a balance
2. When new readings are added for all tenants, consumption is calculated (difference from the previous reading)
3. After adding all readings, a recharge is recorded for one tenant and added to their balance
4. When calculating charges:
   - The application uses the readings from just before the last recharge as the baseline
   - It calculates consumption between those readings and the current readings
   - The total consumption for all tenants is calculated
   - Each tenant's share is determined based on their consumption ratio
   - The last recharge amount is deducted from all tenants' balances proportionally to their consumption

For example:
- Initial readings: Tenant A: 1000, Tenant B: 2000, Tenant C: 3000
- Tenant A recharges Rs.1200
- Later readings: Tenant A: 1020, Tenant B: 2030, Tenant C: 3050
- When the next recharge occurs:
  - The application calculates consumption since the readings before the last recharge:
    - Tenant A: 20 units, Tenant B: 30 units, Tenant C: 50 units (total 100 units)
  - Tenant A's balance will have Rs.240 deducted (20% of last recharge)
  - Tenant B's balance will have Rs.360 deducted (30% of last recharge)
  - Tenant C's balance will have Rs.600 deducted (50% of last recharge)

## Usage

### Running the Application

```bash
python main.py
```

When first starting the application with no existing data, you'll be prompted to import sample data from the provided `sample_transactions.csv` file. This will pre-fill the system with starting meter readings and a sample recharge.

### Main Menu Options

1. **Record Readings and Recharge**: Record meter readings for all tenants and then add a recharge
2. **Display Current State**: Show current balances, meter readings, and consumption
3. **View Transaction History**: Display a history of all readings and recharges
4. **Exit**: Quit the application

### Workflow Example

1. Initialize with starting meter readings for all tenants (or import sample data)
2. Use option 1 to record new readings for all tenants and add a recharge
3. The application will:
   - Record the new meter readings for all tenants
   - Calculate consumption since the readings before the last recharge
   - Deduct from each tenant's balance based on their consumption ratio of the previous recharge amount
   - Add the new recharge amount to the specified tenant's balance
   - Store the current readings as the new baseline for the next calculation

## Data Storage

The application stores all transactions in a CSV file named `transactions.csv` with the following columns:

- **Type**: READING or RECHARGE
- **Timestamp**: Date and time of the transaction
- **Tenant**: Name of the tenant
- **Reading/Amount**: Meter reading value or recharge amount
- **Consumption**: Calculated consumption (for readings only)
- **Balances**: Current balances for all tenants at the time of the transaction

## Sample Data

The application includes a `sample_transactions.csv` file with initial data to help you get started:
- Initial meter readings for all three tenants
- A sample recharge of Rs.1200 for the First Floor tenant

## Requirements

- Python 3.6 or higher
- Standard Python libraries (csv, os, datetime, decimal) 
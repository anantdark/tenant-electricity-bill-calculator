#!/usr/bin/env python3

import csv
import os
import datetime
import shutil
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Optional

# Constants
CSV_FILE = "transactions.csv"
SAMPLE_CSV_FILE = "sample_transactions.csv"
TENANTS = ["Ground Floor", "First Floor", "Second Floor"]


class Transaction:
    def __init__(self, trans_type: str, timestamp: str, tenant: str, value: float, 
                 consumption: Optional[float] = None, balances: Optional[str] = None):
        self.type = trans_type
        self.timestamp = timestamp
        self.tenant = tenant
        self.value = value
        self.consumption = consumption
        self.balances = balances
    
    @staticmethod
    def from_csv_row(row: List[str]) -> 'Transaction':
        """Create Transaction object from CSV row"""
        consumption = float(row[4]) if row[4] and row[4].strip() else None
        return Transaction(
            row[0], row[1], row[2], float(row[3]), consumption, row[5]
        )
    
    def to_csv_row(self) -> List[str]:
        """Convert Transaction to CSV row format"""
        consumption_str = f"{self.consumption}" if self.consumption is not None else ""
        return [
            self.type,
            self.timestamp,
            self.tenant,
            f"{self.value}",
            consumption_str,
            self.balances or ""
        ]


class ElectricityCalculator:
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.balances: Dict[str, Decimal] = {tenant: Decimal('0.00') for tenant in TENANTS}
        self.last_readings: Dict[str, float] = {tenant: 0.0 for tenant in TENANTS}
        self.last_consumption: Dict[str, float] = {tenant: 0.0 for tenant in TENANTS}
        self.last_recharge_amount: float = 0.0
        self.last_recharge_tenant: str = ""
        self.last_readings_before_recharge: Dict[str, float] = {tenant: 0.0 for tenant in TENANTS}
        
        # Load existing transactions if file exists
        self.load_transactions()
    
    def load_transactions(self) -> None:
        """Load transactions from CSV file if it exists"""
        if not os.path.exists(CSV_FILE):
            # Create the file with headers if it doesn't exist
            with open(CSV_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Timestamp", "Tenant", "Reading/Amount", "Consumption", "Balances"])
            return
        
        with open(CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)
            
            # First pass: load all transactions
            for row in rows:
                if len(row) >= 6:
                    transaction = Transaction.from_csv_row(row)
                    self.transactions.append(transaction)
                    
                    # Update balances from the last transaction
                    if transaction.balances:
                        self.update_balances_from_string(transaction.balances)
            
            # Find the latest recharge transaction
            latest_recharge = None
            for transaction in reversed(self.transactions):
                if transaction.type == "RECHARGE":
                    latest_recharge = transaction
                    self.last_recharge_amount = transaction.value
                    self.last_recharge_tenant = transaction.tenant
                    break
            
            # Find the readings just before the latest recharge 
            if latest_recharge:
                recharge_index = self.transactions.index(latest_recharge)
                readings_before_recharge = {}
                
                # Find the last reading for each tenant before this recharge
                for i in range(recharge_index - 1, -1, -1):
                    transaction = self.transactions[i]
                    if transaction.type == "READING" and transaction.tenant not in readings_before_recharge:
                        readings_before_recharge[transaction.tenant] = transaction.value
                        
                # Store these readings
                for tenant in TENANTS:
                    if tenant in readings_before_recharge:
                        self.last_readings_before_recharge[tenant] = readings_before_recharge[tenant]
            
            # Update last readings with the most recent values for each tenant
            for tenant in TENANTS:
                for transaction in reversed(self.transactions):
                    if transaction.type == "READING" and transaction.tenant == tenant:
                        self.last_readings[tenant] = transaction.value
                        break
    
    def update_balances_from_string(self, balance_string: str) -> None:
        """Parse and update balances from string format"""
        balance_parts = balance_string.split('; ')
        for part in balance_parts:
            tenant, amount_str = part.split(': Rs.')
            self.balances[tenant] = Decimal(amount_str)
    
    def format_balances_string(self) -> str:
        """Format balances as string for CSV"""
        return "; ".join([f"{tenant}: Rs.{self.balances[tenant]:.2f}" for tenant in TENANTS])
    
    def add_readings_and_recharge(self) -> None:
        """Add meter readings for all tenants and record a recharge"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\nEnter meter readings for all tenants:")
        
        # First record readings for all tenants
        for tenant in TENANTS:
            while True:
                try:
                    reading = float(input(f"Enter reading for {tenant}: "))
                    
                    # Calculate consumption (difference from last reading)
                    consumption = reading - self.last_readings[tenant]
                    if consumption < 0:
                        print(f"Error: New reading ({reading}) cannot be less than previous reading ({self.last_readings[tenant]})")
                        continue
                    
                    # Update last reading
                    self.last_readings[tenant] = reading
                    
                    # Create transaction
                    transaction = Transaction(
                        "READING", 
                        timestamp, 
                        tenant, 
                        reading, 
                        consumption, 
                        self.format_balances_string()
                    )
                    
                    # Add to transactions list
                    self.transactions.append(transaction)
                    
                    # Save to CSV
                    self.save_transaction(transaction)
                    
                    print(f"Added reading of {reading} for {tenant}. Consumption since last reading: {consumption}")
                    break
                except ValueError:
                    print("Please enter a valid number")
        
        print("\nAll readings have been recorded successfully.")
        
        # Then record a recharge
        print("\nNow enter recharge details:")
        tenant = select_tenant()
        if tenant:
            try:
                amount = float(input(f"Enter recharge amount for {tenant}: "))
                
                # Calculate consumption since the last recharge using the last readings before recharge
                if any(self.last_readings_before_recharge.values()):
                    self.calculate_consumption_since_last_recharge()
                
                # Then add the new recharge to the tenant's balance
                self.balances[tenant] += Decimal(str(amount))
                
                # Update last recharge information
                self.last_recharge_amount = amount
                self.last_recharge_tenant = tenant
                
                # Save current readings as the last readings before recharge
                for t in TENANTS:
                    self.last_readings_before_recharge[t] = self.last_readings[t]
                
                # Create transaction
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                transaction = Transaction(
                    "RECHARGE", 
                    timestamp, 
                    tenant, 
                    amount, 
                    None, 
                    self.format_balances_string()
                )
                
                # Add to transactions list
                self.transactions.append(transaction)
                
                # Save to CSV
                self.save_transaction(transaction)
                
                print(f"Added recharge of Rs.{amount} for {tenant}")
                print(f"Updated balances: {self.format_balances_string()}")
            except ValueError as e:
                print(f"Error: {e}")
    
    def calculate_consumption_since_last_recharge(self) -> None:
        """Calculate consumption since last recharge and deduct from balances"""
        # Calculate consumption since last recharge for each tenant
        consumption_since_recharge = {}
        for tenant in TENANTS:
            consumption = self.last_readings[tenant] - self.last_readings_before_recharge[tenant]
            consumption_since_recharge[tenant] = max(0, consumption)  # Ensure no negative consumption
        
        total_consumption = sum(consumption_since_recharge.values())
        
        if total_consumption <= 0:
            print("No consumption recorded since last recharge. Nothing to deduct.")
            return
        
        print("\nCalculating consumption ratios and deducting from balances:")
        print(f"Last recharge amount: Rs.{self.last_recharge_amount}")
        print(f"Total consumption since last recharge: {total_consumption} units")
        
        # Calculate consumption ratio for each tenant
        for tenant in TENANTS:
            consumption = consumption_since_recharge[tenant]
            ratio = consumption / total_consumption if total_consumption > 0 else 0
            
            print(f"  {tenant}: {consumption} units, ratio {ratio:.4f}")
            
            if self.last_recharge_amount > 0:
                # Calculate the amount to deduct based on ratio
                deduction = Decimal(str(self.last_recharge_amount)) * Decimal(str(ratio))
                
                # Round to 2 decimal places
                deduction = deduction.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Deduct from each tenant's balance based on their consumption ratio
                self.balances[tenant] -= deduction
                print(f"  Deducted Rs.{deduction} from {tenant}'s balance")
    
    def save_transaction(self, transaction: Transaction) -> None:
        """Save a transaction to the CSV file"""
        file_exists = os.path.exists(CSV_FILE)
        
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(["Type", "Timestamp", "Tenant", "Reading/Amount", "Consumption", "Balances"])
            
            writer.writerow(transaction.to_csv_row())
    
    def display_current_state(self) -> None:
        """Display current balances and readings"""
        print("\nCurrent State:")
        print("==============")
        print("Balances:")
        for tenant in TENANTS:
            print(f"  {tenant}: Rs.{self.balances[tenant]:.2f}")
        
        print("\nLast Meter Readings:")
        for tenant in TENANTS:
            print(f"  {tenant}: {self.last_readings[tenant]}")
        
        print("\nLast Readings Before Previous Recharge:")
        for tenant in TENANTS:
            print(f"  {tenant}: {self.last_readings_before_recharge[tenant]}")
        
        print(f"\nLast Recharge: Rs.{self.last_recharge_amount} by {self.last_recharge_tenant or 'N/A'}")
    
    def display_transaction_history(self) -> None:
        """Display history of transactions"""
        if not self.transactions:
            print("\nNo transactions found.")
            return
        
        print("\nTransaction History:")
        print("===================")
        
        for i, transaction in enumerate(self.transactions, 1):
            print(f"\n{i}. Type: {transaction.type}")
            print(f"   Timestamp: {transaction.timestamp}")
            print(f"   Tenant: {transaction.tenant}")
            
            if transaction.type == "READING":
                print(f"   Reading: {transaction.value}")
                print(f"   Consumption: {transaction.consumption}")
            else:  # RECHARGE
                print(f"   Recharge Amount: Rs.{transaction.value}")
            
            print(f"   Balances: {transaction.balances}")


def main_menu():
    calculator = ElectricityCalculator()
    
    # Check if transactions file exists and is empty (only header)
    file_exists = os.path.exists(CSV_FILE)
    file_empty = False
    if file_exists:
        with open(CSV_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            # Check if file only has header row
            try:
                header = next(reader)
                file_empty = next(reader, None) is None
            except StopIteration:
                file_empty = True
    
    # If file doesn't exist or is empty, offer to import sample data
    if not file_exists or file_empty:
        if os.path.exists(SAMPLE_CSV_FILE):
            print("\nNo transaction data found. Would you like to import sample data?")
            choice = input("Enter y/n: ").lower().strip()
            if choice == 'y':
                try:
                    shutil.copy(SAMPLE_CSV_FILE, CSV_FILE)
                    print("Sample data imported successfully!")
                    # Reload data
                    calculator = ElectricityCalculator()
                except Exception as e:
                    print(f"Error importing sample data: {e}")
    
    while True:
        print("\n=========================================")
        print("Electricity Calculator - Tenant Recharges")
        print("=========================================")
        print("1. Record Readings and Recharge")
        print("2. Display Current State")
        print("3. View Transaction History")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            calculator.add_readings_and_recharge()
        
        elif choice == '2':
            calculator.display_current_state()
        
        elif choice == '3':
            calculator.display_transaction_history()
        
        elif choice == '4':
            print("Exiting program. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")


def select_tenant() -> Optional[str]:
    """Prompt user to select a tenant"""
    print("\nSelect tenant:")
    for i, tenant in enumerate(TENANTS, 1):
        print(f"{i}. {tenant}")
    
    try:
        choice = int(input("\nEnter tenant number (1-3): "))
        if 1 <= choice <= len(TENANTS):
            return TENANTS[choice - 1]
        else:
            print("Invalid choice.")
            return None
    except ValueError:
        print("Please enter a number.")
        return None


if __name__ == "__main__":
    main_menu()

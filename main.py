import csv
import os
from datetime import datetime

def update_balances(last_recharge, recharge_tenant, tenant_readings, tenant_balances, tenant_names=None, update_balance=False):
    """
    Update tenant balances based on electricity consumption and recharge amount.
    
    Parameters:
    - last_recharge: Amount of the last electricity recharge (0 if no recharge)
    - recharge_tenant: Index of the tenant who paid for the recharge (1-based, None if no recharge)
    - tenant_readings: List of current meter readings for each tenant
    - tenant_balances: List of current balances for each tenant
    - tenant_names: Optional list of tenant names/descriptions
    - update_balance: Whether to update balances or just calculate consumption
    
    Returns:
    - Updated tenant balances
    - Consumption values
    """
    # Validate inputs
    if recharge_tenant is not None:
        if recharge_tenant < 1 or recharge_tenant > len(tenant_readings):
            raise ValueError(f"Invalid recharge tenant index: {recharge_tenant}. Must be between 1 and {len(tenant_readings)}")
    
    if len(tenant_readings) != len(tenant_balances):
        raise ValueError("Number of tenant readings must match number of tenant balances")
    
    # Use default tenant names if not provided
    if tenant_names is None:
        tenant_names = [f"Tenant {i+1}" for i in range(len(tenant_readings))]
    elif len(tenant_names) != len(tenant_readings):
        raise ValueError("Number of tenant names must match number of tenant readings")
    
    # Get previous readings from transaction history
    previous_readings = get_previous_readings(tenant_names)
    
    # Calculate consumption for each tenant
    consumptions = []
    for i, curr in enumerate(tenant_readings):
        prev = previous_readings[i]
        if curr < prev:
            raise ValueError(f"Current reading ({curr}) cannot be less than previous reading ({prev})")
        consumptions.append(curr - prev)
    
    # Calculate total consumption
    total_consumption = sum(consumptions)
    
    # Calculate shares and update balances
    shares = [0] * len(consumptions)
    costs = [0] * len(consumptions)
    
    # If there's consumption, calculate each tenant's share
    if total_consumption > 0:
        # Calculate each tenant's share of the total consumption cost
        for i, consumption in enumerate(consumptions):
            # Each tenant's share is proportional to their consumption
            shares[i] = consumption / total_consumption
            costs[i] = last_recharge * shares[i] if last_recharge > 0 else 0
    
    # If there's a recharge and we should update balances
    if update_balance and last_recharge > 0 and recharge_tenant is not None:
        # The tenant who paid the recharge gets their balance increased
        tenant_balances[recharge_tenant - 1] += last_recharge
        
        # If there's consumption, distribute the cost
        if total_consumption > 0:
            # Deduct each tenant's share from their balance
            for i in range(len(tenant_balances)):
                # Cost is proportional to consumption
                tenant_balances[i] -= costs[i]
    
    # Display results in a nicely formatted table
    try:
        from colorama import Fore, Style, init
        init()  # Initialize colorama
        has_colors = True
    except ImportError:
        has_colors = False
        print("For colored output, install colorama: pip install colorama")
    
    # Display consumption table
    print("\n" + "="*60)
    print(" "*15 + "ELECTRICITY CONSUMPTION SUMMARY")
    print("="*60)
    
    # Header
    print(f"{'Tenant':<20} {'Consumption (kWh)':<20} {'Cost (Rs.)':<15}")
    print("-"*60)
    
    # Data rows
    for i, (name, consumption, cost) in enumerate(zip(tenant_names, consumptions, costs)):
        if has_colors:
            name_color = Fore.CYAN
            text_color = Fore.WHITE
            if recharge_tenant is not None and i == (recharge_tenant - 1):
                text_color = Fore.GREEN
            print(f"{name_color}{name:<20}{Style.RESET_ALL} {text_color}{consumption:.2f} kWh{' '*11} Rs.{cost:.2f}{Style.RESET_ALL}")
        else:
            print(f"{name:<20} {consumption:.2f} kWh{' '*11} Rs.{cost:.2f}")
    
    # Total row
    if has_colors:
        print(f"{Fore.YELLOW}{'TOTAL':<20}{Style.RESET_ALL} {Fore.YELLOW}{total_consumption:.2f} kWh{' '*11} Rs.{last_recharge:.2f}{Style.RESET_ALL}")
    else:
        print(f"{'TOTAL':<20} {total_consumption:.2f} kWh{' '*11} Rs.{last_recharge:.2f}")
    
    # Display balances table
    print("\n" + "="*60)
    print(" "*20 + "CURRENT BALANCES")
    print("="*60)
    
    # Header
    print(f"{'Tenant':<20} {'Balance (Rs.)':<15} {'Status':<15}")
    print("-"*60)
    
    # Data rows
    for i, (name, balance) in enumerate(zip(tenant_names, tenant_balances)):
        status = "PAID" if recharge_tenant is not None and i == (recharge_tenant - 1) else ""
        if has_colors:
            name_color = Fore.CYAN
            balance_color = Fore.GREEN if balance >= 0 else Fore.RED
            status_color = Fore.GREEN if status else ""
            balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
            print(f"{name_color}{name:<20}{Style.RESET_ALL} {balance_color}{balance_sign}Rs.{balance:.2f}{Style.RESET_ALL}{' '*5}{status_color}{status}{Style.RESET_ALL}")
        else:
            balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
            print(f"{name:<20} {balance_sign}Rs.{balance:.2f}{' '*5}{status}")
    
    # Determine who will pay next (the one with the most negative balance)
    most_negative_index = tenant_balances.index(min(tenant_balances))
    
    print("\n" + "="*60)
    if has_colors:
        print(f"{Fore.YELLOW}RECOMMENDATION: {tenant_names[most_negative_index]} should pay the next recharge.{Style.RESET_ALL}")
    else:
        print(f"RECOMMENDATION: {tenant_names[most_negative_index]} should pay the next recharge.")
    print("="*60 + "\n")
    
    return tenant_balances, consumptions


def get_previous_readings(tenant_names):
    """Get the most recent meter readings for each tenant from the transactions file"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    # Default to zero if no previous readings
    previous_readings = [0] * len(tenant_names)
    
    if not os.path.exists(transactions_file):
        return previous_readings
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows to find the latest reading for each tenant
            rows = list(reader)
            
            if not rows:
                return previous_readings
            
            # Find the latest reading for each tenant
            for i, name in enumerate(tenant_names):
                # Look for the latest reading entry for this tenant
                for row in reversed(rows):
                    if len(row) >= 5 and row[0] == "READING" and row[2] == name:
                        try:
                            previous_readings[i] = float(row[3])
                            break
                        except (ValueError, IndexError):
                            # If there's an error parsing, continue with the next row
                            continue
    except Exception as e:
        print(f"Warning: Could not read previous readings: {e}")
    
    return previous_readings


def save_transaction(transaction_type, timestamp, tenant_name=None, reading=None, recharge_amount=None, tenant_balances=None, tenant_names=None, consumption=None):
    """
    Save a transaction to the transactions CSV file
    
    Parameters:
    - transaction_type: "READING" or "RECHARGE"
    - timestamp: Timestamp of the transaction
    - tenant_name: Name of the tenant (for readings or who paid the recharge)
    - reading: Meter reading value (for readings)
    - recharge_amount: Amount of the recharge (for recharges)
    - tenant_balances: Current balances for all tenants (for both types)
    - tenant_names: Names of all tenants (for both types)
    - consumption: Consumption since last reading (for readings)
    """
    # Create data directory if it doesn't exist
    data_dir = "electricity_data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Format timestamp
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare the transactions file
    transactions_file = os.path.join(data_dir, "transactions.csv")
    file_exists = os.path.exists(transactions_file)
    
    with open(transactions_file, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(["Type", "Timestamp", "Tenant", "Reading/Amount", "Consumption", "Balances"])
        
        # Write the transaction
        if transaction_type == "READING":
            # Format balances as a string if provided
            balances_str = ""
            if tenant_balances and tenant_names:
                balances_str = "; ".join([f"{name}: Rs.{balance:.2f}" for name, balance in zip(tenant_names, tenant_balances)])
            
            writer.writerow([
                "READING",
                timestamp_str,
                tenant_name,
                reading,
                consumption if consumption is not None else "",
                balances_str
            ])
        elif transaction_type == "RECHARGE":
            # Format balances as a string if provided
            balances_str = ""
            if tenant_balances and tenant_names:
                balances_str = "; ".join([f"{name}: Rs.{balance:.2f}" for name, balance in zip(tenant_names, tenant_balances)])
            
            writer.writerow([
                "RECHARGE",
                timestamp_str,
                tenant_name,
                recharge_amount,
                "",  # No consumption for recharges
                balances_str
            ])


def load_from_csv():
    """
    Load the current state from transactions CSV
    
    Returns:
    - tenant_names: List of tenant names
    - tenant_balances: List of current balances
    - last_updated: Timestamp of when the data was last updated
    """
    data_dir = "electricity_data"
    transactions_file = os.path.join(data_dir, "transactions.csv")
    
    # Default values
    tenant_names = ["Ground Floor", "First Floor", "Second Floor"]
    tenant_balances = [0, 0, 0]
    last_updated = "No previous data"
    
    if not os.path.exists(transactions_file):
        return tenant_names, tenant_balances, last_updated
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows to find the latest transaction
            rows = list(reader)
            
            if not rows:
                return tenant_names, tenant_balances, last_updated
            
            # Get the last transaction timestamp
            last_updated = rows[-1][1] if len(rows[-1]) > 1 else "Unknown"
            
            # Find the latest balances
            for row in reversed(rows):
                if len(row) >= 6 and row[5]:  # Check if balances column has data
                    try:
                        # Parse the balances string
                        balances_str = row[5]
                        balance_entries = balances_str.split("; ")
                        
                        # Extract tenant names and balances
                        extracted_names = []
                        extracted_balances = []
                        
                        for entry in balance_entries:
                            if ": Rs." in entry:
                                name, balance_part = entry.split(": Rs.")
                                extracted_names.append(name)
                                extracted_balances.append(float(balance_part))
                        
                        if extracted_names and extracted_balances:
                            tenant_names = extracted_names
                            tenant_balances = extracted_balances
                            break
                    except Exception:
                        # If there's an error parsing, continue with the next row
                        continue
    except Exception as e:
        print(f"Warning: Could not load state from transactions file: {e}")
    
    return tenant_names, tenant_balances, last_updated


def get_user_input(tenant_names, tenant_balances, last_updated):
    """
    Get user input for meter readings and recharge information
    
    Parameters:
    - tenant_names: List of tenant names
    - tenant_balances: List of current balances
    - last_updated: Timestamp of when the data was last updated
    
    Returns:
    - tenant_readings: List of current meter readings
    - last_recharge: Amount of the recharge (0 if no recharge)
    - recharge_tenant: Index of the tenant who paid for the recharge (None if no recharge)
    - custom_date: Custom date if provided by user, otherwise None
    """
    print("\n" + "="*60)
    print(" "*15 + "ELECTRICITY METER READING INPUT")
    print("="*60)
    
    # Display last updated timestamp
    print(f"\nLast updated: {last_updated}")
    
    # Display current balances
    print("\nCurrent balances:")
    for i, (name, balance) in enumerate(zip(tenant_names, tenant_balances)):
        print(f"{i+1}. {name}: Balance = Rs.{balance:.2f}")
    
    # Get previous readings for reference
    previous_readings = get_previous_readings(tenant_names)
    print("\nPrevious meter readings:")
    for i, (name, prev) in enumerate(zip(tenant_names, previous_readings)):
        print(f"{i+1}. {name}: Previous Reading = {prev:.2f}")
    
    # Ask about timestamp
    current_time = datetime.now()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nCurrent timestamp: {current_time_str}")
    
    custom_date = None
    use_current_timestamp = input("Use current timestamp? (y/n): ").lower().strip()
    
    if use_current_timestamp != 'y':
        while True:
            try:
                date_input = input("Enter date (YYYY-MM-DD): ").strip()
                # Validate date format
                try:
                    custom_date = datetime.strptime(date_input, "%Y-%m-%d")
                    # Keep the current time, just change the date
                    custom_date = custom_date.replace(
                        hour=current_time.hour,
                        minute=current_time.minute,
                        second=current_time.second
                    )
                    print(f"Using date: {custom_date.strftime('%Y-%m-%d')} with current time: {current_time.strftime('%H:%M:%S')}")
                    break
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD format.")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
    
    # Get current readings
    print("\nEnter current meter readings:")
    tenant_readings = []
    for i, (name, prev) in enumerate(zip(tenant_names, previous_readings)):
        while True:
            try:
                reading_input = input(f"{name} current reading (previous: {prev:.2f}): ").strip()
                
                # Empty input is not allowed for current readings
                if not reading_input:
                    print("Current reading cannot be empty. Please enter a value.")
                    continue
                
                reading = float(reading_input)
                if reading < prev:
                    print(f"Current reading cannot be less than previous reading ({prev:.2f}).")
                    continue
                tenant_readings.append(reading)
                break
            except ValueError:
                print("Please enter a valid number.")
    
    # Ask if there's a recharge to record
    record_recharge = input("\nDo you want to record a recharge with these readings? (y/n): ").lower().strip()
    
    last_recharge = 0
    recharge_tenant = None
    
    if record_recharge == 'y':
        print("\nEnter the recharge information:")
        while True:
            try:
                last_recharge = float(input("Recharge amount (Rs.): "))
                if last_recharge <= 0:
                    print("Recharge amount must be positive.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        while True:
            try:
                recharge_tenant = int(input(f"Which tenant paid for the recharge (1-{len(tenant_names)})? "))
                if recharge_tenant < 1 or recharge_tenant > len(tenant_names):
                    print(f"Please enter a number between 1 and {len(tenant_names)}.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
    else:
        print("\nNo recharge will be recorded. Only consumption will be calculated.")
    
    # Display timestamp being used
    if custom_date:
        print(f"\nUsing timestamp: {custom_date.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\nUsing current timestamp: {current_time_str}")
    
    return tenant_readings, last_recharge, recharge_tenant, custom_date


def get_user_input_for_recharge(tenant_names, tenant_balances, last_updated):
    """
    Get user input for recharge information only
    
    Parameters:
    - tenant_names: List of tenant names
    - tenant_balances: List of current balances
    - last_updated: Timestamp of when the data was last updated
    
    Returns:
    - last_recharge: Amount of the recharge
    - recharge_tenant: Index of the tenant who paid for the recharge
    - custom_date: Custom date if provided by user, otherwise None
    """
    print("\n" + "="*60)
    print(" "*15 + "ELECTRICITY RECHARGE INPUT")
    print("="*60)
    
    # Display last updated timestamp
    print(f"\nLast updated: {last_updated}")
    
    # Display current balances
    print("\nCurrent balances:")
    for i, (name, balance) in enumerate(zip(tenant_names, tenant_balances)):
        print(f"{i+1}. {name}: Balance = Rs.{balance:.2f}")
    
    # Ask about timestamp
    current_time = datetime.now()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nCurrent timestamp: {current_time_str}")
    
    custom_date = None
    use_current_timestamp = input("Use current timestamp? (y/n): ").lower().strip()
    
    if use_current_timestamp != 'y':
        while True:
            try:
                date_input = input("Enter date (YYYY-MM-DD): ").strip()
                # Validate date format
                try:
                    custom_date = datetime.strptime(date_input, "%Y-%m-%d")
                    # Keep the current time, just change the date
                    custom_date = custom_date.replace(
                        hour=current_time.hour,
                        minute=current_time.minute,
                        second=current_time.second
                    )
                    print(f"Using date: {custom_date.strftime('%Y-%m-%d')} with current time: {current_time.strftime('%H:%M:%S')}")
                    break
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD format.")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
    
    print("\nEnter the recharge information:")
    while True:
        try:
            last_recharge = float(input("Recharge amount (Rs.): "))
            if last_recharge <= 0:
                print("Recharge amount must be positive.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    while True:
        try:
            recharge_tenant = int(input(f"Which tenant paid for the recharge (1-{len(tenant_names)})? "))
            if recharge_tenant < 1 or recharge_tenant > len(tenant_names):
                print(f"Please enter a number between 1 and {len(tenant_names)}.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    # Display timestamp being used
    if custom_date:
        print(f"\nUsing timestamp: {custom_date.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\nUsing current timestamp: {current_time_str}")
    
    return last_recharge, recharge_tenant, custom_date


def display_transactions():
    """Display the history of all transactions"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    if not os.path.exists(transactions_file):
        print("No transaction history found.")
        return
    
    print("\n" + "="*100)
    print(" "*35 + "TRANSACTION HISTORY")
    print("="*100)
    
    try:
        from colorama import Fore, Style, init
        init()  # Initialize colorama
        has_colors = True
    except ImportError:
        has_colors = False
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            
            # Read header
            header = next(reader, None)
            if not header:
                print("Transaction file is empty or corrupted.")
                return
            
            # Format and display header
            if has_colors:
                print(f"{Fore.YELLOW}{' | '.join(header)}{Style.RESET_ALL}")
            else:
                print(' | '.join(header))
            
            print("-"*100)
            
            # Read and display data rows with alternating colors for better readability
            rows = list(reader)
            for i, row in enumerate(rows):
                if has_colors:
                    if row and len(row) > 0:
                        # Color code by transaction type
                        if row[0] == "READING":
                            type_color = Fore.CYAN
                        elif row[0] == "RECHARGE":
                            type_color = Fore.GREEN
                        else:
                            type_color = Fore.WHITE
                        
                        # Highlight timestamp
                        if len(row) > 1:
                            row[1] = f"{Fore.YELLOW}{row[1]}{Style.RESET_ALL}"
                        
                        # Color the type
                        row[0] = f"{type_color}{row[0]}{Style.RESET_ALL}"
                        
                    print(' | '.join(row))
                else:
                    print(' | '.join(row))
        
        print("="*100 + "\n")
        
        # Display number of records
        print(f"Total transactions: {len(rows)}")
        
        # Display date range
        if rows:
            first_date = rows[0][1] if len(rows[0]) > 1 else "Unknown"
            last_date = rows[-1][1] if len(rows[-1]) > 1 else "Unknown"
            print(f"Date range: {first_date} to {last_date}")
            
            # Count by type
            readings = sum(1 for row in rows if row and len(row) > 0 and row[0] == "READING")
            recharges = sum(1 for row in rows if row and len(row) > 0 and row[0] == "RECHARGE")
            print(f"Readings: {readings}, Recharges: {recharges}")
    
    except Exception as e:
        print(f"Error displaying transactions: {e}")


def get_last_recharge_info(tenant_names):
    """
    Get information about the last recharge: amount, tenant who paid, and readings at that time
    
    Returns:
    - last_recharge_amount: Amount of the last recharge (0 if none found)
    - last_recharge_tenant_index: Index of the tenant who paid (None if none found)
    - last_recharge_readings: Readings at the time of the last recharge
    """
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    # Default values
    last_recharge_amount = 0
    last_recharge_tenant_index = None
    last_recharge_readings = [0] * len(tenant_names)
    
    if not os.path.exists(transactions_file):
        return last_recharge_amount, last_recharge_tenant_index, last_recharge_readings
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows
            rows = list(reader)
            
            if not rows:
                return last_recharge_amount, last_recharge_tenant_index, last_recharge_readings
            
            # Find the last recharge
            last_recharge_index = -1
            last_recharge_tenant_name = None
            
            for i, row in enumerate(reversed(rows)):
                if len(row) >= 4 and row[0] == "RECHARGE":
                    last_recharge_index = len(rows) - 1 - i
                    try:
                        last_recharge_amount = float(row[3])
                        last_recharge_tenant_name = row[2]
                    except (ValueError, IndexError):
                        pass
                    break
            
            # If no recharge found, return defaults
            if last_recharge_index == -1 or last_recharge_tenant_name is None:
                return last_recharge_amount, last_recharge_tenant_index, last_recharge_readings
            
            # Find the tenant index
            for i, name in enumerate(tenant_names):
                if name == last_recharge_tenant_name:
                    last_recharge_tenant_index = i + 1  # 1-based index
                    break
            
            # Get the readings at the time of the last recharge
            readings_at_recharge = {}
            
            # Look for the latest readings before the recharge
            for i in range(last_recharge_index):
                row = rows[i]
                if len(row) >= 5 and row[0] == "READING":
                    tenant_name = row[2]
                    try:
                        reading = float(row[3])
                        readings_at_recharge[tenant_name] = reading
                    except (ValueError, IndexError):
                        continue
            
            # Convert to list in the same order as tenant_names
            for i, name in enumerate(tenant_names):
                if name in readings_at_recharge:
                    last_recharge_readings[i] = readings_at_recharge[name]
    
    except Exception as e:
        print(f"Warning: Could not read last recharge info: {e}")
    
    return last_recharge_amount, last_recharge_tenant_index, last_recharge_readings


def sync_balances_with_previous_recharge(tenant_names, tenant_readings, tenant_balances):
    """
    Sync balances with the previous recharge by distributing the previous recharge amount
    proportionally based on consumption since that recharge.
    
    Parameters:
    - tenant_names: List of tenant names
    - tenant_readings: Current meter readings
    - tenant_balances: Current balances to be updated
    
    Returns:
    - Updated tenant balances
    - Whether a sync was performed
    """
    # Get the last recharge info
    prev_recharge_amount, prev_recharge_tenant, prev_recharge_readings = get_last_recharge_info(tenant_names)
    
    # If no previous recharge, nothing to sync
    if prev_recharge_amount <= 0 or prev_recharge_tenant is None:
        return tenant_balances, False
    
    # Calculate consumption since last recharge
    consumptions = []
    for i, curr in enumerate(tenant_readings):
        prev = prev_recharge_readings[i]
        consumption = curr - prev
        consumptions.append(consumption)
    
    # Calculate total consumption
    total_consumption = sum(consumptions)
    
    # If no consumption, nothing to sync
    if total_consumption <= 0:
        return tenant_balances, False
    
    print("\n" + "="*60)
    print(" "*15 + "SYNCING BALANCES WITH PREVIOUS RECHARGE")
    print("="*60)
    print(f"Previous recharge: Rs.{prev_recharge_amount:.2f} by {tenant_names[prev_recharge_tenant-1]}")
    
    # Reset balances to zero
    synced_balances = [0] * len(tenant_balances)
    
    # Add the previous recharge to the tenant who paid
    synced_balances[prev_recharge_tenant - 1] += prev_recharge_amount
    
    # Calculate each tenant's share
    shares = [consumption / total_consumption for consumption in consumptions]
    
    # Deduct each tenant's share
    for i, share in enumerate(shares):
        cost = prev_recharge_amount * share
        synced_balances[i] -= cost
    
    # Display consumption and costs
    print("\n" + "="*60)
    print(" "*15 + "CONSUMPTION SINCE PREVIOUS RECHARGE")
    print("="*60)
    print(f"{'Tenant':<20} {'Consumption (kWh)':<20} {'Cost (Rs.)':<15}")
    print("-"*60)
    for i, (name, consumption, share) in enumerate(zip(tenant_names, consumptions, shares)):
        cost = prev_recharge_amount * share
        print(f"{name:<20} {consumption:.2f} kWh{' '*11} Rs.{cost:.2f}")
    print(f"{'TOTAL':<20} {total_consumption:.2f} kWh{' '*11} Rs.{prev_recharge_amount:.2f}")
    
    # Display synced balances
    print("\n" + "="*60)
    print(" "*20 + "SYNCED BALANCES")
    print("="*60)
    print(f"{'Tenant':<20} {'Balance (Rs.)':<15}")
    print("-"*60)
    for name, balance in zip(tenant_names, synced_balances):
        balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
        print(f"{name:<20} {balance_sign}Rs.{balance:.2f}")
    
    return synced_balances, True


def display_tenant_dashboard(tenant_names, tenant_balances):
    """
    Display a comprehensive dashboard for all tenants showing readings, recharges, and recommendations
    
    Parameters:
    - tenant_names: List of tenant names
    - tenant_balances: Current balances for all tenants
    """
    print("\n" + "="*80)
    print(" "*30 + "TENANT DASHBOARD")
    print("="*80)
    
    # Get the latest readings for each tenant
    latest_readings = []
    previous_readings = []
    for name in tenant_names:
        latest = get_latest_reading_for_tenant(name)
        previous = get_previous_reading_for_tenant(name, latest)
        latest_readings.append(latest)
        previous_readings.append(previous)
    
    # Get the last recharge info
    last_recharge_amount, last_recharge_tenant_index, _ = get_last_recharge_info(tenant_names)
    last_recharge_tenant = tenant_names[last_recharge_tenant_index-1] if last_recharge_tenant_index else "None"
    last_recharge_date = get_last_recharge_date()
    
    # Calculate consumption for each tenant
    consumptions = []
    for i, (prev, curr) in enumerate(zip(previous_readings, latest_readings)):
        consumption = curr - prev
        consumptions.append(consumption)
    
    # Determine who should pay next (the one with the most negative balance)
    if tenant_balances:
        most_negative_index = tenant_balances.index(min(tenant_balances))
        next_recharge_tenant = tenant_names[most_negative_index]
    else:
        next_recharge_tenant = "Unknown"
    
    try:
        from colorama import Fore, Style, init
        init()  # Initialize colorama
        has_colors = True
    except ImportError:
        has_colors = False
    
    # Display meter readings section
    print("\n" + "-"*80)
    print(" "*30 + "METER READINGS")
    print("-"*80)
    print(f"{'Tenant':<20} {'Previous':<15} {'Current':<15} {'Consumption':<15}")
    print("-"*80)
    
    for i, (name, prev, curr, consumption) in enumerate(zip(tenant_names, previous_readings, latest_readings, consumptions)):
        if has_colors:
            name_color = Fore.CYAN
            print(f"{name_color}{name:<20}{Style.RESET_ALL} {prev:.2f}{' '*10} {curr:.2f}{' '*10} {consumption:.2f} kWh")
        else:
            print(f"{name:<20} {prev:.2f}{' '*10} {curr:.2f}{' '*10} {consumption:.2f} kWh")
    
    # Display recharge information
    print("\n" + "-"*80)
    print(" "*30 + "RECHARGE INFORMATION")
    print("-"*80)
    
    if has_colors:
        print(f"Last Recharge Amount: {Fore.GREEN}Rs.{last_recharge_amount:.2f}{Style.RESET_ALL}")
        print(f"Last Recharge By: {Fore.CYAN}{last_recharge_tenant}{Style.RESET_ALL}")
        print(f"Last Recharge Date: {Fore.YELLOW}{last_recharge_date}{Style.RESET_ALL}")
    else:
        print(f"Last Recharge Amount: Rs.{last_recharge_amount:.2f}")
        print(f"Last Recharge By: {last_recharge_tenant}")
        print(f"Last Recharge Date: {last_recharge_date}")
    
    # Display current balances
    print("\n" + "-"*80)
    print(" "*30 + "CURRENT BALANCES")
    print("-"*80)
    print(f"{'Tenant':<20} {'Balance (Rs.)':<15} {'Status':<15}")
    print("-"*80)
    
    for i, (name, balance) in enumerate(zip(tenant_names, tenant_balances)):
        status = ""
        if name == next_recharge_tenant:
            status = "NEXT RECHARGE"
        
        if has_colors:
            name_color = Fore.CYAN
            balance_color = Fore.GREEN if balance >= 0 else Fore.RED
            status_color = Fore.YELLOW if status else ""
            balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
            print(f"{name_color}{name:<20}{Style.RESET_ALL} {balance_color}{balance_sign}Rs.{balance:.2f}{Style.RESET_ALL}{' '*5}{status_color}{status}{Style.RESET_ALL}")
        else:
            balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
            print(f"{name:<20} {balance_sign}Rs.{balance:.2f}{' '*5}{status}")
    
    # Display recommendation
    print("\n" + "-"*80)
    print(" "*30 + "RECOMMENDATION")
    print("-"*80)
    
    if has_colors:
        print(f"{Fore.YELLOW}Based on current balances, {Fore.CYAN}{next_recharge_tenant}{Fore.YELLOW} should pay the next recharge.{Style.RESET_ALL}")
    else:
        print(f"Based on current balances, {next_recharge_tenant} should pay the next recharge.")
    
    print("="*80)


def get_previous_reading_for_tenant(tenant_name, latest_reading):
    """Get the previous meter reading for a specific tenant (one before the latest)"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    # Default to zero if no previous reading
    previous_reading = 0
    
    if not os.path.exists(transactions_file):
        return previous_reading
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows to find readings for this tenant
            rows = list(reader)
            
            if not rows:
                return previous_reading
            
            # Find all readings for this tenant
            tenant_readings = []
            for row in rows:
                if len(row) >= 5 and row[0] == "READING" and row[2] == tenant_name:
                    try:
                        reading = float(row[3])
                        tenant_readings.append(reading)
                    except (ValueError, IndexError):
                        continue
            
            # If we have at least two readings, return the second-to-last one
            if len(tenant_readings) >= 2 and tenant_readings[-1] == latest_reading:
                return tenant_readings[-2]
            elif len(tenant_readings) >= 1 and tenant_readings[-1] != latest_reading:
                return tenant_readings[-1]
    
    except Exception as e:
        print(f"Warning: Could not read previous reading for {tenant_name}: {e}")
    
    return previous_reading


def get_last_recharge_date():
    """Get the date of the last recharge"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    # Default if no recharge found
    last_recharge_date = "No previous recharge"
    
    if not os.path.exists(transactions_file):
        return last_recharge_date
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows
            rows = list(reader)
            
            if not rows:
                return last_recharge_date
            
            # Find the last recharge
            for row in reversed(rows):
                if len(row) >= 2 and row[0] == "RECHARGE":
                    return row[1]  # Return the timestamp
    
    except Exception as e:
        print(f"Warning: Could not read last recharge date: {e}")
    
    return last_recharge_date


def main_menu():
    """Display the main menu and handle user choices"""
    while True:
        print("\n" + "="*60)
        print(" "*15 + "ELECTRICITY BILLING SYSTEM")
        print("="*60)
        
        # Display current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Current time: {current_time}")
        
        print("\n1. Enter new meter readings")
        print("2. Record a recharge")
        print("3. View transaction history")
        print("4. View tenant dashboard")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            # Load current state
            tenant_names, tenant_balances, last_updated = load_from_csv()
            
            # Check if this is the first entry
            is_first_entry = not has_any_readings()
            
            # Get user input for readings
            tenant_readings, last_recharge, recharge_tenant, custom_date = get_user_input(
                tenant_names, tenant_balances, last_updated
            )
            
            # For first entry, just record the readings without calculating consumption
            if is_first_entry:
                print("\nThis is the initial meter reading. No consumption calculated.")
                # Save readings to transactions file
                timestamp = custom_date if custom_date else datetime.now()
                
                # Save each reading as a separate transaction
                for i, (name, reading) in enumerate(zip(tenant_names, tenant_readings)):
                    save_transaction(
                        transaction_type="READING",
                        timestamp=timestamp,
                        tenant_name=name,
                        reading=reading,
                        tenant_balances=tenant_balances,
                        tenant_names=tenant_names,
                        consumption=0  # No consumption for initial readings
                    )
                
                print("\nInitial readings saved successfully!")
            else:
                # Get previous readings for consumption calculation
                previous_readings = get_previous_readings(tenant_names)
                
                # Calculate consumption since previous readings
                consumptions = []
                for i, curr in enumerate(tenant_readings):
                    prev = previous_readings[i]
                    if curr < prev:
                        print(f"Error: Current reading ({curr}) cannot be less than previous reading ({prev}) for {tenant_names[i]}")
                        break
                    consumptions.append(curr - prev)
                else:
                    # Only proceed if all readings are valid
                    # Save readings to transactions file
                    timestamp = custom_date if custom_date else datetime.now()
                    
                    # Save each reading as a separate transaction
                    for i, (name, reading, consumption) in enumerate(zip(tenant_names, tenant_readings, consumptions)):
                        save_transaction(
                            transaction_type="READING",
                            timestamp=timestamp,
                            tenant_name=name,
                            reading=reading,
                            tenant_balances=tenant_balances,
                            tenant_names=tenant_names,
                            consumption=consumption
                        )
                    
                    # Display consumption
                    print("\n" + "="*60)
                    print(" "*15 + "ELECTRICITY CONSUMPTION SUMMARY")
                    print("="*60)
                    print(f"{'Tenant':<20} {'Consumption (kWh)':<20}")
                    print("-"*60)
                    total_consumption = sum(consumptions)
                    for name, consumption in zip(tenant_names, consumptions):
                        print(f"{name:<20} {consumption:.2f} kWh")
                    print(f"{'TOTAL':<20} {total_consumption:.2f} kWh")
                    
                    print("\nReadings saved successfully!")
                
                # If there's a recharge, process it
                if last_recharge > 0 and recharge_tenant is not None:
                    # First, sync balances with previous recharge
                    tenant_balances, synced = sync_balances_with_previous_recharge(
                        tenant_names, tenant_readings, tenant_balances
                    )
                    
                    # Now process the new recharge
                    # Add recharge to the tenant who paid
                    tenant_balances[recharge_tenant - 1] += last_recharge
                    
                    # Save recharge transaction with updated balances
                    save_transaction(
                        transaction_type="RECHARGE",
                        timestamp=timestamp,
                        tenant_name=tenant_names[recharge_tenant-1],
                        recharge_amount=last_recharge,
                        tenant_balances=tenant_balances,
                        tenant_names=tenant_names
                    )
                    
                    print(f"\nRecharge of Rs.{last_recharge:.2f} by {tenant_names[recharge_tenant-1]} recorded successfully!")
                    
                    # Display updated balances
                    print("\n" + "="*60)
                    print(" "*20 + "UPDATED BALANCES")
                    print("="*60)
                    print(f"{'Tenant':<20} {'Balance (Rs.)':<15}")
                    print("-"*60)
                    for name, balance in zip(tenant_names, tenant_balances):
                        balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
                        print(f"{name:<20} {balance_sign}Rs.{balance:.2f}")
            
            # Ask if user wants to log another recharge
            log_recharge = input("\nDo you want to log another recharge? (y/n): ").lower().strip()
            if log_recharge == 'y':
                # Get recharge information
                last_recharge, recharge_tenant, custom_date = get_user_input_for_recharge(
                    tenant_names, tenant_balances, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                # First, sync balances with previous recharge
                tenant_balances, synced = sync_balances_with_previous_recharge(
                    tenant_names, tenant_readings, tenant_balances
                )
                
                # Now process the new recharge
                # Add recharge to the tenant who paid
                tenant_balances[recharge_tenant - 1] += last_recharge
                
                # Save recharge transaction
                timestamp = custom_date if custom_date else datetime.now()
                save_transaction(
                    transaction_type="RECHARGE",
                    timestamp=timestamp,
                    tenant_name=tenant_names[recharge_tenant-1],
                    recharge_amount=last_recharge,
                    tenant_balances=tenant_balances,
                    tenant_names=tenant_names
                )
                
                print(f"\nRecharge of Rs.{last_recharge:.2f} by {tenant_names[recharge_tenant-1]} recorded successfully!")
                
                # Display updated balances
                print("\n" + "="*60)
                print(" "*20 + "UPDATED BALANCES")
                print("="*60)
                print(f"{'Tenant':<20} {'Balance (Rs.)':<15}")
                print("-"*60)
                for name, balance in zip(tenant_names, tenant_balances):
                    balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
                    print(f"{name:<20} {balance_sign}Rs.{balance:.2f}")
            
        elif choice == '2':
            # Load current state
            tenant_names, tenant_balances, last_updated = load_from_csv()
            
            # Get the latest readings for each tenant
            latest_readings = []
            for name in tenant_names:
                reading = get_latest_reading_for_tenant(name)
                latest_readings.append(reading)
            
            # Get recharge information
            last_recharge, recharge_tenant, custom_date = get_user_input_for_recharge(
                tenant_names, tenant_balances, last_updated
            )
            
            # First, sync balances with previous recharge
            tenant_balances, synced = sync_balances_with_previous_recharge(
                tenant_names, latest_readings, tenant_balances
            )
            
            # Now process the new recharge
            # Add recharge to the tenant who paid
            tenant_balances[recharge_tenant - 1] += last_recharge
            
            # Save recharge transaction
            timestamp = custom_date if custom_date else datetime.now()
            save_transaction(
                transaction_type="RECHARGE",
                timestamp=timestamp,
                tenant_name=tenant_names[recharge_tenant-1],
                recharge_amount=last_recharge,
                tenant_balances=tenant_balances,
                tenant_names=tenant_names
            )
            
            print(f"\nRecharge of Rs.{last_recharge:.2f} by {tenant_names[recharge_tenant-1]} recorded successfully!")
            
            # Display updated balances
            print("\n" + "="*60)
            print(" "*20 + "UPDATED BALANCES")
            print("="*60)
            print(f"{'Tenant':<20} {'Balance (Rs.)':<15}")
            print("-"*60)
            for name, balance in zip(tenant_names, tenant_balances):
                balance_sign = "+" if balance > 0 else ""  # Add plus sign for positive balances
                print(f"{name:<20} {balance_sign}Rs.{balance:.2f}")
            
        elif choice == '3':
            display_transactions()
            
        elif choice == '4':
            # Load current state
            tenant_names, tenant_balances, last_updated = load_from_csv()
            
            # Display tenant dashboard
            display_tenant_dashboard(tenant_names, tenant_balances)
            
        elif choice == '5':
            print("Thank you for using the Electricity Billing System. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def get_latest_reading_for_tenant(tenant_name):
    """Get the latest meter reading for a specific tenant"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    # Default to zero if no previous reading
    latest_reading = 0
    
    if not os.path.exists(transactions_file):
        return latest_reading
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Read all rows to find the latest reading for the tenant
            rows = list(reader)
            
            if not rows:
                return latest_reading
            
            # Look for the latest reading entry for this tenant
            for row in reversed(rows):
                if len(row) >= 5 and row[0] == "READING" and row[2] == tenant_name:
                    try:
                        latest_reading = float(row[3])
                        break
                    except (ValueError, IndexError):
                        # If there's an error parsing, continue with the next row
                        continue
    except Exception as e:
        print(f"Warning: Could not read latest reading for {tenant_name}: {e}")
    
    return latest_reading


def has_any_readings():
    """Check if there are any readings in the transaction history"""
    transactions_file = os.path.join("electricity_data", "transactions.csv")
    
    if not os.path.exists(transactions_file):
        return False
    
    try:
        with open(transactions_file, 'r', newline='') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            
            # Check if there are any READING transactions
            for row in reader:
                if len(row) >= 2 and row[0] == "READING":
                    return True
    except:
        pass
    
    return False


if __name__ == "__main__":
    # Try to import colorama for colored output
    try:
        import colorama
        print("Using colorama for colored output")
    except ImportError:
        print("For colored output, install colorama: pip install colorama")
    
    # Run the main menu
    main_menu()

from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
import csv
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
import subprocess
import shlex
import re
import json
import threading

from report import generate_pdf_from_original_csv

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'csv'}
CSV_HEADERS = ['Type', 'Timestamp', 'Tenant', 'Reading/Amount', 'Consumption', 'Balances']
TENANTS = ['Ground Floor', 'First Floor', 'Second Floor']
CONFIG_PATH = 'app_config.json'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.secret_key = 'change-me'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def flash_with_status(message: str, status: str = 'neutral'):
    """Flash a message with a status type (success, error, neutral)"""
    # Store the status in session to be retrieved in templates
    session.setdefault('flash_statuses', []).append(status)
    flash(message)


def get_flash_messages_with_status():
    """Get flash messages with their corresponding status types"""
    from flask import get_flashed_messages
    messages = get_flashed_messages()
    statuses = session.pop('flash_statuses', [])
    
    # Ensure we have a status for each message, default to 'neutral'
    while len(statuses) < len(messages):
        statuses.append('neutral')
    
    return list(zip(messages, statuses))


# Make helper function available in templates
app.jinja_env.globals.update(get_flash_messages_with_status=get_flash_messages_with_status)


def determine_git_command_status(code: int, out: str, err: str, action: str) -> str:
    """Determine if a git command was successful based on return code and output"""
    if code == 0:
        # Check for specific success indicators
        if action == 'pull':
            if 'Already up to date' in out or 'Fast-forward' in out or 'Merge made' in out:
                return 'success'
            elif 'up-to-date' in out.lower() or 'already up to date' in out.lower():
                return 'success'
        elif action == 'push':
            if 'To ' in out and ('new branch' in out or 'branch' in out):
                return 'success'
            elif not err or 'Everything up-to-date' in out:
                return 'success'
        elif action == 'commit':
            if 'files changed' in out or 'create mode' in out or 'nothing to commit' in out:
                return 'success'
        
        # If return code is 0 but we can't determine specific success, it's likely successful
        return 'success'
    else:
        return 'error'


def load_config() -> Dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except Exception:
            return {}
    return {}


def save_config(cfg: Dict) -> None:
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def list_available_csvs():
    csvs = []
    for name in os.listdir('.'):
        if name.lower().endswith('.csv'):
            csvs.append({'label': f"{name} (project)", 'path': name})
    for name in os.listdir(UPLOAD_FOLDER):
        if name.lower().endswith('.csv'):
            csvs.append({'label': f"{name} (uploads)", 'path': os.path.join(UPLOAD_FOLDER, name)})
    seen = set()
    unique = []
    for c in csvs:
        if c['path'] not in seen:
            unique.append(c)
            seen.add(c['path'])
    return unique


def ensure_csv_with_header(path: str):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def validate_csv_file(path: str) -> str:
    """Validate CSV file and return error message if invalid, None if valid"""
    if not path or not path.strip():
        return "No CSV file configured. Please select a default CSV file in Settings."
    
    if not os.path.exists(path):
        return f"CSV file not found: {path}. Please check the file path in Settings."
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if not header:
                return f"CSV file is empty or invalid: {path}"
            
            # Check if required columns exist
            required_columns = set(CSV_HEADERS)
            actual_columns = set(header)
            
            if not required_columns.issubset(actual_columns):
                missing = required_columns - actual_columns
                return f"CSV file is missing required columns: {', '.join(missing)}. Expected columns: {', '.join(CSV_HEADERS)}"
            
            # Check if we can read at least one row to ensure format is valid
            try:
                next(reader, None)  # Try to read one data row
            except csv.Error as e:
                return f"CSV file format is invalid: {e}"
                
    except Exception as e:
        return f"Error reading CSV file: {e}"
    
    return None  # No errors


def get_current_csv() -> str:
    cfg = load_config()
    cur = session.get('current_csv') or cfg.get('preferences', {}).get('csv_path')
    if cur and os.path.exists(cur):
        return cur
    if os.path.exists('transactions.csv'):
        session['current_csv'] = 'transactions.csv'
        return 'transactions.csv'
    csvs = list_available_csvs()
    if csvs:
        session['current_csv'] = csvs[0]['path']
        return csvs[0]['path']
    default = os.path.join(UPLOAD_FOLDER, 'transactions.csv')
    session['current_csv'] = default
    return default


def set_current_csv(path: str):
    session['current_csv'] = path
    cfg = load_config()
    prefs = cfg.get('preferences', {})
    prefs['csv_path'] = path
    cfg['preferences'] = prefs
    save_config(cfg)


class CsvCalculator:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.transactions: List[Dict] = []
        self.balances: Dict[str, Decimal] = {t: Decimal('0.00') for t in TENANTS}
        self.last_readings: Dict[str, float] = {t: 0.0 for t in TENANTS}
        self.last_readings_before_recharge: Dict[str, float] = {t: 0.0 for t in TENANTS}
        self.last_recharge_amount: float = 0.0
        self.last_recharge_tenant: str = ''
        self.load()

    def load(self) -> None:
        ensure_csv_with_header(self.csv_path)
        rows: List[List[str]] = []
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            rows = list(reader)
        self.transactions.clear()
        self.balances = {t: Decimal('0.00') for t in TENANTS}
        self.last_readings = {t: 0.0 for t in TENANTS}
        self.last_readings_before_recharge = {t: 0.0 for t in TENANTS}
        self.last_recharge_amount = 0.0
        self.last_recharge_tenant = ''
        for row in rows:
            if len(row) < 6:
                continue
            rec = {
                'Type': row[0],
                'Timestamp': row[1],
                'Tenant': row[2],
                'Reading/Amount': row[3],
                'Consumption': row[4],
                'Balances': row[5],
            }
            self.transactions.append(rec)
            if rec['Balances']:
                try:
                    self._update_balances_from_string(rec['Balances'])
                except Exception:
                    pass
        for rec in reversed(self.transactions):
            if rec['Type'] == 'RECHARGE':
                try:
                    self.last_recharge_amount = float(rec['Reading/Amount'])
                except Exception:
                    self.last_recharge_amount = 0.0
                self.last_recharge_tenant = rec['Tenant']
                break
        latest_recharge_idx = None
        for idx in range(len(self.transactions) - 1, -1, -1):
            if self.transactions[idx]['Type'] == 'RECHARGE':
                latest_recharge_idx = idx
                break
        if latest_recharge_idx is not None:
            seen = set()
            for i in range(latest_recharge_idx - 1, -1, -1):
                tr = self.transactions[i]
                if tr['Type'] == 'READING' and tr['Tenant'] not in seen:
                    try:
                        self.last_readings_before_recharge[tr['Tenant']] = float(tr['Reading/Amount'])
                    except Exception:
                        self.last_readings_before_recharge[tr['Tenant']] = 0.0
                    seen.add(tr['Tenant'])
                    if len(seen) == 3:
                        break
        for t in TENANTS:
            for rec in reversed(self.transactions):
                if rec['Type'] == 'READING' and rec['Tenant'] == t:
                    try:
                        self.last_readings[t] = float(rec['Reading/Amount'])
                    except Exception:
                        self.last_readings[t] = 0.0
                    break

    def _update_balances_from_string(self, s: str) -> None:
        parts = [p.strip() for p in s.split(';') if p.strip()]
        for p in parts:
            if ': Rs.' in p:
                tenant, amt = p.split(': Rs.', 1)
                self.balances[tenant.strip()] = Decimal(amt.strip())

    def _balances_string(self) -> str:
        return '; '.join([f"{t}: Rs.{self.balances[t]:.2f}" for t in TENANTS])

    def _append_row(self, row: Dict) -> None:
        file_exists = os.path.exists(self.csv_path)
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(CSV_HEADERS)
            w.writerow([
                row['Type'],
                row['Timestamp'],
                row['Tenant'],
                row['Reading/Amount'],
                row.get('Consumption', ''),
                row.get('Balances', ''),
            ])

    def calculate_and_deduct_previous_recharge(self) -> None:
        if not any(self.last_readings_before_recharge.values()):
            return
        consumption_since = {}
        for t in TENANTS:
            consumption_since[t] = max(0.0, self.last_readings[t] - self.last_readings_before_recharge[t])
        total = sum(consumption_since.values())
        if total <= 0 or self.last_recharge_amount <= 0:
            return
        for t in TENANTS:
            ratio = consumption_since[t] / total if total > 0 else 0.0
            deduction = (Decimal(str(self.last_recharge_amount)) * Decimal(str(ratio))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.balances[t] -= deduction

    def record_readings_and_recharge(self, readings: Dict[str, float], recharge_tenant: str, recharge_amount: float) -> None:
        for t in TENANTS:
            new_val = readings.get(t)
            if new_val is None:
                raise ValueError(f"Missing reading for {t}")
            if new_val < self.last_readings[t]:
                raise ValueError(f"New reading for {t} ({new_val}) cannot be less than previous ({self.last_readings[t]})")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for t in TENANTS:
            consumption = readings[t] - self.last_readings[t]
            self.last_readings[t] = readings[t]
            self._append_row({
                'Type': 'READING',
                'Timestamp': timestamp,
                'Tenant': t,
                'Reading/Amount': f"{readings[t]}",
                'Consumption': f"{consumption}",
                'Balances': self._balances_string(),
            })
        self.calculate_and_deduct_previous_recharge()
        if recharge_amount and recharge_tenant in TENANTS:
            self.balances[recharge_tenant] += Decimal(str(recharge_amount))
            self.last_recharge_amount = recharge_amount
            self.last_recharge_tenant = recharge_tenant
            for t in TENANTS:
                self.last_readings_before_recharge[t] = self.last_readings[t]
            timestamp2 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._append_row({
                'Type': 'RECHARGE',
                'Timestamp': timestamp2,
                'Tenant': recharge_tenant,
                'Reading/Amount': f"{recharge_amount}",
                'Consumption': '',
                'Balances': self._balances_string(),
            })
        self.load()

    def current_status(self) -> Dict:
        return {
            'balances': {t: f"Rs.{self.balances[t]:.2f}" for t in TENANTS},
            'last_readings': {t: self.last_readings[t] for t in TENANTS},
            'last_recharge_amount': self.last_recharge_amount,
            'last_recharge_tenant': self.last_recharge_tenant or 'N/A',
        }

    def preview_last_group_for_revert(self) -> Tuple[str, List[Dict]]:
        """Preview the last group of transactions that would be reverted"""
        if not self.transactions:
            return '', []
        
        # Find the last timestamp
        last_timestamp = self.transactions[-1]['Timestamp']
        
        # Find all transactions with the same timestamp (same group)
        preview_rows = []
        for transaction in reversed(self.transactions):
            if transaction['Timestamp'] == last_timestamp:
                preview_rows.append(transaction)
            else:
                break
        
        # Reverse to show in chronological order
        preview_rows.reverse()
        
        return last_timestamp, preview_rows

    def revert_last_group(self) -> int:
        """Revert the last group of transactions and return count of removed rows"""
        if not self.transactions:
            return 0
        
        # Find the last timestamp
        last_timestamp = self.transactions[-1]['Timestamp']
        
        # Count how many transactions have this timestamp
        count_to_remove = 0
        for transaction in reversed(self.transactions):
            if transaction['Timestamp'] == last_timestamp:
                count_to_remove += 1
            else:
                break
        
        if count_to_remove == 0:
            return 0
        
        # Read all rows from CSV
        rows = []
        with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = list(reader)
        
        # Remove the last count_to_remove rows
        rows = rows[:-count_to_remove]
        
        # Write back to CSV
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(rows)
        
        # Reload the calculator state
        self.load()
        
        return count_to_remove


# Metrics

def compute_metrics(csv_path: str) -> Dict:
    ensure_csv_with_header(csv_path)
    totals = {t: 0.0 for t in TENANTS}
    monthly = {}
    monthly_total = {}
    yearly_total = {}
    yearly_per_tenant = {t: {} for t in TENANTS}
    recharges_total = 0.0
    recharges_per_tenant = {t: 0.0 for t in TENANTS}
    count_readings = 0
    count_recharges = 0
    
    # Track initial readings to exclude them from calculations
    initial_readings = {}
    first_timestamp = None
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 5:
                continue
            typ, ts, tenant, val, cons = row[0], row[1], row[2], row[3], row[4]
            ym = (ts or '')[:7]
            yr = (ts or '')[:4]
            
            # Track the first timestamp to identify initial readings
            if first_timestamp is None:
                first_timestamp = ts
            
            if typ == 'READING':
                try:
                    c = float(cons) if cons else 0.0
                except Exception:
                    c = 0.0
                
                # If this is the first timestamp, store as initial readings (baseline)
                if ts == first_timestamp:
                    initial_readings[tenant] = c
                    # Don't count initial readings as consumption
                    continue
                
                totals[tenant] = totals.get(tenant, 0.0) + c
                monthly.setdefault(ym, {t: 0.0 for t in TENANTS})
                monthly[ym][tenant] += c
                monthly_total[ym] = monthly_total.get(ym, 0.0) + c
                yearly_total[yr] = yearly_total.get(yr, 0.0) + c
                ymap = yearly_per_tenant.get(tenant, {})
                ymap[yr] = ymap.get(yr, 0.0) + c
                yearly_per_tenant[tenant] = ymap
                count_readings += 1
            elif typ == 'RECHARGE':
                try:
                    amt = float(val) if val else 0.0
                except Exception:
                    amt = 0.0
                recharges_total += amt
                if tenant in TENANTS:
                    recharges_per_tenant[tenant] += amt
                count_recharges += 1
    total_usage = sum(totals.values())
    latest_month = sorted(monthly.keys())[-1] if monthly else None
    # Yearly averages (per available months in that year)
    months_per_year = {}
    for ym in monthly_total.keys():
        yr = ym[:4]
        months_per_year[yr] = months_per_year.get(yr, 0) + 1
    yearly_avg_total = {yr: (yearly_total.get(yr, 0.0) / max(1, months_per_year.get(yr, 1))) for yr in yearly_total.keys()}
    yearly_avg_per_tenant = {}
    for t in TENANTS:
        yt = yearly_per_tenant.get(t, {})
        yearly_avg_per_tenant[t] = {yr: (yt.get(yr, 0.0) / max(1, months_per_year.get(yr, 1))) for yr in yt.keys()}
    # Calculate monthly estimates based on last 3 months data
    def calculate_estimates_from_recharges():
        # Get last 3 months (or all if less than 3) of data
        all_months = sorted([ym for ym in monthly_total.keys() if ym in monthly], reverse=True)
        analysis_months = all_months[:3]  # Last 3 months or all if less than 3
        if not analysis_months:
            return {}, 0.0, {}, 0.0, 0.0
        
        # Calculate total recharge amount and consumption in the last 3 months
        total_recharge_period = 0.0
        total_consumption_period = {t: 0.0 for t in TENANTS}
        monthly_recharge_data = {}
        
        for ym in analysis_months:
            monthly_recharge_data[ym] = 0.0
            # Get consumption for this month from the monthly data we already calculated
            if ym in monthly:
                for tenant in TENANTS:
                    total_consumption_period[tenant] += monthly[ym].get(tenant, 0.0)
            
            # Find recharges in this month
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 5:
                        typ, ts, tenant, val, cons = row[0], row[1], row[2], row[3], row[4]
                        if typ == 'RECHARGE' and ts.startswith(ym):
                            try:
                                amt = float(val) if val else 0.0
                                total_recharge_period += amt
                                monthly_recharge_data[ym] += amt
                            except Exception:
                                pass
        
        # Calculate per unit cost based on last 3 months
        total_consumption_all_tenants = sum(total_consumption_period.values())
        per_unit_cost = total_recharge_period / total_consumption_all_tenants if total_consumption_all_tenants > 0 else 0.0
        
        # Calculate average monthly consumption and estimates for each tenant
        months_count = len(analysis_months)
        monthly_estimates = {}
        
        for t in TENANTS:
            # Average monthly consumption for this tenant in last 3 months
            avg_monthly_consumption = total_consumption_period[t] / months_count if months_count > 0 else 0.0
            
            # Monthly estimate = average monthly consumption * per unit cost
            monthly_estimates[t] = avg_monthly_consumption * per_unit_cost
        
        # Calculate average monthly total
        avg_monthly_recharge = total_recharge_period / months_count if months_count > 0 else 0.0
        
        return monthly_estimates, avg_monthly_recharge, monthly_recharge_data, per_unit_cost
    
    monthly_avg_per_tenant, monthly_avg_total, monthly_recharge_data, per_unit_cost = calculate_estimates_from_recharges()
    
    return {
        'total_usage': total_usage,
        'usage_per_tenant': totals,
        'monthly_usage': monthly,
        'monthly_total': monthly_total,
        'latest_month': latest_month,
        'monthly_avg_total': monthly_avg_total,
        'monthly_avg_per_tenant': monthly_avg_per_tenant,
        'yearly_avg_total': yearly_avg_total,
        'yearly_avg_per_tenant': yearly_avg_per_tenant,
        'yearly_total': yearly_total,
        'yearly_per_tenant': yearly_per_tenant,
        'yearly_avg_per_tenant_old': yearly_avg_per_tenant,  # Keep old calculation for charts
        'recharges_total': recharges_total,
        'recharges_per_tenant': recharges_per_tenant,
        'monthly_recharge_data': monthly_recharge_data,
        'per_unit_cost': per_unit_cost,  # Add per unit cost based on last 3 months
        'count_readings': count_readings,
        'count_recharges': count_recharges,
    }


# Index / dashboard
@app.route('/', methods=['GET', 'POST'])
def index():
    # Get CSV path from config
    default_csv = get_current_csv()
    csv_error = validate_csv_file(default_csv)
    
    if request.method == 'POST':
        # If there's a CSV error, don't process the form
        if csv_error:
            flash('Cannot generate PDF: ' + csv_error)
            return redirect(request.url)
        
        input_path = default_csv
        cutoff_str = request.form.get('cutoff_date') or ''
        cutoff_param = cutoff_str.strip() if cutoff_str.strip() else None
        
        if cutoff_param is not None:
            try:
                datetime.strptime(cutoff_param, '%Y-%m-%d')
            except ValueError:
                flash('Cutoff date must be in YYYY-MM-DD format.')
                return redirect(request.url)
        
        output_pdf_name = os.path.splitext(os.path.basename(input_path))[0] + '.pdf'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_pdf_name)
        
        try:
            generate_pdf_from_original_csv(input_path, output_path, cutoff_param)
        except Exception as e:
            app.logger.exception('Failed to generate PDF')
            flash(f'Failed to generate PDF: {e}')
            return redirect(request.url)
        
        return redirect(url_for('result', pdf_name=output_pdf_name))
    
    # Prepare template data
    status_data = None
    next_recharge = None
    metrics = None
    
    # Only load data if CSV is valid
    if not csv_error and default_csv and os.path.exists(default_csv):
        try:
            status_data = CsvCalculator(default_csv).current_status()
            metrics = compute_metrics(default_csv)
            if status_data and status_data.get('balances'):
                balances = status_data['balances']
                def parse_amt(s: str) -> Decimal:
                    try:
                        return Decimal(s.replace('Rs.', '').replace(',', '').strip())
                    except Exception:
                        return Decimal('0')
                least_tenant = min(TENANTS, key=lambda t: parse_amt(balances.get(t, 'Rs.0')))
                next_recharge = least_tenant
        except Exception:
            status_data = None
    
    return render_template('index.html',
                         status_data=status_data,
                         current_csv=default_csv,
                         localmode=session.get('localmode', False),
                         next_recharge=next_recharge,
                         metrics=metrics,
                         csv_error=csv_error)


# Config
@app.route('/config', methods=['GET', 'POST'])
def config_page():
    cfg = load_config()
    if request.method == 'POST':
        # Handle form fields
        pat = request.form.get('git_pat', '').strip()
        default_csv = request.form.get('csv_path', '').strip()
        
        # Handle PAT token
        cfg.setdefault('git', {})
        if pat:
            cfg['git']['pat'] = pat
        
        # Handle regular CSV path selection (skip upload option since it's handled by AJAX)
        if default_csv and default_csv != '__upload__':
            prefs = cfg.get('preferences', {})
            prefs['csv_path'] = default_csv
            cfg['preferences'] = prefs
            set_current_csv(default_csv)
        
        save_config(cfg)
        flash('Configuration saved.')
        return redirect(url_for('config_page'))
    csvs = list_available_csvs()
    return render_template('config.html', cfg=cfg, csvs=csvs, current_csv=get_current_csv(), localmode=session.get('localmode', False))


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """API endpoint for direct CSV file uploads via AJAX"""
    try:
        uploaded_file = request.files.get('csv_file')
        if not uploaded_file or not uploaded_file.filename:
            return jsonify({'success': False, 'message': 'Please select a file to upload.'})
        
        if not allowed_file(uploaded_file.filename):
            return jsonify({'success': False, 'message': 'Only CSV files are allowed for upload.'})
        
        filename = secure_filename(uploaded_file.filename)
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        uploaded_file.save(upload_path)
        
        # Validate the uploaded CSV file
        csv_error = validate_csv_file(upload_path)
        if csv_error:
            # Remove the invalid file
            os.remove(upload_path)
            return jsonify({'success': False, 'message': f'Uploaded file is invalid: {csv_error}'})
        
        # File is valid, set it as current CSV and update config
        set_current_csv(upload_path)
        
        return jsonify({
            'success': True,
            'message': f'File "{filename}" uploaded successfully and set as current CSV.',
            'file_path': upload_path
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to upload file: {str(e)}'})


# Sync utilities
def run_git(cmd: str) -> Tuple[int, str, str]:
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd(), text=True)
    out, err = p.communicate(timeout=20)
    return p.returncode, out.strip(), err.strip()


def git_remote_status(do_fetch: bool = False):
    code, url, _ = run_git('git remote get-url origin')
    if code != 0:
        return {'has_repo': False}
    if do_fetch:
        # Run fetch synchronously when explicitly requested by API
        run_git('git fetch --prune')
    _, branch, _ = run_git('git rev-parse --abbrev-ref HEAD')
    _, status, _ = run_git('git status -sb')
    ahead = behind = 0
    m = re.search(r'\[ahead (\d+)\]', status)
    if m:
        ahead = int(m.group(1))
    m = re.search(r'\[behind (\d+)\]', status)
    if m:
        behind = int(m.group(1))
    return {'has_repo': True, 'remote_url': url, 'branch': branch, 'ahead': ahead, 'behind': behind}


@app.route('/api/sync/status')
def api_sync_status():
    refresh = request.args.get('refresh') == '1'
    # If refresh requested, run fetch in background thread and immediately return current status
    if refresh:
        def _bg_fetch():
            try:
                git_remote_status(do_fetch=True)
            except Exception:
                pass
        threading.Thread(target=_bg_fetch, daemon=True).start()
    st = git_remote_status(do_fetch=False)
    cfg = load_config()
    git_pat = cfg.get('git', {}).get('pat')
    is_https = st.get('remote_url','').startswith('https://') if st.get('has_repo') else False
    missing_pat = is_https and not git_pat
    return jsonify({'status': st, 'is_https': is_https, 'missing_pat': missing_pat})


@app.route('/sync', methods=['GET', 'POST'])
def sync():
    if session.get('localmode', False):
        flash('Sync is disabled in local mode.')
        return redirect(url_for('index'))
    action = request.form.get('action')
    status = git_remote_status()
    cfg = load_config()
    git_pat = cfg.get('git', {}).get('pat', '')
    if request.method == 'POST':
        if not status.get('has_repo'):
            flash('No git repository detected.')
            return redirect(url_for('sync'))
        remote = status['remote_url']
        branch = status['branch']
        if remote.startswith('https://') and not git_pat:
            flash('HTTPS remote detected. Add a PAT token in Config to pull/push.')
            return redirect(url_for('config_page'))
        auth_remote = re.sub(r'^https://', f"https://x-access-token:{git_pat}@", remote) if (remote.startswith('https://') and git_pat) else remote
        if action == 'pull':
            run_git('git fetch --prune')
            code, out, err = run_git(f'git pull {shlex.quote(auth_remote)} {shlex.quote(branch)}')
            status = determine_git_command_status(code, out, err, 'pull')
            flash_with_status(err or out or 'Pulled', status)
            return redirect(url_for('sync'))
        if action == 'push':
            code, out, err = run_git(f'git push {shlex.quote(auth_remote)} {shlex.quote(branch)}')
            status = determine_git_command_status(code, out, err, 'push')
            flash_with_status(err or out or 'Pushed', status)
            return redirect(url_for('sync'))
        if action in ('commit', 'commit_and_push'):
            msg = request.form.get('commit_msg') or f'Update {datetime.now().isoformat(timespec="seconds")}'
            run_git('git add -A')
            code, out, err = run_git(f'git commit -m {shlex.quote(msg)}')
            status = determine_git_command_status(code, out, err, 'commit')
            flash_with_status(err or out or 'Committed', status)
            if action == 'commit_and_push':
                if remote.startswith('https://') and not git_pat:
                    flash_with_status('Cannot push: PAT token missing. Configure it in Config.', 'error')
                    return redirect(url_for('config_page'))
                code, out, err = run_git(f'git push {shlex.quote(auth_remote)} {shlex.quote(branch)}')
                push_status = determine_git_command_status(code, out, err, 'push')
                flash_with_status((err or out or '') + ' Pushed', push_status)
            return redirect(url_for('sync'))
        if action == 'remove_remote':
            if status['behind'] > 0:
                flash('Remote has changes; pull first or force remove via CLI.')
                return redirect(url_for('sync'))
            run_git('git remote remove origin')
            flash('Removed remote origin.')
            return redirect(url_for('sync'))
    status = git_remote_status()
    default_commit_ts = datetime.now().isoformat(timespec='seconds')
    is_https = status.get('remote_url','').startswith('https://') if status.get('has_repo') else False
    missing_pat = is_https and not load_config().get('git', {}).get('pat')
    return render_template('sync.html', status=status, is_https=is_https, missing_pat=missing_pat, localmode=session.get('localmode', False), default_commit_ts=default_commit_ts)


@app.route('/toggle_localmode', methods=['POST'])
def toggle_localmode():
    session['localmode'] = not session.get('localmode', False)
    return jsonify({'localmode': session['localmode']})


@app.route('/result')
def result():
    pdf_name = request.args.get('pdf_name')
    if not pdf_name:
        return redirect(url_for('index'))
    return render_template('result.html', pdf_name=pdf_name)


@app.route('/download/<path:pdf_name>')
def download(pdf_name: str):
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], pdf_name)
    if not os.path.exists(output_path):
        flash('Requested file not found.')
        return redirect(url_for('index'))
    return send_file(output_path, as_attachment=True)


@app.route('/record', methods=['GET', 'POST'])
def record():
    csvs = list_available_csvs()
    target_path = request.form.get('target_csv') or get_current_csv()
    if request.method == 'POST':
        if target_path == 'new':
            new_name = secure_filename(request.form.get('new_csv_name') or '').strip()
            if not new_name:
                flash('Please provide a name for the new CSV.')
                return redirect(request.url)
            if not new_name.lower().endswith('.csv'):
                new_name += '.csv'
            target_path = os.path.join(UPLOAD_FOLDER, new_name)
        try:
            readings = {
                'Ground Floor': float(request.form.get('gf_reading') or '0') ,
                'First Floor': float(request.form.get('ff_reading') or '0') ,
                'Second Floor': float(request.form.get('sf_reading') or '0') ,
            }
        except ValueError:
            flash('Readings must be numbers for all three tenants.')
            return redirect(request.url)
        recharge_tenant = request.form.get('recharge_tenant') or ''
        recharge_amount_str = request.form.get('recharge_amount') or ''
        recharge_amount = 0.0
        if recharge_amount_str.strip():
            try:
                recharge_amount = float(recharge_amount_str)
            except ValueError:
                flash('Recharge amount must be a number.')
                return redirect(request.url)
        try:
            calc = CsvCalculator(target_path)
            calc.record_readings_and_recharge(readings, recharge_tenant, recharge_amount)
            set_current_csv(target_path)
        except Exception as e:
            flash(str(e))
            return redirect(request.url)
        if request.form.get('generate_now') == 'on':
            output_pdf_name = os.path.splitext(os.path.basename(target_path))[0] + '.pdf'
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_pdf_name)
            try:
                generate_pdf_from_original_csv(target_path, output_path, None)
                return redirect(url_for('result', pdf_name=output_pdf_name))
            except Exception as e:
                flash(f'PDF generation failed: {e}')
                return redirect(url_for('status', csv_path=target_path))
        return redirect(url_for('status', csv_path=target_path))
    return render_template('record.html', csvs=csvs, current_csv=get_current_csv(), localmode=session.get('localmode', False))


@app.route('/status')
def status():
    csv_path = request.args.get('csv_path') or get_current_csv()
    calc = CsvCalculator(csv_path)
    data = calc.current_status()
    return render_template('status.html', csv_path=csv_path, data=data, localmode=session.get('localmode', False))


@app.route('/revert', methods=['GET', 'POST'])
def revert():
    csvs = list_available_csvs()
    csv_path = request.values.get('csv_path') or get_current_csv()
    calc = CsvCalculator(csv_path)
    ts, preview = calc.preview_last_group_for_revert()
    if request.method == 'POST':
        if not preview:
            flash('Nothing to revert.')
            return redirect(url_for('revert', csv_path=csv_path))
        removed = calc.revert_last_group()
        flash(f'Reverted {removed} rows from {os.path.basename(csv_path)}')
        return redirect(url_for('status', csv_path=csv_path))
    return render_template('revert.html', csvs=csvs, csv_path=csv_path, preview=preview, ts=ts, localmode=session.get('localmode', False))


@app.route('/browse')
def browse():
    csvs = list_available_csvs()
    csv_path = request.args.get('csv_path') or get_current_csv()
    set_current_csv(csv_path)
    ensure_csv_with_header(csv_path)
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None) or CSV_HEADERS
        all_rows = list(reader)
    q = (request.args.get('q') or '').strip().lower()
    type_filter = (request.args.get('type') or 'all').upper()
    sort_by = (request.args.get('sort_by') or 'Timestamp').strip()
    sort_order = (request.args.get('sort_order') or 'desc').lower()
    def match(row):
        if q and not any(q in (col or '').lower() for col in row):
            return False
        if type_filter in {'READING','RECHARGE'} and row[0].upper() != type_filter:
            return False
        return True
    all_rows = [row for row in all_rows if match(row)]
    # sorting
    def key_ts(val: str):
        try:
            return datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return datetime.min
    def key_num(val: str):
        try:
            return float(val)
        except Exception:
            return float('-inf')
    def sort_key(row):
        if sort_by.lower() == 'timestamp':
            return key_ts(row[1])
        if sort_by.lower() == 'type':
            return row[0]
        if sort_by.lower() == 'tenant':
            return row[2]
        if sort_by.lower() in ('reading','reading/amount','readingamount'):
            return key_num(row[3])
        if sort_by.lower() == 'consumption':
            return key_num(row[4])
        return key_ts(row[1])
    all_rows.sort(key=sort_key, reverse=(sort_order == 'desc'))
    try:
        page = max(1, int(request.args.get('page', '1')))
    except ValueError:
        page = 1
    try:
        page_size = max(1, min(200, int(request.args.get('page_size', '25'))))
    except ValueError:
        page_size = 25
    total = len(all_rows)
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    end = start + page_size
    rows = all_rows[start:end]
    enriched_rows: List[Dict] = []
    for r in rows:
        balances_map = {t: '' for t in TENANTS}
        if len(r) >= 6 and r[5].strip():
            try:
                parts = [p.strip() for p in r[5].split(';') if p.strip()]
                for p in parts:
                    if ': Rs.' in p:
                        tenant, amt = p.split(': Rs.', 1)
                        balances_map[tenant.strip()] = f"Rs.{amt.strip()}"
            except Exception:
                pass
        enriched_rows.append({
            'Type': r[0], 'Timestamp': r[1], 'Tenant': r[2], 'ReadingAmount': r[3], 'Consumption': r[4],
            'Ground': balances_map['Ground Floor'], 'First': balances_map['First Floor'], 'Second': balances_map['Second Floor']
        })
    return render_template('browse.html', csvs=csvs, csv_path=csv_path, rows=enriched_rows, page=page, page_size=page_size, total=total, total_pages=total_pages, q=q, type_filter=type_filter, sort_by=sort_by, sort_order=sort_order, localmode=session.get('localmode', False))


# For Vercel deployment, we need to modify file operations to use /tmp
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
    app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
    UPLOAD_FOLDER = '/tmp/uploads'
    OUTPUT_FOLDER = '/tmp/outputs'
    
    # Ensure tmp directories exist
    os.makedirs('/tmp/uploads', exist_ok=True)
    os.makedirs('/tmp/outputs', exist_ok=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
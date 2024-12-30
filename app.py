from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from functools import wraps
from binance.client import Client
import time
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key in production

# Demo user credentials
DEMO_USER = {
    'email': '',
    'password': ''
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('terminal'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    recaptcha_response = request.form.get('g-recaptcha-response')
    
    # Verify reCAPTCHA
    verify_url = 'https://www.google.com/recaptcha/api/siteverify'
    verify_data = {
        'secret': '',
        'response': recaptcha_response
    }
    
    try:
        response = requests.post(verify_url, data=verify_data)
        result = response.json()
        
        if not result.get('success', False):
            return render_template('index.html', error='Please complete the reCAPTCHA')
            
        if email == DEMO_USER['email'] and password == DEMO_USER['password']:
            session['user'] = email
            return redirect(url_for('terminal'))
        
        return render_template('index.html', error='Invalid credentials')
        
    except Exception as e:
        print(f"reCAPTCHA verification error: {str(e)}")
        return render_template('index.html', error='An error occurred. Please try again.')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/terminal')
@login_required
def terminal():
    return render_template('terminal.html')

# Initialize Binance.US client with API keys
try:
    client = Client(
        '',
        '',
        tld='us'  # Use Binance.US API
    )
except Exception as e:
    print(f"Warning: Could not initialize Binance client: {str(e)}")
    client = None

def get_timeframe_params(interval='1h'):
    """Convert interval to Binance kline interval and calculate limit"""
    mappings = {
        '1d': (Client.KLINE_INTERVAL_1HOUR, 24),
        '5d': (Client.KLINE_INTERVAL_1HOUR, 24 * 5),
        '1m': (Client.KLINE_INTERVAL_4HOUR, 30),
        '3m': (Client.KLINE_INTERVAL_4HOUR, 90),
        '6m': (Client.KLINE_INTERVAL_1DAY, 180),
        '1y': (Client.KLINE_INTERVAL_1DAY, 365),
        '5y': (Client.KLINE_INTERVAL_1WEEK, 260)
    }
    return mappings.get(interval, (Client.KLINE_INTERVAL_1HOUR, 100))

@app.route('/get_klines')
def get_klines():
    try:
        if client is None:
            # Return sample data if Binance client is not available
            return jsonify([{
                'time': int(time.time()),
                'open': 50000,
                'high': 51000,
                'low': 49000,
                'close': 50500
            }])

        # Get interval from query params or default to 1h
        interval = request.args.get('interval', '1h')
        
        # Map intervals to Binance format and lookback periods
        interval_mappings = {
            '1h': (Client.KLINE_INTERVAL_1HOUR, 30),      # 30 days
            '4h': (Client.KLINE_INTERVAL_4HOUR, 60),      # 60 days
            '1d': (Client.KLINE_INTERVAL_1DAY, 180),      # 180 days
            '1w': (Client.KLINE_INTERVAL_1WEEK, 365),     # 365 days
        }
        
        binance_interval, days_back = interval_mappings.get(interval, (Client.KLINE_INTERVAL_1HOUR, 30))
        start_time = int((time.time() - (days_back * 24 * 60 * 60)) * 1000)
        
        try:
            # Get available symbols
            exchange_info = client.get_exchange_info()
            symbols = [s['symbol'] for s in exchange_info['symbols']]
            print(f"Available BTC pairs: {[s for s in symbols if s.startswith('BTC')]}")

            # Get candlestick data from Binance
            print(f"Fetching klines for BTCUSDT with interval {binance_interval}")
            klines = client.get_klines(
                symbol='BTCUSDT',  # Using BTCUSDT as it's the standard pair
                interval=binance_interval,
                startTime=start_time,
                limit=1000
            )
            print(f"Received {len(klines)} klines")
            
            # Format data for TradingView chart
            formatted_data = []
            for k in klines:
                # Convert timestamp to seconds and ensure it's an integer
                timestamp = int(k[0] / 1000)  # Binance timestamps are in milliseconds
                formatted_data.append({
                    'time': timestamp,
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4])
                })
            
            # Sort by timestamp to ensure proper order
            formatted_data.sort(key=lambda x: x['time'])
            
            # Log the latest data point
            if formatted_data:
                print(f"Latest data point: {formatted_data[-1]}")
            
            return jsonify(formatted_data)
        except Exception as e:
            print(f"Error fetching klines: {str(e)}")
            # Return sample data on error
            return jsonify([{
                'time': int(time.time()),
                'open': 50000,
                'high': 51000,
                'low': 49000,
                'close': 50500
            }])
    except Exception as e:
        print(f"Error in get_klines: {str(e)}")
        # Return sample data on error
        return jsonify([{
            'time': int(time.time()),
            'open': 50000,
            'high': 51000,
            'low': 49000,
            'close': 50500
        }])

if __name__ == '__main__':
    app.run(debug=True)

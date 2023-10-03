from pymongo import MongoClient
# from api.config import MONGO_URI, DB_NAME, COLLECTION_NAME  # Import MONGO_URI from config.py
from flask_cors import CORS
import json
import pandas as pd
from bson import json_util
from flask import Flask,request, jsonify
from werkzeug.urls import url_quote

app = Flask(__name__)

# Initialize and configure CORS
cors = CORS(app, resources={
    r"*": {"origins": ["http://localhost:5173", "https://oneassureassignment.netlify.app"]}
})

mongo_client = MongoClient("mongodb+srv://chaithanya:chaithanya%401M@cluster0.v7ivcmn.mongodb.net/?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE")
db = mongo_client['oneassure']
collection = db['insurancedata']

@app.route('/', methods=['GET'])
def hello_world():
    return "Hello, World"


@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        # Get the uploaded CSV file from the request
        file = request.files['file']

        if not file:
            return jsonify({'error': 'No file provided'}), 400

        # Load the CSV data into a DataFrame
        data = pd.read_csv(file)

        # Convert the DataFrame to a list of dictionaries for MongoDB insertion
        data_dict = data.to_dict(orient='records')

        # Insert the data into the MongoDB collection
        collection.insert_many(data_dict)

        return jsonify({'message': 'Data uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/check-db-connection', methods=['GET'])
def check_db_connection():
    try:
        # Check if the MongoDB client is connected
        is_connected = False
        if mongo_client.server_info():
            is_connected = True

        return jsonify({'message': 'Database connection status', 'connected': is_connected}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch-premium', methods=['GET'])
def fetch_premium():
    try:
        # Parse and sort adult ages
        adult_ages = sorted(map(int, request.args.get('adult_ages', '').split(',')), reverse=True)
        
        # Parse and sort child ages
        child_ages = sorted(map(int, request.args.get('child_ages', '').split(',')), reverse=True)
        
        tier = request.args.get('tier')
        combination = request.args.get('premium_comb')
        cover = request.args.get('cover')
        
        baseRates = []
        floaterDiscount = []
        discountRate = []
        total_premium = []
        finalData = []

        # Process adult ages
        for age in adult_ages:
            adultdata = {}
            # Find matching records in the database
            filtered_records = collection.find({
                "tier": tier,
                "member_csv": combination,
                "age_range": {"$regex": r"\b{}\b".format(age)}
            })
            
            if filtered_records.count() > 0:
                record = filtered_records[0]
                base_rate = record.get(cover, 0)
                adultdata['base_rate'] = base_rate
                
                # Calculate floater discount
                floater_discount = 50 if baseRates else 0
                adultdata['floater_discount'] = floater_discount
                
                # Calculate discount rate
                discount_price = (base_rate * floater_discount) / 100
                adultdata['discount_rate'] = discount_price
                
                baseRates.append(base_rate)
                floaterDiscount.append(floater_discount)
                discountRate.append(discount_price)
                total_premium.append(discount_price)
                
                finalData.append(adultdata)

        # Process child ages
        for age in child_ages:
            record = collection.find_one({
                "tier": tier,
                "member_csv": combination,
                "age_range": {"$regex": r"\b{}\b".format(age)}
            })

            if record:
                baseRates.append(record.get(cover, 0))
                discount_price = record.get(cover, 0)
                discountRate.append(discount_price)
                total_premium.append(discount_price)
                floaterDiscount.append(50)

        # Close the database connection
        mongo_client.close()

        return jsonify({
            'baseRates': baseRates,
            'floaterDiscount': floaterDiscount,
            'discountRate': discountRate,
            'total': sum(total_premium),
            'status': 'SUCCESS'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

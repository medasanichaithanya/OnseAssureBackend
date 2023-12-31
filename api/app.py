from pymongo import MongoClient
# from api.config import MONGO_URI, DB_NAME, COLLECTION_NAME  # Import MONGO_URI from config.py
from flask_cors import CORS
import json
import pandas as pd
from bson import json_util
from flask import Flask,request, jsonify
from werkzeug.urls import url_quote
import certifi
ca = certifi.where()
app = Flask(__name__)

# Initialize and configure CORS
cors = CORS(app, resources={
    r"*": {"origins": ["http://localhost:5173", "https://oneassureassignment.netlify.app"]}
})

mongo_client = MongoClient("mongodb+srv://chaithanya:chaithanya%401M@cluster0.v7ivcmn.mongodb.net/?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE",tlsCAFile=ca)
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
        adult_ages = sorted(map(int, request.args.get('adult_ages', '').split(',')), reverse=True)
        child_ages = sorted(map(int, request.args.get('child_ages', '').split(',')), reverse=True)
        tier = request.args.get('tier')
        combination = request.args.get('premium_comb')
        cover = request.args.get('cover')

        baseRates = []
        floaterDiscount = []
        finalData = []
        discountRate = []
        total_premium = []
        count = 0

        for ages in adult_ages:
            count +=1
            adultdata = {}
            filtered_data = collection.find({"tier": tier, "member_csv": combination})
            filtered_records = [record for record in filtered_data if 'age_range' in record and '-' in record['age_range'] and ages in range(int(record['age_range'].split('-')[0]), int(record['age_range'].split('-')[1]) + 1)]
            adultsdata = json.loads(json_util.dumps(filtered_records))
            adultdata['base_rate'] = adultsdata[0][cover]
            baseRates.append(adultsdata[0][cover])
            if count > 1:
                adultdata['floater_discount'] = 50
                floaterDiscount.append(50)
                discount_price = (adultsdata[0][cover]*50)/100
                adultdata['discount_rate'] = discount_price
                discountRate.append(discount_price)
                total_premium.append(discount_price)

            else:
                adultdata['floater_discount'] = 0
                floaterDiscount.append(0)
                discount_price = adultsdata[0][cover]
                adultdata['discount_rate'] = discount_price
                discountRate.append(discount_price)
                total_premium.append(discount_price) 

            finalData.append(adultdata)

        for i in child_ages:
            filtered_data = collection.find_one({"tier": tier, "member_csv": "1a","age_range":i})
            baseRates.append(filtered_data[cover])
            discount_price = (filtered_data[cover]*50)/100
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

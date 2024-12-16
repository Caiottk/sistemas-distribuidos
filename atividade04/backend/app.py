from principal import *

app = Flask(__name__)
CORS(app)  # This will allow all origins to access your API
    
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(Principal.products)

@app.route('/place_order', methods=['POST'])
def place_order():
    try:
        # Get the JSON data from the request
        order_data = request.get_json()

        # For demonstration, let's print the order data
        print(f"Order received: {order_data}")

        # Process the order here (e.g., save it to a database, send a message to a queue)
        # For simplicity, we just respond with a success message

        return jsonify({
            'status': 'success',
            'message': 'Order placed successfully',
            'order': order_data
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
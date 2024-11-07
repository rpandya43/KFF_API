from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import string
from datetime import datetime, timezone
from models import db,RegisteredUsers,User,Vendor,Transaction,RegisteredSevakas
from flask_migrate import Migrate
import json


# Initialize Flask App
app = Flask(__name__)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.lnimabjrgjtznupmdvzv:ajDzs1eqzrkFgRWg@aws-0-ap-south-1.pooler.supabase.com:6543/postgres'

db.init_app(app)

migrate = Migrate(app, db)

# Create the database and table
with app.app_context():
    db.create_all()

#Route 1: Fetch users by phone number
@app.route('/fetch_user', methods=['GET'])
def fetch_user():
    # Get the search parameter from the query string
    data = request.json
    search = data.get('search')

    if not search:
        return jsonify({'error': 'No search parameter provided.'}), 400

    # Query the database for users matching the search parameter
    users = User.query.filter(
        (User.phone_number == search) |
        (User.email == search)
    ).all()

    if not users:
        return jsonify({'message': 'No users found.'}), 404

    # Serialize user data
    user_data = [
        {
            'id': user.customer_id,
            'full_name': user.name,
            'email': user.email,
            'phone_number': user.phone_number,
            # Add other fields as necessary
        }
        for user in users
    ]

    return jsonify(user_data), 200

# Route 2: Assign NFC card
@app.route('/assign_nfc', methods=['POST'])
def nfc_update():
    data = request.json
    cid = data.get('cid')

    if not cid or 'nfc_id' not in data:
        return jsonify({'message': 'CID and NFC card details are required'}), 400

    # Find the user by CID
    user = User.query.get(cid)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update the NFC card field
    user.nfc_id = data['nfc_id']
    db.session.commit()

    return jsonify({'message': 'QR card updated successfully'}), 200

# Route 3: Create a new user
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.json

    # Validate input data
    if 'customer_id' not in data or 'name' not in data or 'phone_number' not in data:
        return jsonify({'message': 'ID, Name, and Phone number are required'}), 400

    # Create a new user instance

    new_user = User(
        customer_id=data['customer_id'],
        name=data['name'],
        email=data['email'],
        phone_number=data['phone_number'],
        nfc_id=data.get('nfc_id', None),  # Optional, default to None if not provided
        balance=data.get('balance', 5),  # Default balance to 5 if not provided
        last_transaction=data.get('last_transaction', None),  # Optional
        time_in=data.get('time_in', None),  # Optional
        time_out=data.get('time_out', None),  # Optional
        customer_class=data['customer_class'],
        status=data['status']
    )

    # Add the new user to the session and commit
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully', 'user': new_user.serialize()}), 201

# Route 4: Process POS Transaction
@app.route('/process_transaction', methods=['POST'])
def process_transaction():
    data = request.json
    vid = data.get('vendor_id')
    nfc_id = data.get('nfc_id')
    amount = data.get('amount')

    # Generate a unique 8-digit alphanumeric Transaction ID
    transaction_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    # Find the user by NFC ID
    user = User.query.filter_by(nfc_id=nfc_id).first()

    if not user:
        return jsonify({"error": "User not found."}), 404

    #print(f"User status before transaction: {user.status}")

    if user.status == "3":
        return jsonify({'message': 'User already signed out. No transaction can be made'}), 200

    current_balance = user.balance
    cid = user.customer_id

    # Check if the user has sufficient balance
    if current_balance >= amount:
        # Deduct amount from user balance
        user.balance -= amount
        user.last_transaction = datetime.now(timezone.utc)
        user.status = '1'
        db.session.commit()  # Commit the user changes

        # Update Transaction Table
        transaction = Transaction(
            transaction_id=transaction_id,
            nfc_id=nfc_id,
            name=user.name,
            vendor_id=vid,
            transaction_amount=amount,
            status="successful",
            date_time=datetime.now(timezone.utc),
            type_of_transaction="POS",
            customer_id=cid
        )
        db.session.add(transaction)

        # Update Vendor Balance
        vendor = Vendor.query.get(vid)
        if vendor:
            vendor.vendor_balance += amount
            vendor.vendor_last_transaction = datetime.now(timezone.utc)
            db.session.commit()  # Commit vendor changes

        db.session.commit()  # Commit transaction

        return jsonify({
            "transaction_id": transaction_id,
            "status": "Transaction successful",
            "new_balance": user.balance
        }), 200
    else:
        # Insufficient balance case
        transaction = Transaction(
            transaction_id=transaction_id,
            nfc_id=nfc_id,
            name=user.name,
            vendor_id=vid,
            transaction_amount=amount,
            status="failed",
            date_time=datetime.now(timezone.utc),
            type_of_transaction="POS",
            customer_id=cid
        )
        db.session.add(transaction)

        db.session.commit()  # Commit transaction

        return jsonify({
            "error": "Insufficient balance",
            "current_balance": current_balance
        }), 400

# Route 5: Add Vendor to DB
@app.route('/add_vendor', methods=['POST'])
def add_vendor():
    data = request.json
    vid = data.get('vendor_id')
    vendor_name = data.get('vendor_name')
    vendor_phone_number = data.get('vendor_phone_number')

    # Create a new Vendor instance
    new_vendor = Vendor(
        vendor_id=vid,
        vendor_name=vendor_name,
        vendor_phone_number=vendor_phone_number,
        vendor_balance=0,  # Initialize balance to 0 or set as needed
        vendor_last_transaction=datetime.now(timezone.utc)  # Set initial last transaction time
    )

    # Add the new vendor to the session and commit
    db.session.add(new_vendor)
    db.session.commit()

    return jsonify({
        "message": "Vendor added successfully",
        "vendor_id": vid,
        "vendor_name": vendor_name,
        "vendor_phone_number": vendor_phone_number
    }), 201

# Route 6: Get a users Balance based on User ID
@app.route('/get_user_balance/<int:user_customer_id>', methods=['GET'])
def get_user_balance(user_customer_id):
    user = User.query.get(user_customer_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id": user.customer_id,
        "full_name": user.name,
        "current_balance": user.balance
    }), 200

# Route 7: Get a vendor Balance amount
@app.route('/get_vendor_balance/<int:vendor_id>', methods=['GET'])
def get_vendor_balance(vendor_id):
    vendor = Vendor.query.get(vendor_id)

    if vendor is None:
        return jsonify({"error": "Vendor not found"}), 404

    return jsonify({
        "vendor_id": vendor.vendor_id,
        "vendor_name": vendor.vendor_name,
        "vendor_balance": vendor.vendor_balance
    }), 200

# Route 8: Process Top-up Transaction
@app.route('/topup', methods=['POST'])
def top_up_account():
    data = request.get_json()

    nfc_id = data.get('nfc_id')
    topup_source = data.get('topup_source')
    amount = data.get('amount')

    if not nfc_id or not amount or not topup_source:
        return jsonify({"error": "Missing required data"}), 400

    # Find the user by NFC ID
    user = User.query.filter_by(nfc_id=nfc_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.status == "3":
        return jsonify({'message': 'User already signed out. No changes can be made.'}), 200

    # Update user credits
    user.balance += amount
    user.last_transaction = datetime.now(timezone.utc)  # Set last transaction to now

    # Generate a 7-digit alphanumeric Transaction ID
    transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

    # Insert a new transaction entry
    new_transaction = Transaction(
        transaction_id=transaction_id,
        nfc_id=nfc_id,
        name=user.name,
        vendor_id=9999,  # Hard set to 'KFF' as specified
        transaction_amount=f"+{amount}",
        status="successful",
        date_time=datetime.now(timezone.utc),
        type_of_transaction="top up",
        customer_id=user.customer_id
    )
    db.session.add(new_transaction)

    # Commit the transaction and update the user balance
    db.session.commit()

    # Return success with customer details and new balance
    return jsonify({
        "message": "Top up successful",
        "transaction_id": transaction_id,
        "user": {
            "name": user.name,
            "nfc_id": nfc_id,
            "new_balance": user.balance
        }
    }), 200

# Route 9.a: Fetch Atendee
@app.route('/fetch_user_registered', methods=['GET'])
def fetch_user_registered():
    # Get the search parameter from the request JSON
    data = request.json
    search = data.get('search')

    if not search:
        return jsonify({'error': 'No search parameter provided.'}), 400

    # Query the database for users matching either phone_number or email in the RegisteredUsers table
    users = RegisteredUsers.query.filter(
        (RegisteredUsers.phone == search) |
        (RegisteredUsers.code == search) |
        (RegisteredUsers.email == search)
    ).all()

    if not users:
        return jsonify({'message': 'No users found.'}), 404

    # Serialize user data to include `customer_id` as `rid`
    user_data = [
        {
            'rid': RegisteredUsers.rid,  # Assuming customer_id is rid
            'slot': RegisteredUsers.slot,
            'full_name': RegisteredUsers.name,   # Full Name of the user
            'email': RegisteredUsers.email,      # Email of the user
            'phone_number': RegisteredUsers.phone  # Phone number
            # Add any other fields you want to return
        }
        for RegisteredUsers in users
    ]

    return jsonify(user_data), 200

# Route 9.b: Fetch Sevaka
@app.route('/fetch_sevaka_registered', methods=['GET'])
def fetch_sevaka_registered():
    # Get the search parameter from the request JSON
    data = request.json
    search = data.get('search')

    if not search:
        return jsonify({'error': 'No search parameter provided.'}), 400

    # Query the database for users matching either phone_number or email in the RegisteredUsers table
    users = RegisteredSevakas.query.filter(
        (RegisteredSevakas.phone == search) |
        (RegisteredSevakas.email == search)
    ).all()

    if not users:
        return jsonify({'message': 'No Sevaka found.'}), 404

    # Serialize user data to include `customer_id` as `rid`
    user_data = [
        {
            'sid': RegisteredSevakas.rid,  # Assuming customer_id is rid
            'slot': RegisteredSevakas.slot,
            'full_name': RegisteredSevakas.name,   # Full Name of the user
            'email': RegisteredSevakas.email,      # Email of the user
            'phone_number': RegisteredSevakas.phone  # Phone number
            # Add any other fields you want to return
        }
        for RegisteredSevakas in users
    ]

    return jsonify(user_data), 200

# Route 10: Register user
@app.route('/sign_in', methods=['POST'])
def create_user_from_rid():
    data = request.json
    rid = data.get('rid')
    slot = data.get('slot')

    # Check if RID is provided
    if not rid:
        return jsonify({"error": "RID is required."}), 400

    # Find the registered user by RID
    registered_user = RegisteredUsers.query.filter_by(rid=rid).first()
    if not registered_user:
        return jsonify({"error": "No registered user found with the provided RID."}), 404
  
    # Check if the provided current_slot is in the list of available slots
    if str(slot) not in str(registered_user.slot):
        return jsonify({
            "error": f"User is not registered for the current slot: {slot}. Available slots: {registered_user.slot}"
        }), 400

    # Check the status of the registered user
    if registered_user.log == '1':
        # User is already registered, find the corresponding user in the User table
        existing_user = User.query.filter_by(name=registered_user.name).first()
        if existing_user:
            return jsonify({
                "message": f"User already checked in with user ID: {existing_user.customer_id}"
            }), 200
        else:
            return jsonify({
                "error": "User status is 1 but no user found in the User table."
            }), 404

    # Only proceed if status is 0 (user is not yet registered)
    if registered_user.log == '0' :
        # Generate a new user ID (auto-generated by the DB)
        new_user = User(
            slot_id=slot,
            customer_class='customer',
            name=registered_user.name,
            email=registered_user.email,
            phone_number=registered_user.phone,
            balance=registered_user.top_up_balance,
            time_in=datetime.now(timezone.utc),  # Set Time In to now
            status='0'
        )

        # Add the new user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        # Update the registration status in RegisteredUsers table
        registered_user.log = '1'
        db.session.commit()

        return jsonify({
            "message": "User registered successfully.",
            "user_id": new_user.customer_id
        }), 201
    else:
        # Handle any unexpected case where the status is neither 0 nor 1
        return jsonify({"error": "Invalid registration status."}), 400

# Route 11: Registerd Sevaka
@app.route('/sign_in_sevaka', methods=['POST'])
def create_user_from_sid():
    data = request.json
    sid = data.get('sid')
    slot = data.get('slot')

    # Check if RID is provided
    if not sid:
        return jsonify({"error": "SID is required."}), 400

    # Find the registered user by RID
    registered_sevaka = RegisteredSevakas.query.filter_by(sid=sid).first()
    if not registered_sevaka:
        return jsonify({"error": "No registered user found with the provided SID."}), 404
  
    # Check if the provided current_slot is in the list of available slots
    if str(slot) not in str(registered_sevaka.service_slot):
        return jsonify({
            "error": f"User is not registered for the current slot: {slot}. Available slots: {registered_sevaka.slot}"
        }), 400

    # Check the status of the registered user
    if registered_sevaka.log == '1':
        # User is already registered, find the corresponding user in the User table
        existing_user = User.query.filter_by(name=registered_sevaka.name).first()
        if existing_user:
            return jsonify({
                "message": f"User already checked in with user ID: {existing_user.customer_id}"
            }), 200
        else:
            return jsonify({
                "error": "User status is 1 but no user found in the User table."
            }), 404

    # Only proceed if status is 0 (user is not yet registered)
    if registered_sevaka.log == '0' :
        # Generate a new user ID (auto-generated by the DB)
        new_user = User(
            slot_id=slot,
            customer_class='sevaka',
            name=registered_sevaka.name,
            email=registered_sevaka.email,
            phone_number=registered_sevaka.phone,
            balance="100",
            time_in=datetime.now(timezone.utc),  # Set Time In to now
            status='0'
        )

        # Add the new user to the session and commit
        db.session.add(new_user)
        db.session.commit()

        # Update the registration status in RegisteredUsers table
        registered_sevaka.log = '1'
        db.session.commit()

        return jsonify({
            "message": "User registered successfully.",
            "user_id": new_user.customer_id
        }), 201
    else:
        # Handle any unexpected case where the status is neither 0 nor 1
        return jsonify({"error": "Invalid registration status."}), 400

# Route 12: add user to preregistered list
@app.route('/create_registered_user', methods=['POST'])
def pre_register_user():
    data = request.json
    rid = data.get('rid')
    slot = data.get('slot')
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    topup_amount = data.get('topup_amount')
    status = data.get('status')

    # Validate input
    if not all([rid, slot, name, email, phone_number, topup_amount is not None]):
        return jsonify({"error": "All fields must be provided."}), 400

    # Create a new RegisteredUsers instance
    new_registered_user = RegisteredUsers(
        rid=rid,
        slot=slot,
        name=name,
        email=email,
        phone=phone_number,
        top_up_balance=topup_amount,
        status=status
    )

    # Add the new registered user to the session and commit
    db.session.add(new_registered_user)
    db.session.commit()

    return jsonify({
        "message": "User pre-registered successfully",
        "rid": rid,
        "name": name,
        "email": email,
        "phone": phone_number,
        "top_up_balance": topup_amount
    }), 201

# Route 13: Sign out user
@app.route('/sign_out', methods=['POST'])
def close_user():
    try:
        # Get the NFC ID from the request body
        data = request.json
        nfc_id = data.get('nfc_id')

        if not nfc_id:
            return jsonify({'error': 'No NFC ID provided.'}), 400

        # Query the database for the user with the given NFC ID
        user = User.query.filter_by(nfc_id=nfc_id).first()

        if not user:
            return jsonify({'error': 'User not found.'}), 404

        # Update the user's status to 3 and set time_out to current time
        user.status = 3
        user.time_out = datetime.now(timezone.utc)  # Use .now() if you want local time,  for UTC

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'User signed out from Venue'}), 200

    except Exception as e:
        # Handle any exceptions and return a 500 Internal Server Error
        return jsonify({'error': str(e)}), 500

# Route 14:
@app.route('/venue_report', methods=['GET'])
def venue_report():
    try:
        # Get the data from the request body
        data = request.json

        # Verify authentication key
        auth_key = data.get('auth_key')
        if auth_key != 'xcv0b9':
            return jsonify({'error': 'Invalid authentication key.'}), 403

        # 1. Calculate how many people are in the venue (status code 0 or 1)
        people_in_venue = db.session.query(User).filter(User.status.in_([0, 1])).count()

        # 2. Calculate how many people have exited the venue (status code 3)
        people_exited_venue = db.session.query(User).filter(User.status == 3).count()

        # 3. Calculate total spend (sum of all vendor balances)
        total_spend = db.session.query(db.func.sum(Vendor.vendor_balance)).scalar() or 0

        # Prepare the report data
        report = {
            'people_in_venue': people_in_venue,
            'people_exited_venue': people_exited_venue,
            'total_spend': total_spend
        }

        # Return the report as JSON
        return jsonify(report), 200

    except Exception as e:
        # Handle any exceptions and return a 500 Internal Server Error
        return jsonify({'error': str(e)}), 500



# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1346, debug=False)

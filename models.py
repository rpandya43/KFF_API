# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Registered Users model
class RegisteredUsers(db.Model):
    rid = db.Column(db.String(100), primary_key=True)  # Registration ID (RID)
    slot = db.Column(db.String(50), nullable=False)  # Slot (*** change to array ***)
    name = db.Column(db.String(100), nullable=False)  # Name
    age = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=False)  # Email
    phone = db.Column(db.String(15), nullable=False)  # Phone
    top_up_balance = db.Column(db.Float, nullable=False, default=0.0)  # Top-up Balance
    chakra = db.Column(db.String(100), nullable=False)
    lang_used = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.String(100), nullable=False)
    registration_fees = db.Column(db.String(100), nullable=False)
    total_amt = db.Column(db.String(100), nullable=False)
    volunteer = db.Column(db.String(100), nullable=False)
    pmt_status = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), nullable=True)
    log = db.Column(db.String(100), nullable=True)
    

    # Serialize method to return data as a dictionary
    def serialize(self):
        return {
            'rid': self.rid,
            'slot': self.slot,
            'name': self.name,
            'age': self.age,
            'email': self.email,
            'phone': self.phone,
            'top_up_balance': self.top_up_balance,
            'chakra': self.chakra,
            'lang_used': self.lang_used,
            'created_at': self.created_at,
            'registration_fees': self.registration_fees,
            'total_amt': self.total_amt,
            'volunteer': self.volunteer,
            'pmt_status': self.pmt_status,
            'code': self.code,
            'log': self.log
        }

    # Representation method to make debugging easier
    def __repr__(self):
        return f"<RegisteredUsers {self.rid} - {self.name}>"

# User model
class User(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True)  # User ID
    slot_id = db.Column(db.Integer, nullable=True)  # Slot ID
    customer_class = db.Column(db.String, nullable=False)
    name = db.Column(db.String(100), nullable=True)  # Full Name
    email = db.Column(db.String(100), nullable=True)  # Email
    phone_number = db.Column(db.String(20), nullable=True)  # Phone Number
    nfc_id = db.Column(db.String(100), nullable=True)  # NFC ID
    balance = db.Column(db.Float, default=0.0)  # Balance
    last_transaction = db.Column(db.String(100), nullable=True)  # Last Transaction
    status = db.Column(db.String(100), nullable=False)
    time_in = db.Column(db.DateTime, nullable=True)  # Time In
    time_out = db.Column(db.DateTime, nullable=True)  # Time Out


    def serialize(self):
        return {
            'customer_id': self.customer_id,
            'slot_id': self.slot_id,
            'customer_class': self.customer_class,
            'name': self.name,
            'email': self.email,
            'phone_number': self.phone_number,
            'nfc_id': self.nfc_id,
            'balance': self.balance,
            'last_transaction': self.last_transaction,
            'status': self.status,
            'time_in': self.time_in,
            'time_out': self.time_out,
        }

    def __repr__(self):
        return f"<User {self.name}>"

# Vendor model
class Vendor(db.Model):
    vendor_id = db.Column(db.Integer, primary_key=True)  # Vendor ID
    vendor_name = db.Column(db.String(100), nullable=False)  # Vendor Name
    vendor_phone_number = db.Column(db.String(20), nullable=False)  # Vendor Phone Number
    vendor_balance = db.Column(db.Float, default=0.0)  # Vendor Balance
    vendor_last_transaction = db.Column(db.String(100), nullable=True)  # Vendor Last Transaction

    def serialize(self):
        return {
            'vendor_id': self.vendor_id,
            'vendor_name': self.vendor_name,
            'vendor_phone_number': self.vendor_phone_number,
            'vendor_balance': self.vendor_balance,
            'vendor_last_transaction': self.vendor_last_transaction,
        }

    def __repr__(self):
        return f"<Vendor {self.vendor_name}>"

# Transaction model
class Transaction(db.Model):
    transaction_id = db.Column(db.String(100), primary_key=True)  # Transaction ID
    nfc_id = db.Column(db.String(100), nullable=False)  # NFC ID
    name = db.Column(db.String(100), nullable=False)  # Name
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.vendor_id'), nullable=False)
    transaction_amount = db.Column(db.Float, nullable=False)  # Transaction Amount
    status = db.Column(db.String(50), nullable=False)  # Status
    date_time = db.Column(db.DateTime, nullable=True)  # Date and Time
    type_of_transaction = db.Column(db.String(50), nullable=False)  # Type of Transaction
    customer_id = db.Column(db.Integer, db.ForeignKey('user.customer_id'), nullable=False)


    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

    def serialize(self):
        return {
            'transaction_id': self.transaction_id,
            'nfc_id': self.nfc_id,
            'name': self.name,
            'vendor_id': self.vendor_id,
            'transaction_amount': self.transaction_amount,
            'status': self.status,
            'date_time': self.date_time,
            'type_of_transaction': self.type_of_transaction,
            'customer_id': self.customer_id
        }

    def __repr__(self):
        return f"<Transaction {self.id} by {self.name}>"

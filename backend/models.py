from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)  #  'admin' or 'customer' or 'professional'
    user_status = db.Column(db.String(10), nullable=False)  # active, inactive, blocked

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    pin_code = db.Column(db.Integer, nullable=False)

    user = db.relationship('User',cascade='all,delete', backref=db.backref('customer',uselist=False), uselist=False)
    requests = db.relationship('ServiceRequest',backref=db.backref('customer',uselist=False),cascade='all,delete')

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name= db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    pin_code = db.Column(db.Integer, nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)

    user = db.relationship('User',cascade='all,delete', backref=db.backref('professional',uselist=False), uselist=False)
    requests=db.relationship('ServiceRequest',backref=db.backref('professional',uselist=False),cascade='all,delete')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False, unique=True)
    
    packages = db.relationship('Package', backref=db.backref('service', uselist=False), lazy=True, cascade='all,delete')
    professional = db.relationship('Professional', backref=db.backref('service', uselist=False), lazy=True, cascade='all,delete')

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    package_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

    requests = db.relationship('ServiceRequest', backref=db.backref('package', uselist=False),cascade='all,delete')

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_of_complete = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='requested', nullable=False)  # requested, accepted, rejected, cancelled, completed
    rating = db.Column(db.Integer, nullable=True) # out of 5
    

from sqlalchemy import Column, ForeignKey, true

from .. import db
from datetime import datetime
import copy

#Flask WTF
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, SelectField, IntegerField, SelectMultipleField, FloatField, BooleanField
from wtforms.validators import DataRequired, EqualTo
from sqlalchemy.orm import declarative_base
from datetime import datetime

from functools import reduce

from ..models.abstracts import AbstractStamps
from ..models.paystamps import PayStamps
from ..models.receipts import Receipts
from ..models.shiftstamps import ShiftStamps

from ..helper_functions import program_functions as pf


class GovLevels(db.Model):
    __tablename__ = 'govlevels'
    level = db.Column(db.String(50), nullable=False, primary_key=true)
    campaigns = db.relationship('Campaigns', back_populates='gov_level')

class CreateCampaignForm(FlaskForm):
    candidate = StringField('Candidate', validators=[DataRequired()])
    alias = StringField('Internal Reference Name (firstName_year):', validators=[DataRequired()])
    riding = StringField('Riding:', validators=[DataRequired()])
    year = IntegerField('Election Year:', validators=[DataRequired()])
    gov_level = SelectField('Gov Level:', validators=[DataRequired()])
    hourly_rate = FloatField('Hourly Value:')
    submit = SubmitField('Submit')

class JoinCampaignForm(FlaskForm):
    hex_code=StringField('Enter the provided code for your campaign')
    submit = SubmitField('Submit')

class CampaignContractForm(FlaskForm):
    user = SelectField('User:')
    campaign = SelectField('Campaign:')
    getting_paid = BooleanField('Getting Paid?')
    getting_commute_pay = BooleanField('Getting Commute Pay?')
    admin_rate = FloatField('Admin Hourly Rate:', validators=[DataRequired()])
    canvass_rate = FloatField('Canvass Hourly Rate:', validators=[DataRequired()])
    calling_rate = FloatField('Calling Hourly Rate:', validators=[DataRequired()])
    general_rate = FloatField('General Hourly Rate:', validators=[DataRequired()])
    litdrop_rate = FloatField('Litdrop Hourly Rate:', validators=[DataRequired()])
    commute_rate = FloatField('Commute Hourly Rate:', validators=[DataRequired()])
    submit = SubmitField('Submit')

admins = db.Table('admins', db.Model.metadata, 
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')), 
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id'))
)

payment_exceptions = db.Table('payment_exceptions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaigns.id')),
    db.Column('hourly_rate', db.Integer)
)

default_pay_rates = {
    'admin' : '15.0',
    'canvass' : '15.0',
    'calling' : '15.0',
    'general' : '15.0',
    'litdrop' : '15.0',
    'commute' : '6.50'
}

class Pay_Per_Users(db.Model):
    __tablename__ = 'pay_per_users'
    id = db.Column(db.Integer, primary_key=true)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user  = db.relationship('Users', back_populates='pay_from_campaigns')
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    campaign = db.relationship('Campaigns', back_populates='pay_per_user')
    pay_sum = db.Column(db.JSON)

default_pay_out = {
    'shift_based': {
        'total': 0
    },
    'receipts': 0,
    'abstracts': 0,
    'total_earned': 0,
    'paystamps_sum': 0,
    'paystamps_total': {
        'each_activity': 0,
        'no_category': 0,
        'total': 0
    },
    'owed': {
        'total': 0
    }
}

class Campaign_Contracts(db.Model):
    __tablename__ = 'campaign_contracts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id')) 
    campaign_id = db.Column(db.ForeignKey('campaigns.id'))
    campaign = db.relationship('Campaigns', back_populates='user_contracts')
    user = db.relationship("Users", back_populates='campaign_contracts')
    getting_paid = db.Column(db.Boolean, default=False)
    getting_commute_pay = db.Column(db.Boolean, default=False)
    commute_pay = db.Column(db.Float, default=0)
    pay_rates = db.Column(db.JSON, nullable=False, default=default_pay_rates)
    pay_out = db.Column(db.JSON, nullable=False, default=default_pay_out)

    def process_new_shift(self, shift: ShiftStamps):
        d = copy.deepcopy(self.pay_out.copy())
        """if self.getting_paid == 1:
            if self.getting_commute_pay == 1:    
                sum = (float(shift.minutes) * (float(shift.hourly_rate)/60)) + float(self.commute_pay)
            else:
                sum = (float(shift.minutes) * (float(shift.hourly_rate)/60))
        try:
            d['earnings']['shift_based'][shift.activity_id] += sum
        except KeyError as e:
            d['earnings']['shift_based'][shift.activity_id] = sum

        try:
            d['earnings']['shift_based']['total'] += sum
        except KeyError as e:
            d['earnings']['shift_based']['total'] = sum

        try:
            d['earnings']['total'] += sum
        except KeyError as e:
            d['earnings']['total'] = sum

        self.pay_out = d
        """
        db.session.commit()

    def process_new_paystamp(self, paystamp: PayStamps):
        d = copy.deepcopy(self.pay_out.copy())
        try:
            d['paystamps'][paystamp.activity_id] += paystamp.amount
        except KeyError:
            d['paystamps'][paystamp.activity_id] = paystamp.amount
        try:
            d['paystamps']['total'] += paystamp.amount
        except KeyError:
            d['paystamps']['total'] = paystamp.amount
        
        self.pay_out = d
        db.session.commit()

    def process_new_receipt(self, receipt: Receipts):
        d = copy.deepcopy(self.pay_out.copy())
        if receipt.accepted == 1:
            try:
                d['earnings']['receipts'] += receipt.amount
            except KeyError:
                d['earnings']['receipts'] = receipt.amount
            try:
                d['earnings']['total'] += receipt.amount
            except KeyError:
                d['earnings']['total'] = receipt.amount

        self.pay_out = d
        db.session.commit()

    def process_new_abstract(self, abstract: AbstractStamps):
        d = copy.deepcopy(self.pay_out.copy())
        if abstract.accepted == 1:
            try:
                d['earnings']['abstracts'] += abstract.amount
            except KeyError:
                d['earnings']['abstracts'] = abstract.amount
            try:
                d['earnings']['total'] += abstract.amount
            except KeyError:
                d['earnings']['total'] = abstract.amount

        self.pay_out = d
        db.session.commit()       

    def process_totals(self):
        d = copy.deepcopy(self.pay_out.copy())
        d['owed']['untrunced_sum'] = d['earnings']['total'] - d['paystamps']['total']
        d['owed']['total'] = pf.negtrunc(d['owed']['untrunced_sum'])
        
        self.pay_out = d
        db.session.commit()


class Campaigns(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #if this gets uncommented, make sure to uncomment Users.py candidacies
    #candidate_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    #candidate = db.relationship('Users', back_populates="candidacies")
    
    # Campaign Info
    candidate = db.Column(db.String(100), nullable=False)
    alias = db.Column(db.String(50), nullable=False)
    riding = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    gov_level_id = db.Column(db.String(50), db.ForeignKey('govlevels.level'), nullable=False)
    gov_level = db.relationship('GovLevels')
    
    # Management Info
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('Users', back_populates='campaigns_owned')
    admins = db.relationship('Users', secondary=admins, back_populates="admin_campaigns")
    user_contracts = db.relationship('Campaign_Contracts', back_populates="campaign")
    
    # Stamps
    shiftstamps_on_campaign = db.relationship('ShiftStamps', back_populates='campaign')
    paystamps_on_campaign = db.relationship('PayStamps', back_populates='campaign')
    abstractstamps_on_campaign = db.relationship('AbstractStamps', back_populates='campaign')
    receipts = db.relationship('Receipts', back_populates='campaign')
    
    hex_code = db.Column(db.String(30), nullable=False, unique=True)
    
    # Pay Amount
    default_commute_pay = db.Column(db.Float, nullable=False, default=0)
    pay_rates = db.Column(db.JSON, nullable=False, default=default_pay_rates)
    admin_rate = db.Column(db.Float, nullable=False, default=15.0)
    canvass_rate = db.Column(db.Float, nullable=False, default=15.0)
    calling_rate = db.Column(db.Float, nullable=False, default=15.0)
    general_rate = db.Column(db.Float, nullable=False, default=15.0)
    litdrop_rate = db.Column(db.Float, nullable=False, default=15.0)
    pay_per_user = db.relationship("Pay_Per_Users", back_populates='campaign')

    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, **kwargs):
        super(Campaigns, self).__init__(**kwargs)
        for user in self.admins:
            user.system_level_id = 4

        db.session.commit()

    def upgrade_to_admin(self):
        for user in self.admins:
            user.system_level_id = 4

        db.session.commit()

    def get_users(self, format):
        '''
        get admins based on format provided. id_list format is a list of admin ids. vlp format is value label pairs
        '''
        contract: Campaign_Contracts

        if format == 'id_list':
            return [contract.user_id for contract in self.user_contracts]
        elif format == 'vlp':
            arr = []
            for contract in self.user_contracts:
                label = contract.user.alias + ' - ' +  contract.user.first_name + ' ' + contract.user.last_name
                t = (contract.user.id, label)
                arr.append(t)
            return arr


    def add_admin():
        pass

    def remove_admin():
        pass

    def get_admins(self, format):
        '''
        get admins based on format provided. id_list format is a list of admin ids. vlp format is value label pairs
        '''
        if format == 'id_list':
            return [admin.id for admin in self.admins]
        elif format == 'vlp':
            arr = []
            for admin in self.admins:
                label =  admin.alias + ' - ' +  admin.first_name + ' ' + admin.last_name
                t = (admin.id, label)
                arr.append(t)

            return arr

    def process_new_shift(self, shift: ShiftStamps):
        user_contract: Campaign_Contracts = Campaign_Contracts.query.filter_by(user_id=shift.user_id, campaign_id=self.id).first()
        user_contract.process_new_shift(shift)
        db.session.commit()

    def process_new_paystamp(self, paystamp: PayStamps):
        user_contract: Campaign_Contracts = Campaign_Contracts.query.filter_by(user_id=paystamp.user_id, campaign_id=self.id).first()
        user_contract.process_new_paystamp(paystamp)
        db.session.commit()

    def process_new_receipt(self, receipt: Receipts):
        user_contract: Campaign_Contracts = Campaign_Contracts.query.filter_by(user_id=receipt.user_id, campaign_id=self.id).first()
        user_contract.process_new_receipt(receipt)
        db.session.commit()

    def process_new_abstract(self, abstract: AbstractStamps):
        user_contract: Campaign_Contracts = Campaign_Contracts.query.filter_by(user_id=abstract.user_id, campaign_id=self.id).first()
        user_contract.process_new_abstract(abstract)
        db.session.commit()  


    def process_totals(self):
        user_contract: Campaign_Contracts
        for user_contract in self.user_contracts:
            user_contract.process_totals()
            db.session.commit()

    def process_pay(self):
        '''Process the pay in a Pay_Per_Users object
        user_id: int
        user: relationship
        campaign_id: int
        campaign: relationship
        pay_sum = {
            earnings: {
                shift_based: {
                    each_activity: float
                    total: int
                },
                receipts: float,
                abstracts: float,
                total: float,
            }
            paystamps: {
                each_activity: float
                total: float
            }
            owed: {
                each_activity: float
                all_activites: float
                total: float
            }
        }
        '''
        # Iterate every contract
        user_contract: Campaign_Contracts
        for user_contract in self.user_contracts:
            out = {}
            earnings = {}
            shift_based = {}
            receipts_abstracts = {}
            paystamps = {}
            paystamps = {}
            owed = {}

            total = 0
            total_paid = 0
            
            # Earnings
            # Calculate Shift Based Earnings
            total = 0
            for pay_rate in user_contract.pay_rates:
                search_term = str(pay_rate).replace('_rate', '')
                shifts = ShiftStamps.query.filter_by(user_id=user_contract.user_id, activity_id=search_term, campaign_id=user_contract.campaign_id)
                shift: ShiftStamps
                activity_total = 0
                if user_contract.getting_paid == 0:
                        for shift in shifts:
                            if user_contract.getting_commute_pay == 1:    
                                activity_total = activity_total + (float(shift.minutes) * (float(shift.hourly_rate)/60)) + float(user_contract.commute_pay)
                            else:
                                activity_total = activity_total + (float(shift.minutes) * (float(shift.hourly_rate)/60))

                        shift_based[str(pay_rate).replace('_rate', '')] = activity_total
                else:
                    shift_based[str(pay_rate).replace('_rate', '')] = 0

                total += activity_total
            shift_based['total'] = total

            # Receipts and Abstracts
            receipts_abstracts['receipts'] = 0
            receipts = Receipts.query.filter_by(user_id=user_contract.user_id)
            r: Receipts
            for r in receipts:
                receipts_abstracts['receipts'] += float(r.amount)
                total += float(r.amount)

            receipts_abstracts['abstracts'] = 0
            abstracts = AbstractStamps.query.filter_by(user_id=user_contract.user_id)
            a: AbstractStamps
            for a in abstracts:
                receipts_abstracts['abstracts'] += float(a.amount)
                total += float(a.amount)

            # Paystamps
            '''
            for pay_rate, pay_rate_amount in user_contract.pay_rates.items():
                paystamp_arr = PayStamps.query.filter_by(user_id=user_contract.user_id, description=str(pay_rate).replace('_rate', ''))
                total_paid = 0
                paystamp_item: PayStamps
                for paystamp_item in paystamp_arr:
                    total_paid =+ paystamp_item.amount
            '''
            total_paid = 0
            paystamps_arr = PayStamps.query.filter_by(user_id=user_contract.user_id)
            paystamp: PayStamps
            for paystamp in paystamps_arr:
                txt = paystamp.activity_id
                try:
                    paystamps[txt] += paystamp.amount
                
                except KeyError:
                    paystamps[txt] = paystamp.amount
                total_paid += paystamp.amount

            #Owed
            owed['untrunced_sum'] = total - total_paid 
            owed['total'] = pf.negtrunc(owed['untrunced_sum'])

            #Output
            earnings['shift_based'] = shift_based
            earnings.update(receipts_abstracts)
            earnings['total'] = total
            paystamps['total'] = total_paid

            out['earnings'] = earnings
            out['paystamps'] = paystamps
            out['owed'] = owed

            user_contract.pay_out = out
            db.session.commit()


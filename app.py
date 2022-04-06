from flask import Flask, jsonify, request, render_template, flash, redirect, session, url_for, logging,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
import os
from flask_marshmallow import Marshmallow
from wtforms import Form, StringField, TextAreaField, SelectField, IntegerField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import datetime
import random
import string
from chat import vanitha
import pandas as pd


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'bank.db')


db = SQLAlchemy(app)
ma = Marshmallow(app)


# Creating Database using flask cli
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


# Deleting database using flask cli
@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


# Seeding database using flask cli
@app.cli.command('db_seed')
def db_seed():
    executive_user = Userstore(
        username='executive1@test.com', password=sha256_crypt.hash('adminpw'), access=0)
    cashier_user = Userstore(username='cashier1@test.com',
                             password=sha256_crypt.hash('adminpw'), access=1)
    db.session.add(executive_user)
    db.session.add(cashier_user)
    db.session.commit()
    print('Database seeded!')


# Session management
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('unauthorized,please login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_c = request.form['password']
        test = Userstore.query.filter_by(username=username).first()
        if test:
            password = test.password
            if sha256_crypt.verify(password_c, password):
                session['logged_in'] = True
                session['username'] = username
                acc = test.access
                if acc == 1:
                    flash('You are now logged in', 'success')
                    return redirect(url_for('cashier_home'))
                flash('You are now logged in', 'success')
                return redirect(url_for('home'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
        else:
            error = 'Username Not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


# access control
ACCESS = {
    'executive': 0,    # New account/New customer executive
    'cashier': 1,     # Cashier/Teller
}


class User():
    def __init__(self, username, access):
        self.username = username
        self.access = access

    def is_executive(self, access_level):
        return self.access == access_level

    def is_cahier(self, access_level):
        return self.access == access_level


def requires_access_level(access_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('username'):
                return redirect(url_for('login'))
            username = session['username']
            test = Userstore.query.filter_by(username=username).first()
            user = User(test.username, test.access)
            if not user.is_executive(access_level):
                flash("You do not have access to that page. Sorry!", 'danger')
                return redirect(url_for('home'))
            elif not user.is_cahier(access_level):
                flash("You do not have access to that page. Sorry!", 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/cashier')
def cashier_home():
    return render_template('cashier_home.html')


@app.route('/get')
def vanitha1():
    userText = request.args.get('msg')
    tmp = vanitha(userText)
    return render_template('home.html', test=tmp)


# Customer registration form
class RegisterForm(Form):
    ssn_id = IntegerField('Customer SSN Id', [
                          validators.NumberRange(min=100000000, max=999999999)])
    name = StringField('Customer Name', [validators.Length(min=5, max=15)])
    age = IntegerField('Age', [validators.DataRequired(),validators.NumberRange(min=12, max=150)])

    address = StringField(
        'Address Line 1', [validators.Length(min=10, max=50)])
    address2 = StringField(
        'Address Line 2', [validators.Length(min=10, max=50)])
    state = StringField('State', [validators.Length(min=2, max=15)])
    city = StringField('City', [validators.Length(min=2, max=15)])


@app.route('/register', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        ssn_id = form.ssn_id.data
        name = form.name.data
        address = form.address.data + " " + form.address2.data
        age = form.age.data
        state = form.state.data
        city = form.city.data
        cust_status = customerstatus.query.filter_by(ssn_id=ssn_id).first()
        if cust_status is not None and cust_status.status == "active":
            flash("SSN ID already exist", 'danger')
            return render_template('register.html', form=form)
        elif cust_status is not None and cust_status.status == "inactive":
            user = Customer(ssn_id=ssn_id, customer_id=cust_status.customer_id,
                            name=name, address=address, age=age, state=state, city=city)
            db.session.add(user)
            cust_status.status = 'active'
            cust_status.message = 'customer created'
            Account_status = accountstatus.query.filter_by(
                customer_id=cust_status.customer_id).first()
            Account_status.account_status = "pending"
            db.session.commit()
            flash('Customer creation initiated successfully', 'success')
            redirect(url_for('login'))
        else:
            customer_id = generate_customer_Id()
            customer_id = int(customer_id)
            user = Customer(ssn_id=ssn_id, customer_id=customer_id,
                            name=name, address=address, age=age, state=state, city=city)
            db.session.add(user)
            user_status = customerstatus(ssn_id=ssn_id, customer_id=customer_id,
                                         status='active', message='Customer details created successfully')
            db.session.add(user_status)
            Account_status = accountstatus(
                customer_id=customer_id, account_status='Pending')
            db.session.add(Account_status)
            db.session.commit()
            flash('Customer creation initiated successfully', 'success')
            redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/search', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def search():
    if request.method == 'POST':
        ssn_id = request.form['ssn_id']
        customer_id = request.form['customer_id']
        message_ssn = ""
        message_customer = ""
        test_ssn = 1
        test_customer = 1
        if ssn_id:
            if not ssn_id.isnumeric():
                message_ssn = "SSN Id must be numberic"
            else:
                if not len(ssn_id)==9:
                    message_ssn = "SSN Id must be 9 digits"
                else:
                    test_ssn = Customer.query.filter_by(ssn_id=ssn_id).first()
        if customer_id:
            if not customer_id.isnumeric():
                message_customer = "Customer Id must be numberic"
            else:
                if not len(customer_id)==9:
                    message_customer = "Customer Id must be 9 digits"
                else:
                    test_customer = Customer.query.filter_by(customer_id=customer_id).first()

        if not len(message_customer)==0 or not len(message_ssn)==0:

            return render_template('search.html',message_customer=message_customer,message_ssn=message_ssn)

        if len(customer_id)==0 and len(ssn_id)==0:
            flash("Fill atleast one field",'danger')
            return render_template('search.html')

        if test_customer is None or test_ssn is None:
            flash("Customer doesn't exist",'danger')
            return render_template('search.html')
        elif not test_customer is None and not test_customer==1:
            result = customer_schema.dump(test_customer)
            return render_template('update.html',search=result)
        elif not test_ssn is None and not test_ssn==1:
            result = customer_schema.dump(test_ssn)
            return render_template('update.html',search=result)
    return render_template('search.html')


@app.route('/customer_search', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def customer_search():
    if request.method == 'POST':
        ssn_id = request.form['ssn_id']
        customer_id = request.form['customer_id']
        message_ssn = ""
        message_customer = ""
        test_ssn = 1
        test_customer = 1
        if ssn_id:
            if not ssn_id.isnumeric():
                message_ssn = "SSN Id must be numberic"
            else:
                if not len(ssn_id)==9:
                    message_ssn = "SSN Id must be 9 digits"
                else:
                    test_ssn = Customer.query.filter_by(ssn_id=ssn_id).first()
        if customer_id:
            if not customer_id.isnumeric():
                message_customer = "Customer Id must be numberic"
            else:
                if not len(customer_id)==9:
                    message_customer = "Customer Id must be 9 digits"
                else:
                    test_customer = Customer.query.filter_by(customer_id=customer_id).first()

        if not len(message_customer)==0 or not len(message_ssn)==0:

            return render_template('customer_search.html',message_customer=message_customer,message_ssn=message_ssn)

        if len(customer_id)==0 and len(ssn_id)==0:
            flash("Fill atleast one field",'danger')
            return render_template('customer_search.html')

        if test_customer is None or test_ssn is None:
            flash("Customer doesn't exist",'danger')
            return render_template('customer_search.html')
        elif not test_customer is None and not test_customer==1:
            result = customer_schema.dump(test_customer)
            return render_template('customer_search.html',search=result)
        elif not test_ssn is None and not test_ssn==1:
            result = customer_schema.dump(test_ssn)
            return render_template('customer_search.html',search=result)
    return render_template('customer_search.html')

@app.route('/account_search', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def account_search():
    if request.method == 'POST':
        account_id = request.form['account_id']
        customer_id = request.form['customer_id']
        message_account = ""
        message_customer = ""
        test_account = 1
        test_customer = 1
        if account_id:
            if not account_id.isnumeric():
                message_account = "Account Id must be numberic"
            else:
                if not len(account_id)==9:
                    message_account = "Account Id must be 9 digits"
                else:
                    test_account = Account.query.filter_by(account_id=account_id).first()
        if customer_id:
            if not customer_id.isnumeric():
                message_customer = "Customer Id must be numberic"
            else:
                if not len(customer_id)==9:
                    message_customer = "Customer Id must be 9 digits"
                else:
                    test_customer = Account.query.filter_by(customer_id=customer_id).first()

        if not len(message_customer)==0 or not len(message_account)==0:

            return render_template('account_search.html',message_customer=message_customer,message_account=message_account)

        if len(customer_id)==0 and len(account_id)==0:
            flash("Fill atleast one field",'danger')
            return render_template('account_search.html')

        if test_customer is None or test_account is None:
            flash("Account doesn't exist",'danger')
            return render_template('account_search.html')
        elif not test_customer is None and not test_customer==1:
            result = acc_schema.dump(test_customer)
            return render_template('account_search.html', search=result)
        elif not test_account is None and not test_account==1:
            result = acc_schema.dump(test_account)
            return render_template('account_search.html', search=result)
    return render_template('account_search.html')


class UpdateForm(Form):
    name = StringField('Name', [validators.Length(min=5, max=200)])
    address = StringField('address', [validators.Length(min=3)])
    age = StringField('Age', [validators.DataRequired(), validators.Regexp(
        '[0-9]', message="Age must be Numeric only"), validators.Length(min=1, max=3)])


# Update Customer details
@app.route('/update/<string:ssn_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def update(ssn_id):
    test = Customer.query.filter_by(ssn_id=ssn_id).first()
    result = customer_schema.dump(test)
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        age = request.form['age']
        print(name,address,age)
        if not len(name)==0:
            test.name = name
        if not len(address)==0:
            test.address = address
        if not len(age)==0:
            test.age = age
        print(test.age,test.name,test.address)
        user_status = customerstatus.query.filter_by(ssn_id=ssn_id).first()
        user_status.message = 'Customer Update Complete'
        db.session.add(user_status)
        db.session.add(test)
        db.session.commit()
        test = Customer.query.filter_by(ssn_id=ssn_id).first()
        result = customer_schema.dump(test)
        flash("Customer update initiated successfully", "success")
    return render_template('update.html', search=result)


@app.route('/delete_search', methods=['GET', 'POST'])
@is_logged_in
def delete_search():
    if request.method == 'POST':
        ssn_id = request.form['ssn_id']
        customer_id = request.form['customer_id']
        message_ssn = ""
        message_customer = ""
        test_ssn = 1
        test_customer = 1

        if ssn_id:
            if not ssn_id.isnumeric():
                message_ssn = "SSN Id must be numberic"
            else:
                if not len(ssn_id)==9:
                    message_ssn = "SSN Id must be 9 digits"
                else:
                    test_ssn = Customer.query.filter_by(ssn_id=ssn_id).first()
        if customer_id:
            if not customer_id.isnumeric():
                message_customer = "Customer Id must be numberic"
            else:
                if not len(customer_id)==9:
                    message_customer = "Customer Id must be 9 digits"
                else:
                    test_customer = Customer.query.filter_by(customer_id=customer_id).first()

        if not len(message_customer)==0 or not len(message_ssn)==0:

            return render_template('delete_search.html',message_customer=message_customer,message_ssn=message_ssn)

        if len(customer_id)==0 and len(ssn_id)==0:
            flash("Fill atleast one field",'danger')
            return render_template('delete_search.html')

        if test_customer is None or test_ssn is None:
            flash("Customer doesn't exist",'danger')
            return render_template('delete_search.html')
        elif not test_customer is None and not test_customer==1:
            result = customer_schema.dump(test_customer)
            return render_template('delete.html',search=result)
        elif not test_ssn is None and not test_ssn==1:
            result = customer_schema.dump(test_ssn)
            return render_template('delete.html',search=result)
    return render_template('delete_search.html')


# Hard delete (soft delete need to be implemented)
@app.route('/delete/<string:ssn_id>', methods=['POST', 'GET'])
@requires_access_level(ACCESS['executive'])
def delete(ssn_id):
    test = Customer.query.filter_by(ssn_id=ssn_id).first()
    if test:
        user_status = customerstatus.query.filter_by(ssn_id=ssn_id).first()
        user_status.message = 'User details deleted'
        user_status.status = 'inactive'
        status = accountstatus.query.filter_by(customer_id=user_status.customer_id).first()
        account = Account.query.filter_by(account_id=status.account_id).first()
        if account:
            db.session.delete(account)
            db.session.commit()
        print(account)
        status.account_id = None
        status.account_type = None
        status.account_status = "inactive"
        status.message = "Account delete"
        db.session.add(status)
        db.session.delete(test)
        db.session.commit()
        flash("Customer deletion initiated successfully", 'success')
        redirect(url_for('home'))
    else:
        return jsonify(message="That record does not exist"), 404
    return render_template('delete.html')


@app.route('/customer_status/', methods=['POST', 'GET'])
@app.route('/customer_status/<int:page_num>', methods=['POST', 'GET'])
@requires_access_level(ACCESS['executive'])
def customer_status(page_num=1):
    test = customerstatus.query.paginate(
        per_page=10, page=page_num, error_out=True)
    return render_template('customer_status.html', lists=test)


@app.route('/view_profile/<string:ssn_id>', methods=['GET'])
@requires_access_level(ACCESS['executive'])
def view_profile(ssn_id):
    test = Customer.query.filter_by(ssn_id=ssn_id).first()
    result = customer_schema.dump(test)
    if test:
        return render_template('view_profile.html', search=test)
    else:
        flash('Customer Profile does not exist', 'danger')
    return render_template('view_profile.html')

# Account registration form


class AccountForm(Form):
    customer_id = StringField('Customer ID', [validators.DataRequired(),validators.Regexp(
        '[0-9]', message="Customer Id must be Numeric only"), validators.Length(min=9, max=9)])
    acc_type = SelectField('Account type', choices=[(
        'saving', 'Savings Account'), ('current', 'Current Account')])
    deposit_amount = IntegerField(
        'Deposit Amount', [validators.DataRequired()])

    def validate_customer_id(self, customer_id):
        customer = Customer.query.filter_by(
            customer_id=customer_id.data).first()
        if customer is None:
            raise validators.ValidationError("Customer doesn't exists.")
        is_customer = int(customer_id.data) == customer.customer_id
        if is_customer:
            is_AccountExist = Account.query.filter_by(
                customer_id=customer_id.data).first()

            if is_AccountExist is not None:
                accstat = accountstatus.query.filter_by(
                    customer_id=customer_id.data).first()
                if accstat.account_status == "active":
                    raise validators.ValidationError("Account already exists.")

        else:
            raise validators.ValidationError("Customer doesn't exists.")


@app.route('/account', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def account():
    form = AccountForm(request.form)
    if request.method == 'POST' and form.validate():
        customer_id = form.customer_id.data
        acc_type = form.acc_type.data
        deposit_amount = form.deposit_amount.data
        customer_id = int(customer_id)
        test = Customer.query.filter_by(customer_id=customer_id).first()
        if test:
            account_id = generate_account_id()
            account = Account(account_id=account_id, customer_id=customer_id,
                              account_type=acc_type, deposit_amount=deposit_amount)
            db.session.add(account)
            test = accountstatus.query.filter_by(
                customer_id=customer_id).first()
            test.account_id = account_id
            test.account_type = acc_type
            test.account_status = 'active'
            test.message = 'account created successfully'
            db.session.commit()
            flash('Account creation initiated successfully', 'success')
            redirect(url_for('account'))
        else:
            flash('Customer Does not exist to crate account')
    return render_template('account.html', form=form)


@app.route('/delete_account', methods=['GET', 'POST'])
@requires_access_level(ACCESS['executive'])
def delete_search_account():
    if request.method == 'POST':
        account_id = request.form['account_id']
        test = Account.query.filter_by(account_id=account_id).first()
        if test:
            result = acc_schema.dump(test)
            return render_template('delete_account.html', search=result)
        else:
            return jsonify(message="This record does not exist"), 404
    return render_template('delete_search_account.html')


@app.route('/deleteacc/<string:account_id>', methods=['POST', 'GET'])
@requires_access_level(ACCESS['executive'])
def deleteacc(account_id):
    test = Account.query.filter_by(account_id=account_id).first()
    if test:
        user_status = accountstatus.query.filter_by(
            account_id=account_id).first()
        user_status.message = 'Account deleted'
        user_status.account_status = 'inactive'
        db.session.delete(test)
        db.session.commit()
        flash("You deleted account details", 'success')
        redirect(url_for('home'))
    else:
        return jsonify(message="That record does not exist"), 404
    return render_template('delete.html')


# cashier
@app.route('/cashier_transaction/<string:acc_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def transfer_money(acc_id):
    acc = Account.query.filter_by(account_id=acc_id).first()
    result = acc_schema.dump(acc)
    if request.method == 'POST':
        dest_id = request.form['dest_id']
        d_acc = Account.query.filter_by(account_id=dest_id).first()
        dest_acc = acc_schema.dump(d_acc)
        if not d_acc:
            flash('Destination account does not exist', 'danger')
            return render_template('cashier_transfer.html', account=result)
        if dest_id == acc_id:
            flash('Destination and source account can not be same', 'danger')
            return render_template('cashier_transfer.html', account=result)
        trnsfr = int(request.form['deposit'])
        if result['deposit_amount'] < trnsfr:
            flash('Transfer not allowed, please choose smaller amount', 'danger')
            return render_template('cashier_transfer.html', account=result)
        update_source_balance = result['deposit_amount'] - trnsfr
        update_dest_balance = dest_acc['deposit_amount'] + trnsfr
        acc = Account.query.filter_by(account_id=acc_id).update(
            {'deposit_amount': update_source_balance})
        d_acc = Account.query.filter_by(account_id=dest_id).update(
            {'deposit_amount': update_dest_balance})
        db.session.commit()
        tcn_id = generate_trxcn_id()
        add_transaction_id(tcn_id, acc_id, 'Transfer', trnsfr, 'source')
        tcn_id = generate_trxcn_id()
        add_transaction_id(tcn_id, dest_id, 'Transfer', trnsfr, 'destination')
        flash('Amount transfer completed successfully', 'success')
        return render_template('transaction_msg.html', latest=update_source_balance, old=update_source_balance + trnsfr)
    return render_template('cashier_transfer.html', account=result)


@app.route('/cashier_deposit/<string:acc_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def deposit_money(acc_id):
    acc = Account.query.filter_by(account_id=acc_id).first()
    result = acc_schema.dump(acc)
    if request.method == 'POST':
        if not acc:
            flash('Account does not exist', 'danger')
            return render_template('cashier_deposit.html', account=result)
        deposit = int(request.form['deposit'])
        if not deposit:
            flash('Please enter a valid amount', 'danger')
            return render_template('cashier_deposit.html', account=result)
        update_balance = result['deposit_amount'] + deposit
        acc = Account.query.filter_by(account_id=acc_id).update(
            {'deposit_amount': update_balance})
        db.session.commit()
        tcn_id = generate_trxcn_id()
        add_transaction_id(tcn_id, acc_id, 'Deposit', deposit)
        flash("Amount deposited successfully", 'success')
        return render_template('transaction_msg.html', latest=update_balance, old=update_balance - deposit)
    return render_template('cashier_deposit.html', account=result)


@app.route('/cashier_withdraw/<string:acc_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def withdraw_money(acc_id):
    acc = Account.query.filter_by(account_id=acc_id).first()
    result = acc_schema.dump(acc)
    if request.method == 'POST':
        if not acc:
            flash('Account does not exist', 'danger')
            return render_template('cashier_withdraw.html', account=result)
        withdraw = int(request.form['withdraw'])
        if not withdraw:
            flash('Please enter a valid amount', 'danger')
            return render_template('cashier_withdraw.html', account=result)
        if withdraw > result['deposit_amount']:
            flash('Withdraw not allowed, please choose smaller amount', 'danger')
            return render_template('cashier_withdraw.html', account=result)
        update_balance = result['deposit_amount'] - withdraw
        acc = Account.query.filter_by(account_id=acc_id).update(
            {'deposit_amount': update_balance})
        db.session.commit()
        tcn_id = generate_trxcn_id()
        add_transaction_id(tcn_id, acc_id, 'Withdraw', withdraw)
        flash("Amount withdrawn successfully", 'success')
        return render_template('transaction_msg.html', latest=update_balance, old=update_balance + withdraw)
    return render_template('cashier_withdraw.html', account=result)


@app.route('/account_stmnt', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def check_stmnts():
    if request.method == 'POST':
        acc_id = request.form['acc_id']
        acc = Account.query.filter_by(account_id=acc_id).first()
        if not acc:
            flash('Account not found', 'danger')
            return render_template('transaction_statement.html')
        txn_type = request.form['trxcn_type']
        if txn_type == 'num':
            records = int(request.form.get('number'))
            txn_objs = Transaction.query.filter_by(account_id=acc_id).order_by(
                Transaction.trxcn_date.desc())[0:records]
            result = txns_schema.dump(txn_objs)
            return render_template('transaction_statement.html', records=result)
        else:
            return redirect(url_for('get_transaction_records', acc_id=acc_id))

    return render_template('transaction_statement.html')


@app.route('/download_excel',methods=['GET','POST'])
@requires_access_level(ACCESS['cashier'])
def download_excel():
    return send_from_directory(basedir,'statement.csv',as_attachment=True)

@app.context_processor
def utility_processor():
    def excel(file):
        df_json = pd.DataFrame(file,columns = ['trxcn_id', 'account_id','description', 'amount', 'trxcn_date'])
        df_json.columns=['Transaction Id','Account Id','Description','Amount','Transaction Date']
        df_json.to_csv('statement.csv')
    return dict(excel=excel)



@app.route('/transaction/details/<string:acc_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def get_transaction_records(acc_id):
    if request.method == 'POST':
        start_date = request.form['start']
        end_date = request.form['end']
        if start_date > end_date:
            flash('End Date should be greater than start date', 'danger')
            return render_template('transaction_by_date_cashier.html', acc_id=acc_id)
        today_date = datetime.date.today()
        if start_date > str(today_date):
            flash("Start Date is not valid", 'danger')
            return render_template('transaction_by_date_cashier.html', acc_id=acc_id)
        if end_date > str(today_date):
            flash("End Date is not valid", 'danger')
            return render_template('transaction_by_date_cashier.html', acc_id=acc_id)
        date = start_date.split('-')
        start_date = datetime.datetime(
            int(date[0]), int(date[1]), int(date[2]), 0, 0, 0, 0)
        date = end_date.split('-')
        end_date = datetime.datetime(int(date[0]), int(
            date[1]), int(date[2]), 23, 59, 59, 999999)
        txn_records = Transaction.query.filter_by(account_id=acc_id).filter(Transaction.trxcn_date >= start_date).\
            filter(Transaction.trxcn_date <= end_date).order_by(
                Transaction.trxcn_date.desc())
        return render_template('transaction_by_date_cashier.html', acc_id=acc_id, records=txn_records)
    return render_template('transaction_by_date_cashier.html', acc_id=acc_id)


class AccountDeleteForm(Form):
    ssn_id = StringField('SSN ID')
    customer_id = StringField('Customer ID')

    def validate_ssn_id(self, ssn_id):
        if len(ssn_id.data):
            if not ssn_id.data.isnumeric():
                raise validators.ValidationError(
                    "SSN ID must be Numerical value")
            elif not len(ssn_id.data) == 9:
                raise validators.ValidationError(
                    "Field must be exactly 9 characters long.")
        elif len(ssn_id.data) == 9:
            customer = Customer.query.filter_by(ssn_id=ssn_id.data).first()
            if customer is None:
                raise validators.ValidationError("Customer doesn't exists")

    def validate_customer_id(self, customer_id):
        if len(customer_id.data):
            if not customer_id.data.isnumeric():
                raise validators.ValidationError(
                    "Customer ID must be Numerical value")
            elif not len(customer_id.data) == 9:
                raise validators.ValidationError(
                    "Field must be exactly 9 characters long.")
        elif len(customer_id.data) == 9:
            customer = Customer.query.filter_by(
                customer_id=customer_id.data).first()
            if customer is None:
                raise validators.ValidationError("Customer doesn't exists")


# Hard delete (soft delete need to be implemented)
@app.route('/account_delete', methods=['POST', 'GET'])
@requires_access_level(ACCESS['executive'])
def account_delete():

    form = AccountDeleteForm(request.form)
    if request.method == 'POST' and form.validate():
        ssn_id = form.ssn_id.data
        customer_id = form.customer_id.data

        if len(ssn_id) == 0 and len(customer_id) == 0:
            flash("Fill atleast one field", 'danger')
            return render_template('account_delete.html', form=form)

        print("check condition")
        if len(ssn_id):
            customer_status = customerstatus.query.filter_by(
                ssn_id=ssn_id).first()
            customer_id = customer_status.customer_id
            print(customer_id)
            status = accountstatus.query.filter_by(
                customer_id=customer_id).first()
            print(status)
            if status.account_id is None:
                flash("Account doesn't exists", "danger")
                return render_template('account_delete.html', form=form)

        elif len(customer_id):
            status = accountstatus.query.filter_by(
                customer_id=customer_id).first()
            if status.account_id is None:
                flash("Account doesn't exists", "danger")
                return render_template('account_delete.html', form=form)

        form = AccountShowForm(request.form)
        return render_template('account_check.html', form=form, status=status)

    return render_template('account_delete.html', form=form)


class AccountShowForm(Form):
    account_id = StringField('Account ID')
    account_type = StringField('Account type')


@app.route('/account_check', methods=['POST', 'GET'])
def account_check():
    print("comes")
    form = AccountShowForm(request.form)
    if request.method == 'POST' and form.validate():
        account_id = form.account_id.data
        status = accountstatus.query.filter_by(account_id=account_id).first()
        account = Account.query.filter_by(account_id=account_id).first()
        status.account_id = None
        status.account_type = None
        status.account_status = "inactive"
        status.message = "Account delete"
        db.session.add(status)
        db.session.delete(account)
        db.session.commit()
        flash("Account deletion initiated successfully", 'success')
        return redirect(url_for('account_delete'))
    return redirect(url_for('home'))


@app.route('/account_status/', methods=['GET', 'POST'])
@app.route('/account_status/<int:page_num>', methods=['POST', 'GET'])
@requires_access_level(ACCESS['executive'])
def account_status(page_num=1):
    test = accountstatus.query.paginate(
        per_page=10, page=page_num, error_out=True)
    return render_template('account_status.html', lists=test)


@app.route('/acc_details/<string:acc_id>', methods=['GET', 'POST'])
@requires_access_level(ACCESS['cashier'])
def accounts(acc_id):
    if request.method == 'POST':
        if 'transfer' in request.form:
            return redirect(url_for('transfer_money', acc_id=acc_id))
        if 'deposit' in request.form:
            return redirect(url_for('deposit_money', acc_id=acc_id))
        if 'withdraw' in request.form:
            return redirect(url_for('withdraw_money', acc_id=acc_id))
    acc = Account.query.filter_by(account_id=acc_id).first()
    result = acc_schema.dump(acc)
    return render_template("accounts.html", result=result)


@app.route('/account_details', methods=['POST', 'GET'])
@requires_access_level(ACCESS['cashier'])
def acc_details():
    if request.method == 'POST':
        if 'submit' in request.form:
            selected_id = request.form['selected_acc_id']
            acc = Account.query.filter_by(account_id=selected_id).first()
            if acc:
                return redirect(url_for('accounts', acc_id=selected_id))
            flash('Account not found', 'danger')
            return render_template("acc_details.html")
        if 'search' in request.form:
            acc_id = request.form['acc_id']
            if not acc_id:
                cust_id = request.form['cust_id']
                if not cust_id:
                    flash('Please enter either account ID or customer ID', 'danger')
                    return render_template("acc_details.html")
                cust = Customer.query.filter_by(customer_id=cust_id).first()
                if not cust:
                    flash('Customer ID not found', 'danger')
                    return render_template('acc_details.html')
                accounts = Account.query.filter_by(customer_id=cust_id)
                result = accs_schema.dump(accounts)
                return render_template('acc_details.html', result=result)
            acc = Account.query.filter_by(account_id=acc_id).first()
            if acc:
                return redirect(url_for('accounts', acc_id=acc_id))
            flash('Account not found', 'danger')
            return render_template("acc_details.html")
    return render_template('acc_details.html')


# database models

class Userstore(db.Model):
    __tablename__ = 'userstore'
    username = Column(String, primary_key=True, unique=True)
    password = Column(String)
    access = Column(Integer)
    created_date = Column(DateTime, default=datetime.datetime.now)


class Customer(db.Model):
    __tablename__ = 'customer'
    ssn_id = Column(Integer, primary_key=True, unique=True)
    customer_id = Column(Integer, unique=True)
    name = Column(String)
    age = Column(Integer)
    address = Column(String)
    state = Column(String)
    city = Column(String)
    created_date = Column(DateTime, default=datetime.datetime.now)


class Status(db.Model):
    __tablename__ = 'status'
    ssn_id = Column(String, primary_key=True)
    account_id = Column(String)
    account_type = Column(String)
    status = Column(String)
    message = Column(String)
    last_updated = Column(DateTime, default=datetime.datetime.now)


class customerstatus(db.Model):
    __tablename__ = 'customerstatus'
    ssn_id = Column(Integer, primary_key=True, unique=True)
    customer_id = Column(Integer, unique=True)
    status = Column(String)
    message = Column(String)
    last_updated = Column(DateTime, default=datetime.datetime.now)


class accountstatus(db.Model):
    __tablename__ = 'accountstatus'
    customer_id = Column(Integer, primary_key=True, unique=True)
    account_id = Column(Integer, unique=True)
    account_type = Column(String)
    account_status = Column(String)
    message = Column(String)
    last_updated = Column(DateTime, default=datetime.datetime.now)


class Account(db.Model):
    __tablename__ = 'account'
    account_id = Column(String, primary_key=True)
    customer_id = Column(String, unique=True, nullable=False)
    account_type = Column(String)
    deposit_amount = Column(Integer)
    created_date = Column(DateTime, default=datetime.datetime.now)


class Transaction(db.Model):
    __tablename__ = 'transaction'
    trxcn_id = Column(String, primary_key=True)
    account_id = Column(String, db.ForeignKey(
        'account.account_id'), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=True)
    trxcn_date = Column(DateTime, default=datetime.datetime.now)

# ID GENERATORS


def generate_trxcn_id():
    t_id = ''.join(random.choice(string.digits) for _ in range(9))
    trxcn = Transaction.query.filter_by(trxcn_id=t_id).first()
    if trxcn:
        return generate_trxcn_id()
    else:
        return t_id


def generate_customer_Id():
    id = ''.join(random.choice(string.digits) for _ in range(9))
    cust_id = Customer.query.filter_by(customer_id=id).first()
    if cust_id:
        return generate_customer_Id()
    else:
        return id


def generate_account_id():
    id = ''.join(random.choice(string.digits) for _ in range(9))
    account = Account.query.filter_by(account_id=id).first()
    if account:
        return generate_account_id()
    else:
        return id


# helper functions
def add_transaction_id(t_id, acc_id, des, amt, type='source'):
    txcn_obj = Transaction(trxcn_id=t_id, account_id=acc_id,
                           description=des, amount=amt, type=type)
    db.session.add(txcn_obj)
    db.session.commit()


# marsh_mallow schema

class TransactionSchema(ma.Schema):
    class Meta:
        fields = ('trxcn_id', 'account_id',
                  'description', 'amount', 'trxcn_date')


class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('ssn_id', 'customer_id' ,'name', 'email', 'age',
                  'address', 'state', 'city', 'created_date')


class AccountSchema(ma.Schema):
    class Meta:
        fields = ('account_id', 'customer_id', 'account_type', 'type',
                  'deposit_amount', 'created_date')


txn_schema = TransactionSchema()
txns_schema = TransactionSchema(many=True)

acc_schema = AccountSchema()
accs_schema = AccountSchema(many=True)


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


if __name__ == '__main__':
    app.secret_key = 'intern123'
    app.run(debug=True)

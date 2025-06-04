from flask import request, session, render_template, redirect, url_for
from flask import current_app as app
from .models import *
from datetime import datetime
import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# default page/ login page
@app.route('/')
@app.route('/loginPage')
def home():
    msg = request.args.get('msg')
    return render_template('login.html',msg=msg)

# checking for the login credentials and redirecting to respective routes according to their roles
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = User.query.filter_by(email=email, password=password).first()
        except:
            return render_template('login.html',msg = "Login failed. Check credentials.")

        if user:
            # creating a session of the user so that only a single user can be logged in from a particular browser
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard',msg = "Login successful!"))

            elif user.role == 'professional':
                if user.user_status == 'active':
                    return redirect(url_for('professional_dashboard',msg = "Login successful!"))
                elif user.user_status == 'inactive':
                    return render_template('login.html',msg = "Please wait, your account is under approval!")
                elif user.user_status == 'blocked':
                    return render_template('login.html',msg = "Your account has been blocked!")

            elif user.role == 'customer':
                if user.user_status== 'active':
                    return redirect(url_for('customer_dashboard',msg = "Login successful!"))
                elif user.user_status == 'blocked':
                    return render_template('login.html',msg = "Your account has been blocked!")
                
        else:
            return redirect(url_for('home',msg = "Login failed. Check credentials."))

# Route for Signup as Customer
@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'GET':
        return render_template('customer_signup.html')

    if request.method == 'POST':
        try:
            full_name = request.form['full_name'].capitalize()
            email = request.form['email']
            password = request.form['password']
            contact = request.form['contact']
            address = request.form['address'].capitalize()
            pin_code = request.form['pin_code']

            user = User.query.filter_by(email=email).first()
            if user:
                return render_template('customer_signup.html', msg="Email already exists")

            # adding data to user table
            new_user = User(email=email,password=password,role='customer',user_status='active')
            db.session.add(new_user)
            db.session.commit()

            # adding data to customer table
            new_customer = Customer(user_id=new_user.id,full_name=full_name,contact=contact,address=address,pin_code=pin_code)
            db.session.add(new_customer)  
            db.session.commit()  
            
            return redirect(url_for('home',msg = "Account created successfully"))
        except:
            return render_template('customer_signup.html', msg="Some error occured. Please try again." )

# Route for Signup as Professional
@app.route('/professional_signup', methods=['GET', 'POST'])
def professional_signup():
    services = Service.query.all()
    if request.method == 'GET':
        return render_template('professional_signup.html', services=services)

    if request.method == 'POST':
        try:
            full_name = request.form['full_name'].capitalize()
            email = request.form['email']
            password = request.form['password']
            contact = request.form['contact']
            experience = request.form['experience']
            service_id = request.form['service_id']
            address = request.form['address'].capitalize()
            pin_code = request.form['pin_code']


            user = User.query.filter_by(email=email).first()
            if user:
                return render_template('professional_signup.html', msg="Email already exists")

            # adding data to user table
            new_user = User(email=email,password=password,role='professional',user_status='inactive')
            db.session.add(new_user)
            db.session.commit()

            # adding data to professional table
            new_professional = Professional(user_id=new_user.id,contact=contact,full_name=full_name,experience=experience,service_id=service_id,address=address,pin_code=pin_code)
            db.session.add(new_professional)
            db.session.commit()

            return redirect(url_for('home',msg = "Registered successfully, wait for approval"))
        except:
            return render_template('professional_signup.html', msg="Please select a valid service name", services=services)

def check_admin():
    if 'user_id' in session and session['role'] == 'admin': 
        return True
    return False

# Route for Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    services = Service.query.all()
    users = User.query.all()
    professionals = Professional.query.all()
    customers = Customer.query.all()
    packages = Package.query.all()
    service_requests = ServiceRequest.query.all()
    msg = request.args.get('msg')

    return render_template('admin_dash.html',services=services,users=users,professionals=professionals,customers=customers,packages=packages,service_requests=service_requests,msg=msg)


def check_customer():
    if 'user_id' in session and session['role'] == 'customer':
        return True
    return False

# Route for Customer Dashboard
@app.route('/customer_dashboard')
def customer_dashboard():
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        # first checking if the user is blocked
        user = User.query.filter_by(id=session['user_id']).first()
        if user.user_status == 'blocked':
            return render_template('login.html',msg = "Your account has been blocked!")

        customer = user.customer
        services = Service.query.all()
        service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id==user.customer.id).all()
        
        no_package_found = request.args.get('no_package_found') # to give a pop up if there is no package made for a service
        msg= request.args.get('msg')
        
        # for making tables visible only if the have the following data rather than showing empty tables
        req=[] 
        for requests in service_requests:
            req.append(requests.status)

        # for rendering a conditional overlay rating pop up with necessary data
        rating = {} 
        rating['rating_popup']=request.args.get('rating_popup')
        if rating['rating_popup'] == 'True':
            rating['request_id']=request.args.get('request_id')
            rating['professional_name']=ServiceRequest.query.filter(ServiceRequest.id==rating['request_id']).first().professional.full_name
            rating['package_name']=ServiceRequest.query.filter(ServiceRequest.id==rating['request_id']).first().package.package_name
        
        return render_template('customer_dash.html',customer=customer,services=services,service_requests=service_requests,no_package_found=no_package_found,req=req,rating=rating,msg=msg)
        
    except:
        return redirect(url_for('home',msg = "Your account has been deleted!"))

def check_professional():
    if 'user_id' in session and session['role'] == 'professional':
        return True
    return False

# Route: Professional Dashboard
@app.route('/professional_dashboard')
def professional_dashboard():
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        # first checking if the user is blocked
        user = User.query.filter_by(id=session['user_id']).first()
        if user.user_status == 'blocked':
            return render_template('login.html',msg = "Your account has been blocked!")

        professional = user.professional

        # to check for any new requests for any service 
        package_ids = []
        for package in professional.service.packages:
            package_ids.append(package.id)
        service_requests = []
        for requests in ServiceRequest.query.filter_by(status='requested').all():
            if requests.package_id in package_ids:
                service_requests.append(requests)
        avail = False
        for requests in service_requests:
            if requests.status == 'requested':
                avail = True
                break
        
        # for making tables visible only if the have the following data rather than showing empty tables
        req=[]
        for requests in professional.requests:
            req.append(requests.status)
            
        msg = request.args.get('msg')

        return render_template('professional_dash.html',professional=professional,service_requests=service_requests,req=req,avail=avail,msg=msg)
        
    except:
        return redirect(url_for('home',msg = "Your account has been deleted!"))

# Route for Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home',msg = "Logged out successfully"))


#************Admin controlls************#

# Adding a new service
@app.route('/admin/add_service', methods=['GET', 'POST'])
def add_service():
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    if request.method == 'GET':
        return render_template('add_service.html')
    
    if request.method == 'POST':
        service_name = request.form['service_name']
        
        services = Service.query.filter_by(service_name=service_name).all()
        if services:
            return render_template('add_service.html', msg='Service name already exists')

        new_service = Service(service_name=service_name)
        db.session.add(new_service)
        db.session.commit()
        return render_template('add_service.html', msg='Service added successfully')


@app.route("/admin/edit_service/<int:service_id>", methods=["GET", "POST"])
def edit_service(service_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    service = Service.query.get(service_id)
    if request.method == "GET":
        return render_template("edit_service.html", service=service)
    
    if request.method == "POST":
        service.service_name = request.form["service_name"]
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_service/<int:service_id>", methods=["GET", "POST"])
def delete_service(service_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    if request.method == "GET":
        service = Service.query.filter_by(id=service_id).first()
        db.session.delete(service)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    
@app.route("/admin/add_package", methods=["GET", "POST"])
def add_package():
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    services = Service.query.all()
    if request.method == "GET":
        service_id = request.args.get("service_id")

        if service_id:
            service = Service.query.get(service_id)
            return render_template("add_package.html", service=service)
        
        else:
            return render_template("add_package.html", services=services)
        
    if request.method == "POST":
        try:
            service_id = request.form["service_id"]
            package_name = request.form["package_name"]
            price = request.form["price"]

        except:
            return render_template("add_package.html",msg="Some error occured, please enter again",services=services)

        new_package = Package(service_id=service_id, package_name=package_name, price=price)
        db.session.add(new_package)
        db.session.commit()
        return render_template("add_package.html", msg="Package added successfully",services=services)

@app.route("/admin/edit_package/<int:package_id>", methods=["GET", "POST"])
def edit_package(package_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    package = Package.query.get(package_id)
    services = Service.query.all()
    if request.method == "GET":
        return render_template("edit_package.html", services=services, package=package)
    
    if request.method == "POST":
        try:
            package.package_name = request.form["package_name"]
            package.price = request.form["price"]
        except:
            return render_template("edit_package.html",msg="Some error occured, please enter again",services=services, package=package)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_package/<int:package_id>", methods=["GET", "POST"])
def delete_package(package_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    if request.method == "GET":
        package = Package.query.filter_by(id=package_id).first()
        db.session.delete(package)
        db.session.commit()
        return redirect(url_for("admin_dashboard")) 

@app.route("/admin/block_user/<int:user_id>", methods=["GET"])
def block_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    if request.method == "GET":
        user = User.query.get(user_id)
        user.user_status = "blocked"
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route("/admin/unblock_user/<int:user_id>", methods=["GET"])
def unblock_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
    
    if request.method == "GET":
        user = User.query.get(user_id)
        user.user_status = "active"
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
    
    user = User.query.get(user_id)
    if request.method == 'GET':

        if user.role == "customer":
            db.session.delete(user.customer)

        elif user.role == "professional":
            db.session.delete(user.professional)

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route('/admin/approve_user/<int:user_id>')
def approve_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
    
    if request.method=='GET':
        user=User.query.get(user_id)
        user.user_status = "active"
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

@app.route('/admin/reject_user/<int:user_id>')
def reject_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))

    if request.method=='GET':
        user=User.query.get(user_id)
        user.user_status = "rejected"
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

# admin can got to the admin view pages for particulars by clicking the view id button
@app.route("/admin/view/<item>",methods=["GET"])
def admin_view(item):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
        
    if request.method == "GET":

        if item == "customers":
            try:
                customer_id = request.args.get('customer_id')
                user = User.query.get(customer_id)
                customer = user.customer

            except:
                return redirect(url_for("admin_dashboard"))
            return render_template("admin_view.html",customer_id=customer_id,customer=customer)

        elif item == "professionals":
            try:
                professional_id = request.args.get('professional_id')
                user = User.query.get(professional_id)
                professional = user.professional

            except:
                return redirect(url_for("admin_dashboard"))
            return render_template("admin_view.html",professional_id=professional_id,professional=professional)

        elif item == "services":
            try:
                service_id=request.args.get('service_id')
                service = Service.query.get(service_id)
                package_ids = []
                for package in service.packages:
                    package_ids.append(package.id)
                service_requests = []
                for requests in ServiceRequest.query.all():
                    if requests.package_id in package_ids:
                        service_requests.append(requests)
            except:
                return redirect(url_for("admin_dashboard"))
            return render_template("admin_view.html",service_id=service_id,service=service,service_requests=service_requests)

        elif item == "packages":
            try:
                package_id=request.args.get('package_id')
                package = Package.query.get(package_id)
            except:
                return redirect(url_for("admin_dashboard"))
            return render_template("admin_view.html",package_id=package_id,package=package)
        
    return redirect(url_for("admin_dashboard"))

# to handle block from the admin view page
@app.route("/admin/view/block_user/<int:user_id>",methods=["GET"])
def view_block_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
        
    if request.method == "GET":
        user = User.query.get(user_id)
        user.user_status = "blocked"
        db.session.commit()

        if user.role == "customer":
            return redirect(f"/admin/view/customers?customer_id={user.id}")
        
        elif user.role == "professional":
            return redirect(f"/admin/view/professionals?professional_id={user.id}")

# to handle unblock from the admin view page
@app.route("/admin/view/unblock_user/<int:user_id>",methods=["GET"])
def view_unblock_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
        
    if request.method == "GET":
        user = User.query.get(user_id)
        user.user_status = "active"
        db.session.commit()

        if user.role == "customer":
            return redirect(f"/admin/view/customers?customer_id={user.id}")
        
        elif user.role == "professional":
            return redirect(f"/admin/view/professionals?professional_id={user.id}")
    
# to approve a professional from the admin view page
@app.route('/admin/view/approve_user/<int:user_id>',methods=["GET"])
def view_approve_user(user_id):
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
        
    if request.method=='GET':
        user=User.query.get(user_id)
        user.user_status = "active"
        db.session.commit()
        return redirect(f"/admin/view/professionals?professional_id={user.id}")

@app.route("/admin/search", methods=["GET", "POST"])
def admin_search():
    if check_admin() == False:
        return redirect(url_for('home',msg="You are not logged in as an admin!"))
        
    if request.method == "GET":
        return render_template("admin_search.html")
    
    if request.method == "POST":
        search_by = request.form.get("search_by")
        search_txt = request.form.get("search_txt")
        if not search_by:
            return render_template("admin_search.html", msg="Please select a search option !!")

        data = {}
        data['search_by'] = search_by
        data['search_txt'] = search_txt

        if search_by == "customer":
            customers = Customer.query.join(User).filter(Customer.full_name.contains(search_txt) | Customer.user_id.contains(search_txt) | User.user_status.contains(search_txt)).all()
            return render_template("admin_search.html", customers=customers,searching=True, data=data)

        elif search_by == "professional":
            professionals = Professional.query.join(User).join(Service).filter(Professional.full_name.contains(search_txt) | Professional.user_id.contains(search_txt) | User.user_status.contains(search_txt) | Service.service_name.contains(search_txt)).all()
            return render_template("admin_search.html", professionals=professionals,searching=True, data=data)

        elif search_by == "service":
            services = Service.query.filter(Service.service_name.contains(search_txt) | Service.id.contains(search_txt)).all()
            return render_template("admin_search.html", services=services,searching=True, data=data)

        elif search_by == "package":
            packages = Package.query.join(Service).filter(Package.package_name.contains(search_txt) | Package.id.contains(search_txt) | Service.service_name.contains(search_txt)).all()
            return render_template("admin_search.html", packages=packages,searching=True, data=data)

        elif search_by == "request":
            requests = ServiceRequest.query.join(Package).join(Service).filter(ServiceRequest.status.contains(search_txt) | ServiceRequest.id.contains(search_txt) | Service.service_name.contains(search_txt) | Package.package_name.contains(search_txt)| ServiceRequest.rating.contains(search_txt)).all()
            return render_template("admin_search.html", requests=requests,searching=True, data=data)

        else:
            return render_template("admin_search.html")


#************ Professional controlls ************#


@app.route("/professional/<int:professional_id>/accept_request/<int:request_id>",methods=["GET"])
def accept_request(request_id, professional_id):
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.professional.id != professional_id:
            return redirect(url_for('home', msg="You are not logged in as the right professional!")) 
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            req = ServiceRequest.query.get(request_id)

            # if multiple professionals see the request same time, and if one of them rejects, but the other professional stills sees options to accept or reject if he hasnt refreshed the page, so he can still accept the request. 
            if req.status == "requested" or req.status == "rejected": 
                req.status = "accepted"
                req.professional_id = professional_id
                db.session.commit()

            else:
                # but if the request is accepted by the first prof, then it shows this
                return 'service already accepted by other professionals'
            
            return redirect(url_for("professional_dashboard"))
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))


@app.route("/professional/<int:professional_id>/reject_request/<int:request_id>",methods=["GET"])
def reject_request(request_id,professional_id):
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.professional.id != professional_id:
            return redirect(url_for('home', msg="You are not logged in as the right professional!")) 
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            req = ServiceRequest.query.get(request_id)

            # if someone has already reject or not, any professional who can see the request can again reject a request
            if req.status == "requested" or req.status == "rejected":
                req.status = "rejected"
                req.professional_id = professional_id
                db.session.commit()
            return redirect(url_for("professional_dashboard"))

    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))


@app.route("/professional/close_request/<int:request_id>",methods=["GET"])
def close_request(request_id):
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            req = ServiceRequest.query.get(request_id)

            if req.status == "accepted":
                req.status = "completed"
                req.date_of_complete = datetime.now()
                db.session.commit()
            return redirect(url_for("professional_dashboard"))

    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/professional_profile",methods=["GET"])
def professional_profile():
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            user = User.query.get(user.id)
            professional=user.professional
            return render_template("professional_profile.html",professional=professional)
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))
    
@app.route("/professional_profile_edit",methods=["GET","POST"])
def professional_profile_edit():
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        professional = user.professional

        if request.method == "GET":
            return render_template("professional_profile_edit.html",professional=professional)
        
        if request.method == "POST":
            professional.full_name = request.form['full_name']
            professional.user.password = request.form['password']
            professional.contact = request.form['contact']
            professional.address = request.form['address']
            professional.pin_code = request.form['pin_code']
            db.session.commit()
            return redirect(url_for("professional_profile"))
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/professional/view/<item>",methods=["GET"])
def professional_view(item):
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":

            if item == "packages":
                try:
                    package_id = request.args.get('package_id')
                    package = Package.query.get(package_id)
                    professional = user.professional
                    requests = ServiceRequest.query.filter(ServiceRequest.package_id==package.id, ServiceRequest.professional_id==professional.id).all()

                except:
                    return redirect(url_for("professional_dashboard"))
                return render_template("professional_view.html",package=package,requests=requests,package_id=package_id)
            
            elif item == "customers":
                try:
                    customer_id = request.args.get('customer_id')
                    customer = Customer.query.filter_by(user_id=customer_id).first()
                    user = User.query.filter_by(id=session['user_id']).first()
                    professional = user.professional
                    requests = ServiceRequest.query.filter(ServiceRequest.customer_id==customer.id, ServiceRequest.professional_id==professional.id).all()

                except:
                    return redirect(url_for("professional_dashboard"))
                return render_template("professional_view.html",customer_id=customer_id,customer=customer,requests=requests)
            
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/professional/search",methods=["GET","POST"])
def professional_search():
    try:
        if check_professional() == False:
            return redirect(url_for('home', msg="You are not logged in as a professional!"))
        user = User.query.get(session['user_id'])
        if user.user_status == 'blocked':
            return render_template('login.html',msg = "Your account has been blocked!")

        if request.method == "GET":
            return render_template("professional_search.html")

        professional = user.professional
        if request.method == "POST":
            search_by = request.form.get("search_by")
            search_txt = request.form.get("search_txt")
            
            if not search_by:
                return render_template("professional_search.html", msg="Please select a search option !!")

            data = {}
            data['search_by'] = search_by
            data['search_txt'] = search_txt
            try:
                if search_by == "customer":
                    customers = Customer.query.join(ServiceRequest).filter(ServiceRequest.professional_id == professional.id,Customer.full_name.contains(search_txt) | Customer.user_id.contains(search_txt) | Customer.pin_code.contains(search_txt)).all() 
                    return render_template("professional_search.html", customers=customers,searching=True, data=data)

                elif search_by == "service":
                    services = Service.query.filter(Service.service_name.contains(search_txt) | Service.id.contains(search_txt)).all()
                    return render_template("professional_search.html", services=services,searching=True, data=data)

                elif search_by == "package":
                    packages = Package.query.filter(Package.service_id == professional.service_id,Package.package_name.contains(search_txt) | Package.id.contains(search_txt)).all()
                    return render_template("professional_search.html", professional=professional, packages=packages,searching=True, data=data)

                elif search_by == "request":
                    requests = ServiceRequest.query.filter(ServiceRequest.professional_id == professional.id,ServiceRequest.status.contains(search_txt) | ServiceRequest.id.contains(search_txt)).all()
                    return render_template("professional_search.html", requests=requests,searching=True, data=data)

            except:
                return render_template("professional_search.html", msg="No results found !!")

    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))


#************ Customer controlls ************#

        
@app.route("/customer/<int:customer_id>/request_service/<int:service_id>",methods=["GET"])
def request_service(customer_id,service_id):
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.customer.id != customer_id:
            return redirect(url_for('home', msg="You are not logged in as the right customer!")) 
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":

            packages = Package.query.join(Service).filter(Package.service_id==service_id).all()
            if not packages:
                return redirect('/customer_dashboard?no_package_found=True')
            
            else:
                no_professional_found = request.args.get('no_professional_found')
                return render_template("choose_package.html",packages=packages,customer_id=customer_id,no_professional_found=no_professional_found)
            
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))
    
@app.route("/customer/<int:customer_id>/request_package/<int:package_id>",methods=["GET"])
def request_package(customer_id,package_id):
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.customer.id != customer_id:
            return redirect(url_for('home', msg="You are not logged in as the right customer!")) 
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            package = Package.query.get(package_id)
            professionals = Professional.query.join(User).filter(Professional.service_id==package.service_id,User.user_status=="active").all()  
            
            if not professionals:
                return redirect(f'/customer/{customer_id}/request_service/{package.service_id}?no_professional_found=True')
            
            else:
                req = ServiceRequest(customer_id=customer_id,package_id=package_id)
                db.session.add(req)
                db.session.commit()
            
            return redirect(url_for("customer_dashboard",msg="Request sent successfully!"))
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/customer/<int:customer_id>/cancel_request/<int:request_id>",methods=["GET"])
def cancel_request(customer_id,request_id):
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.customer.id != customer_id:
            return redirect(url_for('home', msg="You are not logged in as the right customer!")) 
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            req = ServiceRequest.query.get(request_id)
            req.status = "cancelled"
            db.session.commit()
            return redirect(url_for("customer_dashboard",msg="Request Cancelled!"))
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/customer_rating/<int:request_id>",methods=["GET","POST"])
def customer_rating(request_id):
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        req = ServiceRequest.query.get(request_id)
        if request.method == "GET":
            return redirect(url_for("customer_dashboard",rating_popup=True,request_id=request_id))
        
        if request.method == "POST":
            try:
                req.rating = request.form['rating']
                db.session.commit()
                return redirect(url_for("customer_dashboard"))
            
            except:
                return redirect(url_for("customer_dashboard"))
            
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/customer_profile",methods=["GET"])
def customer_profile():
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        
        if request.method == "GET":
            customer=user.customer
            return render_template("customer_profile.html",customer=customer)
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/customer_profile_edit",methods=["GET","POST"])
def customer_profile_edit():
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")

        customer = user.customer
        if request.method == "GET":
            return render_template("customer_profile_edit.html",customer=customer)

        if request.method == "POST":    
            customer.full_name = request.form['full_name']
            customer.user.password = request.form['password']
            customer.contact = request.form['contact']
            customer.address = request.form['address']
            customer.pin_code = request.form['pin_code']
            db.session.commit()
            return redirect(url_for("customer_profile"))
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))
    
@app.route("/customer/view/<item>",methods=["GET"])
def customer_view(item):
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")

        if request.method == "GET":

            if item == "packages":
                try:
                    package_id = request.args.get('package_id')
                    package = Package.query.get(package_id)
                    requests = ServiceRequest.query.filter(ServiceRequest.package_id==package.id, ServiceRequest.customer_id==user.customer.id).all()

                except:
                    return redirect(url_for("customer_dashboard"))
                return render_template("customer_view.html",package=package,requests=requests,package_id=package_id)

    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))

@app.route("/customer/search",methods=["GET","POST"])
def customer_search():
    try:
        if check_customer() == False:
            return redirect(url_for('home', msg="You are not logged in as a customer!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")

        if request.method == "GET":
            return render_template("customer_search.html")

        customer = user.customer
        if request.method == "POST":
            search_by = request.form.get("search_by")
            search_txt = request.form.get("search_txt")
            
            if not search_by:
                return render_template("customer_search.html", msg="Please select a search option !!")

            data = {}
            data['search_by'] = search_by
            data['search_txt'] = search_txt

            if search_by == "service":
                services = Service.query.filter(Service.service_name.contains(search_txt) | Service.id.contains(search_txt)).all()
                return render_template("customer_search.html", services=services,searching=True, data=data,customer=customer)
            
            elif search_by == "package":
                packages = Package.query.join(Service).filter(Package.package_name.contains(search_txt) | Package.id.contains(search_txt) | Service.service_name.contains(search_txt)).all()
                return render_template("customer_search.html", packages=packages,searching=True, data=data)
            
            elif search_by == "request":
                requests = ServiceRequest.query.join(Package).join(Service).filter(ServiceRequest.customer_id==customer.id)
                requests = requests.filter(ServiceRequest.id.contains(search_txt) | ServiceRequest.status.contains(search_txt) | Package.package_name.contains(search_txt) | Service.service_name.contains(search_txt)).all()
                return render_template("customer_search.html", requests=requests,searching=True, data=data)
            
            else:
                return render_template("customer_search.html") 
            
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))


# summary graphs and charts

@app.route("/summary/<item>")
def summary_page(item):
    try:
        if 'user_id' not in session:
            return redirect(url_for('home', msg="You are not logged in!"))
        user = User.query.get(session['user_id'])
        if user.user_status == "blocked":
            return render_template('login.html',msg = "Your account has been blocked!")
        if 'user_id' not in session or user.role != item:
            return redirect(url_for("home",msg = "You are not authorized to view this page!"))
            
        ratings = {'1':0,'2':0,'3':0,'4':0,'5':0,'Not Rated':0}
        if item == "admin":
            requested_count = ServiceRequest.query.filter_by(status='requested').count()
            accepted_count = ServiceRequest.query.filter_by(status='accepted').count()
            completed_count = ServiceRequest.query.filter_by(status='completed').count()
            rejected_count = ServiceRequest.query.filter_by(status='rejected').count()
            cancelled_count = ServiceRequest.query.filter_by(status='cancelled').count()

            # for summary variables
            total_services = Service.query.count()
            total_requests = ServiceRequest.query.count()
            total_completed = completed_count

            users = {}
            users['customer']=Customer.query.count()
            users['professional']=Professional.query.count()
            total_users = users['customer'] + users['professional']

            service_requests = ServiceRequest.query.filter_by(status='completed')
            for service_request in service_requests:
                if service_request.rating == None:
                    ratings["Not Rated"] += 1
                else:
                    ratings[str(service_request.rating)]=ratings[str(service_request.rating)]+1            

            services={}
            for service in Service.query.all():
                services[service.service_name]=0
            for service_request in ServiceRequest.query.all():
                services[service_request.package.service.service_name] +=1
            keys = list(services.keys())
            for service in keys:
                if services[service] == 0:
                    services.pop(service)

        elif item == "customer":
            customer = user.customer
            requested_count = ServiceRequest.query.filter_by(status='requested',customer_id=customer.id).count()
            accepted_count = ServiceRequest.query.filter_by(status='accepted',customer_id=customer.id).count()
            completed_count = ServiceRequest.query.filter_by(status='completed',customer_id=customer.id).count()
            rejected_count = ServiceRequest.query.filter_by(status='rejected',customer_id=customer.id).count()
            cancelled_count = ServiceRequest.query.filter_by(status='cancelled',customer_id=customer.id).count()

            # for summary variables
            total_requests = ServiceRequest.query.filter_by(customer_id=customer.id).count()
            total_completed = completed_count
            total_pending = accepted_count

            service_requests = ServiceRequest.query.filter_by(customer_id=customer.id, status='completed').all()
            for service_request in service_requests:
                if service_request.rating == None:
                    ratings["Not Rated"] += 1
                else:
                    ratings[str(service_request.rating)]=ratings[str(service_request.rating)]+1

        elif item == "professional":
            requested_count = None
            accepted_count = ServiceRequest.query.filter_by(status='accepted',professional_id=user.professional.id).count()
            completed_count = ServiceRequest.query.filter_by(status='completed',professional_id=user.professional.id).count()
            rejected_count = ServiceRequest.query.filter_by(status='rejected',professional_id=user.professional.id).count()
            cancelled_count = ServiceRequest.query.filter_by(status='cancelled',professional_id=user.professional.id).count()

            # for summary variables
            total_requests = ServiceRequest.query.filter_by(professional_id=user.professional.id).count()
            total_completed = completed_count
            total_pending = accepted_count

            service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id==user.professional.id, ServiceRequest.status.contains('completed')).all()
            for service_request in service_requests:
                if service_request.rating == None:
                    ratings["Not Rated"] += 1
                else:
                    ratings[str(service_request.rating)]=ratings[str(service_request.rating)]+1
        
        # graph for status
        if total_requests > 0:
            if item == "customer" or item == "admin":
                statuses = ['Requested', 'Accepted', 'Completed', 'Rejected', 'Cancelled']
                counts = [requested_count, accepted_count, completed_count, rejected_count, cancelled_count]
                color_list=['skyblue', 'orange', 'green', 'salmon', 'red']
            else:
                statuses = ['Accepted', 'Completed', 'Rejected', 'Cancelled']
                counts = [accepted_count, completed_count, rejected_count, cancelled_count]
                color_list = ['orange', 'green', 'salmon', 'red']
            
            plt.figure(figsize=(7, 4))
            plt.bar(statuses, counts, color=color_list, width=0.5)
            plt.xlabel('Status')
            plt.ylabel('Count')
            plt.title(f'Summary of Service Requests')
            status_graph_path = "static/images/status_chart.png"
            plt.savefig(status_graph_path)
            plt.close() 
        
        # graph for ratings
        if total_completed > 0:
            plt.figure(figsize=(7, 4))
            plt.bar(ratings.keys(), ratings.values(), color='skyblue', width=0.5)
            plt.xlabel('Status')
            plt.ylabel('Count')
            plt.title(f'Summary of overall Ratings by Customers ')
            rating_graph_path = "static/images/ratings_chart.png"
            plt.savefig(rating_graph_path)
            plt.close() 

        if item == "admin":
            # graph for users
            if total_users == 0:
                pass
            else:
                plt.figure(figsize=(7, 4))
                plt.pie(users.values(), labels=users.keys(), autopct= lambda p: f'{p:.0f}% ({int(p*total_users/100)})', colors=['lightgreen', 'salmon'])
                plt.title(f'Summary of Users ratio')
                users_graph_path ="static/images/users_chart.png"
                plt.savefig(users_graph_path)
                plt.close()

            # graph for services
            if total_requests == 0:
                pass
            else:
                plt.figure(figsize=(7, 4))
                plt.pie(services.values(), labels=services.keys(), autopct=lambda p: f'{p:.0f}% ({int(p*sum(services.values())/100)})')
                plt.title(f'Summary of Total Services booked by Customers ')
                services_graph_path = "static/images/services_chart.png"
                plt.savefig(services_graph_path)
                plt.close()

        # summary variables
        if item == "admin":
            summary = {"Total users":total_users, "Total services":total_services, "Total requests":total_requests, "Total completed":total_completed}
        elif item == "customer":
            summary = {"Total requests by you":total_requests, "Total completed":total_completed, "Total pending":total_pending}
        elif item == "professional":
            summary = {"Total requests to you":total_requests, "Total completed":total_completed, "Total pending":total_pending}

        return render_template("summary.html",item=item, summary=summary)
        
    except:
        return redirect(url_for("home",msg="Your account has been deleted!"))
    
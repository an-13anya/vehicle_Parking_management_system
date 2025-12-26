from flask import Flask,render_template,request,redirect,url_for,session,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime ,timedelta
import pymysql
import math
pymysql.install_as_MySQLdb()

app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:@localhost:3306/vehicle_db'
db = SQLAlchemy(app)
app.secret_key = b'[_5#y2L"F4Q8z\n\xec]/'


class Tasks(db.Model):
    __tablename__='vehicleEntry'
    id= db.Column(db.Integer, primary_key=True)
    slot_no= db.Column(db.Integer,nullable=False)
    VehicleNum= db.Column(db.String(80),nullable=False)
    VehicleTyp= db.Column(db.String(80),nullable=False)
    status= db.Column(db.String(20),default="parked")
    entry_time=db.Column(db.DateTime,default=datetime.utcnow)
    exit_time=db.Column(db.DateTime,default=datetime.utcnow)
    amount=db.Column(db.Float,default=0,nullable=True)
class Admin(db.Model):
     __tablename__='admin'
     id= db.Column(db.Integer, primary_key=True)
     username= db.Column(db.String(80),unique=True,nullable=False)
     password= db.Column(db.String(80),nullable=False)

@app.route("/",methods=["Get","Post"])
def login():
      if (request.method=='POST'):
        #Add entry to the database
         username= request.form.get("username")
         password=request.form.get("password")
         admin=Admin.query.filter_by( username=username,password=password).all()
         if admin:
             session["is_admin"]=True
             return redirect(url_for("dashboard"))
         else:
             flash("Invalid Credentials.Try again.","danger")
             return  redirect(url_for("login"))

      return render_template('vehicle_log.html')

@app.route("/dashboard",methods=["Get","Post"])
def dashboard():
    if  session.get("is_admin"):
        if (request.method=='POST'):
          VehicleNum=request.form.get("VehicleNum")
          VehicleTyp=request.form.get("VehicleTyp")
          booked_slots=[]
          available_slots=[]
         
          already_exit=Tasks.query.filter_by(VehicleNum=VehicleNum,status="parked").all()
          if already_exit:
              flash("This vehicle is already parked!","danger")
              return redirect(url_for("dashboard"))
          #slot allocation logic
          else:
              for v in Tasks.query.filter_by(status="parked").all():
                    booked_slots.append(v.slot_no)
              total_slots=20
              for i in range (1,total_slots+1):
                    if i not in booked_slots:
                      available_slots.append(i)
              if not available_slots:
                   flash("Slots are full!","danger")
                   return redirect(url_for("dashboard"))
              new_slot=Tasks(VehicleNum=VehicleNum,VehicleTyp=VehicleTyp,slot_no=available_slots[0])
              db.session.add(new_slot)
              db.session.commit()
              flash(f"Vehicle {VehicleNum} successfully parked in slot {available_slots[0]}","success")
              return redirect(url_for("dashboard"))
        tasks=Tasks.query.filter_by(status="parked").all()
        reports=Tasks.query.filter_by(status="exited").all()
        revenue=0
        for a in reports:
                  if a.amount:
                     revenue+=a.amount
        
        booked=len(tasks)
        available=20-booked
        return render_template('dashboard.html',tasks=tasks,reports=reports,booked=booked, available= available,revenue=revenue,timedelta=timedelta)
    else:
        return redirect(url_for("login"))

@app.route("/vehicleExit",methods=["Post"])
def VExit():
     rates={"Two Wheeler":1,"Three Wheeler":2,"Four Wheeler":3,"Heavy Vehicle":5,"Special Vehicle":0}
     if (request.method=='POST'):
          VehicleNum=request.form.get("VehicleNum")
          VehicleTyp=request.form.get("VehicleTyp")
          vehicle=Tasks.query.filter_by(VehicleNum=VehicleNum,VehicleTyp=VehicleTyp,status="parked").first()
          if vehicle:
              vehicle.exit_time=datetime.utcnow()
              vehicle.status="exited"
              duration=((vehicle.exit_time-vehicle.entry_time).total_seconds())/60
              r=rates.get(vehicle.VehicleTyp,1)
              vehicle.amount=math.ceil(duration)*r
              db.session.commit()
              flash(f"Vehicle {VehicleNum} has exited  successfully . Total Amount:{vehicle.amount}rs","success")
              return(redirect(url_for("dashboard")))
          else:
             flash(f"No parked vehicle found with this number and type","danger")
             return(redirect(url_for("dashboard")))

@app.route("/delete/<int:id>")
def delete(id):
      task_to_delete=Tasks.query.filter_by(id=id,status="exited").first()
      db.session.delete(task_to_delete)
      db.session.commit()
      return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
      session.pop("is_admin",None)
      return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)
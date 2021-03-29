from app import db
db.metadata.clear()
class Courier(db.Model):

    courier_id = db.Column(db.Integer, primary_key = True)
    courier_type = db.Column(db.String)
    regions = db.relationship('Region', lazy='dynamic')
    working_hours = db.relationship('WorkingHours', lazy='dynamic')
    previous_order_time = db.relationship('PrevTime', lazy='dynamic')


    def __repr__(self):
        return '<Courier %r>' % (self.courier_id)

class WorkingHours(db.Model):
    hours_idx = db.Column(db.Integer, primary_key=True)
    hours = db.Column(db.String)
    hours_c_id = db.Column(db.Integer, db.ForeignKey('courier.courier_id'))

    def __repr__(self):
        return str(self.hours)

class Region(db.Model):
    reg_idx = db.Column(db.Integer, primary_key=True)
    reg = db.Column(db.Integer)
    reg_c_id = db.Column(db.Integer, db.ForeignKey('courier.courier_id'), unique=False)
    reg_summ_time = db.Column(db.Integer, default=0)
    reg_orders_amount = db.Column(db.Integer, default=0)
    def __repr__(self):
        return str(self.reg)


class PrevTime(db.Model):
    pt_idx = db.Column(db.Integer, primary_key=True)
    pt_c_id = db.Column(db.Integer, db.ForeignKey('courier.courier_id'), unique=False)
    pt_reg = db.Column(db.Integer)
    pt_time = db.Column(db.String)
    pt_ord_id = db.Column(db.Integer)
    def __repr__(self):
        return str(self.pt_time)


class Order(db.Model):

    order_id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    region = db.Column(db.Integer)
    stage = db.Column(db.String, default='Free')
    delivery_hours = db.relationship('DeliveryHours', lazy='dynamic')

    def __repr__(self):
        return str(self.order_id)

class DeliveryHours(db.Model):

    dev_hrs_idx = db.Column(db.Integer, primary_key=True)
    hours = db.Column(db.String)
    ord_id = db.Column(db.Integer, db.ForeignKey('order.order_id'))

    def __repr__(self):
        return (self.hours)
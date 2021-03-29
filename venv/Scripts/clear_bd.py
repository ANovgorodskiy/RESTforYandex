from app import models
from app import db
couriers = models.Courier.query.all()
for c in couriers:
    db.session.delete(c)
orders = models.Order.query.all()
for c in orders:
    db.session.delete(c)
d = models.DeliveryHours.query.all()
for c in d:
    db.session.delete(c)
d = models.WorkingHours.query.all()
for c in d:
    db.session.delete(c)
d = models.Region.query.all()
for c in d:
    db.session.delete(c)
d = models.PrevTime.query.all()
for c in d:
    db.session.delete(c)
db.session.commit()
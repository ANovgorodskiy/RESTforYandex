from app import app, models
from flask import Flask, request, make_response, jsonify, Response, abort
from sqlalchemy import or_
import json
from datetime import datetime
app.url_map.strict_slashes = False


def time_check(courier_time, order_time, assign_time):
    sec_assign_time = int(assign_time[:2]) * 3600 + int(assign_time[3:5]) * 60 + int(assign_time[6:8])
    flag = False
    for el in courier_time:
        el = str(el)
        if int(el[6:8])*3600 + int(el[9:11])*60 >= sec_assign_time >= int(el[:2])*3600 + int(el[3:5])*60:

            flag = True
    if flag:
        for c_time in courier_time:
            c_time = str(c_time)
            for o_time in order_time:
                o_time = str(o_time)
                ord_start = int(o_time[:2]) * 3600 + int(o_time[3:5]) * 60
                ord_end = int(o_time[6:8]) * 3600 + int(o_time[9:11]) * 60
                c_start = int(c_time[:2]) * 3600 + int(c_time[3:5]) * 60
                c_end = int(c_time[6:8]) * 3600 + int(c_time[9:11]) * 60
                if not (ord_start > c_end or c_start > ord_end):
                    if sec_assign_time < min(c_end, ord_end):
                        return True
    else:
        return False


def time_check_for_update(courier_time, order_time):
    for c_time in courier_time:
        c_time = str(c_time)
        for o_time in order_time:
            o_time = str(o_time)
            ord_start = int(o_time[:2]) * 3600 + int(o_time[3:5]) * 60
            ord_end = int(o_time[6:8]) * 3600 + int(o_time[9:11]) * 60
            c_start = int(c_time[:2]) * 3600 + int(c_time[3:5]) * 60
            c_end = int(c_time[6:8]) * 3600 + int(c_time[9:11]) * 60
            if not (ord_start > c_end or c_start > ord_end):
                return True
    return False






@app.route('/app/couriers/', methods=['POST'])
def couriers():
    info = (request.get_json(force=True))
    returner_valid = {"couriers":[]}
    returner_invalid = {'validation_error':{'couriers' : []}}
    checker = ["courier_type","regions","working_hours"]
    for el in info['data']:
        for part in checker:
            if part not in el.keys():
                if el['courier_id'] not in returner_invalid['validation_error']['couriers']:
                    returner_invalid['validation_error']['couriers'].append({'id':el['courier_id']})
        if not len(returner_invalid['validation_error']['couriers']) or el['courier_id'] != returner_invalid['validation_error']['couriers'][-1]['id']:
            c_id,c_type , c_regs, time_str  = el['courier_id'],el['courier_type'],el['regions'], el['working_hours']
            into_courier = models.Courier(courier_id=c_id, courier_type=c_type)
            returner_valid['couriers'].append({'id' : c_id})
            models.db.session.add(into_courier)

            for i in range(len(c_regs)):
                into_reg = models.Region(reg=c_regs[i], reg_c_id=c_id)
                models.db.session.add(into_reg)

            for i in range(len(time_str)):
                into_hrs = models.WorkingHours(hours=time_str[i], hours_c_id=c_id)
                models.db.session.add(into_hrs)
    if not returner_invalid['validation_error']['couriers']:
        models.db.session.commit()
        return Response(response= 'HTTP 201 Created\n'+ json.dumps(returner_valid), status='201 Created')
    else:
        return Response(response= 'HTTP 400 Bad Request\n'+ json.dumps(returner_invalid), status='400 Bad Request')


@app.route('/app/couriers/<int:idx>/', methods=['PUT'])
def update_courier(idx):
    to_update = (request.get_json(force=True))
    courier = models.Courier.query.get(idx)
    if not courier:
        return Response(status=404)
    if 'courier_type' in to_update.keys():
        if to_update['courier_type']:
            courier.courier_type = to_update['courier_type']
        else:
            return 'HTTP 400 Bad Request', 400
    if 'regions' in to_update.keys():
        if to_update['regions']:
            models.Region.query.filter(models.Region.reg_c_id==idx and 2 == 2).delete()
            for i in range(len(to_update['regions'])):
                into_reg = models.Region(reg=to_update['regions'][i], reg_c_id=idx)
                models.db.session.add(into_reg)
        else:
            return 'HTTP 400 Bad Request', 400
    if 'working_hours' in to_update.keys():
        if to_update['working_hours']:
            models.WorkingHours.query.filter(models.WorkingHours.hours_c_id==idx).delete()
            for i in range(len(to_update['working_hours'])):
                into_hours = models.WorkingHours(hours=to_update['working_hours'][i], hours_c_id=idx)
                models.db.session.add(into_hours)
        else:
            return 'HTTP 400 Bad Request', 400
    models.db.session.commit()
    returner = {
        "courier_id": courier.courier_id,
        "courier_type": courier.courier_type,
        "regions": str(courier.regions.all()),
        "working_hours": str(courier.working_hours.all())}
    if courier.courier_type == 'auto':
        weight_available = 50
    elif courier.courier_type == 'bike':
        weight_available = 15
    else:
        weight_available = 10
    regions = (models.Region.query.filter(models.Region.reg_c_id == courier.courier_id).all())
    reg_new = []
    for el in regions:
        reg_new.append(int(str(el)))
    courier_orders_new = models.Order.query.filter(or_((models.Order.stage == str(idx)),\
                                                (models.Order.weight >= weight_available),(models.Order.region.notin_(reg_new)),\
                                                    (time_check_for_update(courier.working_hours.all(), models.DeliveryHours.query.\
                                                        filter(models.DeliveryHours.ord_id == models.Order.order_id).all())))).\
                                                            filter(models.Order.stage != 'Free').all()
    for el in courier_orders_new:
        el = str(el)
        models.Order.query.filter(models.Order.order_id == int(el)).first().stage = 'Free'
    models.db.session.commit()
    return Response(response= 'HTTP 200 OK\n'+ json.dumps(returner), status='200 OK')


@app.route('/app/couriers/<int:idx>/', methods=['GET'])
def get_statistics(idx):
    courier = models.Courier.query.get(idx)
    working_hours = courier.working_hours.all()
    regions = courier.regions
    courier_type = courier.courier_type
    C = 0
    if courier_type == 'auto':
        C = 9
    elif courier_type == 'bike':
        C = 5
    else:
        C = 2
    all_regions = models.Region.query.filter(models.Region.reg_c_id == idx).all()
    str_regs = []
    str_hrs = []
    for el in all_regions:
        str_regs.append(str(el))
    for el in working_hours:
        str_hrs.append(str(el))
    av_min = 99999
    orders_counter = 0
    for el in all_regions:
        if el.reg_orders_amount and el.reg_summ_time:
            tmp = int(str(el.reg_summ_time)) / int(str(el.reg_orders_amount))
            av_min = min(tmp, av_min)
            orders_counter += int(str(el.reg_orders_amount))
    earnings = 500 * C * orders_counter
    if orders_counter != 0:
        rating = (3600 - min(3600, av_min)) / 3600 * 5
        returner = {
            "courier_id": idx,
            "courier_type": courier_type,
            "regions": str_regs,
            "working_hours": str_hrs,
            "rating": rating,
            "earnings": earnings
        }
        return Response(response= json.dumps(returner), status='200 OK')
    else:
        returner = {
            "courier_id": idx,
            "courier_type": courier_type,
            "regions": str_regs,
            "working_hours": str_hrs,
            "earnings": earnings
        }
        return Response(response= json.dumps(returner), status='200 OK')


@app.route('/app/orders/', methods=['POST'])
def orders():
    info = (request.get_json(force=True))
    returner_valid = {"orders": []}
    returner_invalid = {'validation_error': {'orders': []}}
    checker = ["weight", "region", "delivery_hours"]
    for el in info['data']:
        for part in checker:
            if part not in el.keys():
                if not len(returner_invalid['validation_error']['orders']) or el['order_id'] != returner_invalid['validation_error']['orders'][-1]['id']:
                    returner_invalid['validation_error']['orders'].append({'id':el['order_id']})
        if not len(returner_invalid['validation_error']['orders']) or el['order_id'] != returner_invalid['validation_error']['orders'][-1]['id']:
            ord_id, weight, ord_reg, dev_hrs = el['order_id'], el['weight'], el['region'], el['delivery_hours']

            into_order = models.Order(order_id=ord_id, weight=weight, region=ord_reg)
            returner_valid['orders'].append({'id': ord_id})
            models.db.session.add(into_order)


            for i in range(len(dev_hrs)):
                into_hrs = models.DeliveryHours(hours=dev_hrs[i], ord_id=ord_id)
                models.db.session.add(into_hrs)

    if not returner_invalid['validation_error']['orders']:
        models.db.session.commit()
        return Response(response= 'HTTP 201 Created\n' + json.dumps(returner_valid), status = '201 Created')
    else:
        return Response(response= 'HTTP 400 Bad Request\n' + json.dumps(returner_invalid), status = '400 Bad Request')


@app.route('/app/orders/assign/', methods=['POST'])
def assigner():
    info = (request.get_json(force=True))
    if 'courier_id' not in info.keys():
        return Response(status='400 Bad Request')
    else:
        courier_id = info['courier_id']
        info['assign_time'] = str(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))
        assign_time = str(datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))[11:19]
        courier = models.Courier.query.get(courier_id)
        if not courier:
            return Response(status='400 Bad Request')
        if courier.courier_type == 'auto':
            weight_available = 51
        elif courier.courier_type == 'bike':
            weight_available = 15
        else:
            weight_available = 10
    regions = (models.Region.query.filter(models.Region.reg_c_id == courier_id).all())
    reg_new = []
    for el in regions:
        reg_new.append(int(str(el)))
    time_offcut = list(courier.working_hours.all())
    response = models.Order.query.filter(models.Order.weight <= weight_available).\
        filter(models.Order.region.in_(reg_new)).\
        filter(time_check(courier.working_hours.all(), models.DeliveryHours.query.filter(models.DeliveryHours.ord_id == models.Order.order_id).all(), assign_time)).all()
    orders_given = {'orders':[]}
    for el in response:
        el = str(el)
        order = models.Order.query.filter(models.Order.order_id == int(el)).\
            filter(models.Order.stage == 'Free').first()

        if order:
            order.stage = str(courier_id)
            orders_given['orders'].append({'id': el})
            models.db.session.add(models.PrevTime(pt_reg=order.region, pt_time=info['assign_time'], pt_c_id=courier_id, pt_ord_id=int(el)))
        if len(orders_given['orders']):
            orders_given['assign_time'] = info['assign_time']
            models.db.session.commit()
    return Response(response='HTTP 200 Created\n' + json.dumps(orders_given), status = 200)

@app.route('/app/orders/complete/', methods=['POST'])
def complete():
    info = (request.get_json(force=True))
    compl_time = info['complete_time']
    sec_compl_time = int(compl_time[11:13]) * 3600 + int(compl_time[14:15]) * 60 + int(compl_time[17:19])
    order_id = info['order_id']
    courier_id = info['courier_id']
    courier = models.Courier.query.get(courier_id)
    order = models.Order.query.filter(models.Order.order_id == order_id).first()
    if order and order.stage == str(courier_id):
        order.stage = 'COMPLETED'
        to_return = {'order_id':order_id}
        previous_time = models.PrevTime.query.filter(models.PrevTime.pt_ord_id == order_id).first()
        sec_previous_time = int(str(previous_time)[11:13]) * 3600 + int(str(previous_time)[14:15]) * 60 + int(str(previous_time)[17:19])
        region = models.Region.query.filter(models.Region.reg_c_id == courier_id)\
            .filter(models.Region.reg == order.region).first()
        region.reg_summ_time += sec_compl_time - sec_previous_time
        previous_time.pt_time = compl_time
        region.reg_orders_amount += 1
        response = Response(response='HTTP 200 OK' + json.dumps(to_return), status='200 OK' )
        models.db.session.commit()
        return response
    else:
        response = Response(response='HTTP 400 Bad Request', status=400)
        return response








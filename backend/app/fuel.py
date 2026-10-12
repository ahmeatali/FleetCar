"""Fuel dashboard calculations from persisted purchases; no synthetic consumption or locations."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def build_fuel_overview(vehicles, records, photos=None, start_date=None, end_date=None,
                        vehicle_id=None, vehicle_group=None, fuel_type=None, station=None, search=None):
    today = datetime.now(ZoneInfo('Europe/Istanbul')).date()
    try:
        start = date.fromisoformat(start_date) if start_date else today.replace(day=1)
        end = date.fromisoformat(end_date) if end_date else today
    except ValueError:
        raise ValueError('Tarihleri YYYY-AA-GG biçiminde girin.')
    if start > end:
        raise ValueError('Başlangıç tarihi bitiş tarihinden sonra olamaz.')
    if (end - start).days > 3660:
        raise ValueError('En fazla 10 yıllık bir dönem seçebilirsiniz.')
    # A full calendar month compares against the previous calendar month.
    if start.day == 1 and end == (end.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1):
        previous_end = start - timedelta(days=1)
        previous_start = previous_end.replace(day=1)
    else:
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - (end - start)
    vehicle_map = {v.id: v for v in vehicles}
    rows = []
    for record in records:
        v = vehicle_map.get(record['vehicle_id'])
        if not v:
            continue
        try:
            day = date.fromisoformat(record['date'][:10])
        except (ValueError, TypeError):
            continue
        rows.append({**record, 'day': day, 'plate': v.plate, 'brand': v.brand, 'model': v.model,
                     'vehicle_group': v.vehicle_group or v.vehicle_segment or v.vehicle_type or 'Belirtilmedi',
                     'fuel_type': record.get('fuel_type') or v.fuel or 'Belirtilmedi',
                     'station': record.get('station') or 'Belirtilmedi',
                     'unit_price': record['amount'] / record['liters'] if record.get('liters') and record['liters'] > 0 else None,
                     'vehicle_photo': (photos or {}).get(v.id), 'consumption': None, 'distance_km': None,
                     'consumed_liters': None})
    # Between two full fills, sum intervening partial fills and the final fill.
    # The baseline fill is excluded; unknown liters invalidate the entire interval.
    histories = defaultdict(list)
    for row in rows:
        histories[row['vehicle_id']].append(row)
    for history in histories.values():
        baseline, liters, valid = None, 0, True
        for row in sorted(history, key=lambda r: (r['date'], r['id'])):
            if baseline is not None:
                valid = valid and row.get('liters') is not None and row['liters'] > 0
                liters += row.get('liters') or 0
                if row['mileage'] < baseline:
                    baseline, liters, valid = None, 0, True
            if row.get('full_tank'):
                if baseline is not None and row['mileage'] > baseline and valid:
                    row['distance_km'] = row['mileage'] - baseline
                    row['consumed_liters'] = liters
                    row['consumption'] = liters / row['distance_km'] * 100
                baseline, liters, valid = row['mileage'], 0, True

    def normalized(value):
        return str(value or '').replace('İ', 'i').replace('I', 'ı').lower()

    def matches(row):
        return (not vehicle_id or row['vehicle_id'] == vehicle_id) and \
            (not vehicle_group or row['vehicle_group'] == vehicle_group) and \
            (not fuel_type or row['fuel_type'] == fuel_type) and \
            (not station or row['station'] == station) and \
            (not search or normalized(search) in normalized(' '.join(str(row.get(k) or '') for k in
                ('plate', 'brand', 'model', 'receipt_no', 'station', 'date', 'note'))))

    selected = sorted([r for r in rows if start <= r['day'] <= end and matches(r)],
                      key=lambda r: (r['date'], r['id']), reverse=True)
    previous = [r for r in rows if previous_start <= r['day'] <= previous_end and matches(r)]

    def summary(items):
        measured = [r for r in items if r.get('liters') and r['liters'] > 0]
        liters = sum(r['liters'] for r in measured)
        intervals = [r for r in items if r['distance_km'] is not None]
        distance = sum(r['distance_km'] for r in intervals)
        return {'amount': sum(r['amount'] for r in items),
                'liters': liters if measured else None,
                'unit_price': sum(r['amount'] for r in measured) / liters if liters else None,
                'consumption': sum(r['consumed_liters'] for r in intervals) / distance * 100 if distance else None,
                'average_fill': liters / len(measured) if measured else None,
                'count': len(items), 'missing_liters': len(items) - len(measured),
                'measured_distance_km': distance, 'consumption_intervals': len(intervals)}

    totals, prior = summary(selected), summary(previous)
    changes = {key: (totals[key] - prior[key]) / prior[key] * 100
               if totals[key] is not None and prior[key] not in (None, 0) else None
               for key in ('amount', 'liters', 'unit_price', 'consumption', 'average_fill')}
    fuel_groups, station_groups, car_groups = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in selected:
        fuel_groups[row['fuel_type']].append(row)
        if row['station'] != 'Belirtilmedi':
            station_groups[row['station']].append(row)
        car_groups[row['vehicle_id']].append(row)
    breakdown = [{'fuel_type': name, **summary(items)} for name, items in sorted(fuel_groups.items())]
    stations = [{'station': name, **summary(items)} for name, items in station_groups.items()]
    top_station = max(stations, key=lambda s: (s['count'], s['amount']), default=None)
    cheapest = min([s for s in stations if s['unit_price'] is not None], key=lambda s: s['unit_price'], default=None)
    ranking = [{'vehicle_id': key, 'plate': items[0]['plate'], 'brand': items[0]['brand'],
                'model': items[0]['model'], 'vehicle_group': items[0]['vehicle_group'],
                'vehicle_photo': items[0]['vehicle_photo'], **summary(items)} for key, items in car_groups.items()]
    ranking.sort(key=lambda item: (item['consumption'] is not None, item['consumption'] or 0, item['amount']), reverse=True)
    bucket_days = max(7, ((end - start).days + 1 + 11) // 12)
    chart = []
    cursor = start
    while cursor <= end:
        bucket_end = min(end, cursor + timedelta(days=bucket_days - 1))
        chart.append({'start': cursor.isoformat(), 'end': bucket_end.isoformat(),
                      **summary([r for r in selected if cursor <= r['day'] <= bucket_end])})
        cursor = bucket_end + timedelta(days=1)
    markers = [{'id': r['id'], 'latitude': r['latitude'], 'longitude': r['longitude'],
                'station': r['station'], 'plate': r['plate'], 'date': r['date'],
                'consumption': r['consumption'], 'liters': r['liters'], 'amount': r['amount']}
               for r in selected if r.get('latitude') is not None and r.get('longitude') is not None]
    for row in selected:
        row.pop('day')
    return {'period': {'start': start.isoformat(), 'end': end.isoformat(),
                       'previous_start': previous_start.isoformat(), 'previous_end': previous_end.isoformat()},
            'summary': totals, 'changes': changes, 'records': selected, 'chart': chart,
            'breakdown': breakdown, 'ranking': ranking, 'map_markers': markers,
            'insights': {'top_station': top_station, 'cheapest_station': cheapest},
            'options': {'vehicles': [{'id': v.id, 'plate': v.plate, 'brand': v.brand, 'model': v.model,
                                     'fuel': v.fuel, 'is_active': v.is_active} for v in vehicles],
                        'groups': sorted({v.vehicle_group or v.vehicle_segment or v.vehicle_type or 'Belirtilmedi' for v in vehicles}),
                        'fuel_types': sorted({r['fuel_type'] for r in rows} | {v.fuel for v in vehicles if v.fuel}),
                        'stations': sorted({r['station'] for r in rows})}}

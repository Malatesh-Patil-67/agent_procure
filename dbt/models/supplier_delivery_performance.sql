select
  supplier_id,
  round(avg(case when received_date <= promised_date then 1.0 else 0.0 end) * 100, 1) as on_time_delivery_pct,
  percentile_cont(0.5) within group (order by received_date - order_date) as median_lead_time_days,
  sum(units) as delivered_units
from {{ source('public', 'delivery_events') }}
group by supplier_id

-- Q1.1 Row count, unique bookings, unique customers, date range
SELECT COUNT(*)                     AS total_rows,
       COUNT(DISTINCT Booking_ID)   AS unique_bookings,
       COUNT(DISTINCT Customer_ID)  AS unique_customers,
       MIN(Booking_Date)            AS first_day,
       MAX(Booking_Date)            AS last_day
FROM bookings;

-- Q1.2 Nulls that are EXPECTED (ratings/TAT/payment exist only for completed bookings)
SELECT Booking_Status,
       COUNT(*)                                             AS bookings,
       SUM(CASE WHEN Driver_Ratings IS NULL THEN 1 ELSE 0 END) AS missing_driver_rating,
       SUM(CASE WHEN V_TAT IS NULL THEN 1 ELSE 0 END)           AS missing_v_tat,
       SUM(CASE WHEN Payment_Method = 'Not Applicable' THEN 1 ELSE 0 END) AS no_payment
FROM bookings
GROUP BY Booking_Status;

-- 2. HEADLINE KPIs
-- Q2.1 Overall scorecard
SELECT COUNT(*)                                                        AS total_bookings,
       SUM(Booking_Status = 'Success')                                 AS successful_rides,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2)    AS success_rate_pct,
       ROUND(100.0 * SUM(Booking_Status <> 'Success') / COUNT(*), 2)   AS failure_rate_pct,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END)        AS revenue_inr,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END), 1) AS avg_fare_inr,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Ride_Distance END), 2) AS avg_distance_km,
       ROUND(AVG(Driver_Ratings), 2)                                   AS avg_driver_rating,
       ROUND(AVG(Customer_Rating), 2)                                  AS avg_customer_rating
FROM bookings;

-- Q2.2 Booking status split
SELECT Booking_Status,
       COUNT(*)                                                         AS bookings,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM bookings), 2)     AS pct_of_total
FROM bookings
GROUP BY Booking_Status
ORDER BY bookings DESC;

-- Q2.3 Revenue lost: fare value of bookings that did not complete
SELECT Booking_Status,
       COUNT(*)           AS failed_bookings,
       SUM(Booking_Value) AS revenue_at_risk_inr
FROM bookings
WHERE Booking_Status <> 'Success'
GROUP BY Booking_Status
ORDER BY revenue_at_risk_inr DESC;

-- 3. VEHICLE TYPE PERFORMANCE
-- Q3.1 Full vehicle scorecard
SELECT Vehicle_Type,
       COUNT(*)                                                                   AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2)               AS success_rate_pct,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END)           AS revenue_inr,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END), 1) AS avg_fare_inr,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success' THEN Ride_Distance END), 2) AS avg_distance_km,
       ROUND(AVG(Driver_Ratings), 2)                                              AS avg_driver_rating,
       ROUND(AVG(Customer_Rating), 2)                                             AS avg_customer_rating
FROM bookings
GROUP BY Vehicle_Type
ORDER BY revenue_inr DESC;

-- Q3.2 Revenue per km (price efficiency) by vehicle
SELECT Vehicle_Type,
       ROUND(SUM(Booking_Value) * 1.0 / SUM(Ride_Distance), 2) AS revenue_per_km_inr
FROM bookings
WHERE Booking_Status = 'Success' AND Ride_Distance > 0
GROUP BY Vehicle_Type
ORDER BY revenue_per_km_inr DESC;

-- Q3.3 Vehicle ranking with window functions (revenue rank vs. success-rate rank)
WITH v AS (
    SELECT Vehicle_Type,
           SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END)  AS revenue,
           100.0 * SUM(Booking_Status = 'Success') / COUNT(*)                AS success_rate
    FROM bookings GROUP BY Vehicle_Type
)
SELECT Vehicle_Type,
       revenue,
       RANK() OVER (ORDER BY revenue DESC)      AS revenue_rank,
       ROUND(success_rate, 2)                   AS success_rate_pct,
       RANK() OVER (ORDER BY success_rate DESC) AS success_rank
FROM v
ORDER BY revenue_rank;

-- Q3.4 Turnaround times by vehicle (V_TAT = vehicle arrival, C_TAT = customer pickup/drop handling)
SELECT Vehicle_Type,
       ROUND(AVG(V_TAT), 1) AS avg_v_tat,
       ROUND(AVG(C_TAT), 1) AS avg_c_tat,
       MIN(V_TAT)           AS min_v_tat,
       MAX(V_TAT)           AS max_v_tat
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type
ORDER BY avg_v_tat;

-- 4. TIME PATTERNS
-- Q4.1 Demand and success rate by hour of day
SELECT Hour,
       COUNT(*)                                                     AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       ROUND(100.0 * SUM(Booking_Status <> 'Success') / COUNT(*), 2) AS failure_rate_pct
FROM bookings
GROUP BY Hour
ORDER BY Hour;

-- Q4.2 Time-of-day buckets
SELECT CASE WHEN Hour BETWEEN 5  AND 8  THEN '1 Early Morning (5-8)'
            WHEN Hour BETWEEN 9  AND 11 THEN '2 Late Morning (9-11)'
            WHEN Hour BETWEEN 12 AND 16 THEN '3 Afternoon (12-16)'
            WHEN Hour BETWEEN 17 AND 20 THEN '4 Evening Rush (17-20)'
            WHEN Hour BETWEEN 21 AND 23 THEN '5 Night (21-23)'
            ELSE '6 Late Night (0-4)' END                           AS day_part,
       COUNT(*)                                                     AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END) AS revenue_inr
FROM bookings
GROUP BY day_part
ORDER BY day_part;

-- Q4.3 Day of week  (July 2024 has 5 Mon/Tue/Wed but only 4 of every other day,
--      so raw totals mislead: compare avg_bookings_per_day, not bookings)
SELECT Day_Of_Week,
       COUNT(DISTINCT Booking_Date)                                 AS days_in_month,
       COUNT(*)                                                     AS bookings,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT Booking_Date), 0)      AS avg_bookings_per_day,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       ROUND(1.0 * SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END)
             / COUNT(DISTINCT Booking_Date), 0)                     AS avg_revenue_per_day
FROM bookings
GROUP BY Day_Of_Week, Day_Num
ORDER BY Day_Num;

-- Q4.4 Daily trend with running revenue total and 7-day moving average of bookings
WITH daily AS (
    SELECT Booking_Date,
           COUNT(*) AS bookings,
           SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value ELSE 0 END) AS revenue
    FROM bookings GROUP BY Booking_Date
)
SELECT Booking_Date, bookings, revenue,
       SUM(revenue) OVER (ORDER BY Booking_Date)                                   AS running_revenue,
       ROUND(AVG(bookings) OVER (ORDER BY Booking_Date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS bookings_7d_avg
FROM daily
ORDER BY Booking_Date;

-- Q4.5 Busiest and quietest days
SELECT Booking_Date, COUNT(*) AS bookings
FROM bookings GROUP BY Booking_Date ORDER BY bookings DESC LIMIT 5;

-- 5. LOCATION & ROUTE ANALYSIS
-- Q5.1 Top 10 pickup locations by demand
SELECT Pickup_Location,
       COUNT(*)                                                     AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END) AS revenue_inr
FROM bookings
GROUP BY Pickup_Location
ORDER BY bookings DESC
LIMIT 10;

-- Q5.2 Ten weakest pickup locations by success rate (fulfilment problem areas)
SELECT Pickup_Location,
       COUNT(*)                                                     AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       SUM(Booking_Status = 'Driver Not Found')                     AS driver_not_found
FROM bookings
GROUP BY Pickup_Location
ORDER BY success_rate_pct ASC
LIMIT 10;

-- Q5.3 Top 10 drop locations by revenue
SELECT Drop_Location,
       COUNT(*)           AS completed_rides,
       SUM(Booking_Value) AS revenue_inr
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Drop_Location
ORDER BY revenue_inr DESC
LIMIT 10;

-- Q5.4 Top 10 routes (pickup -> drop) by completed rides
SELECT Pickup_Location || ' -> ' || Drop_Location AS route,
       COUNT(*)           AS completed_rides,
       SUM(Booking_Value) AS revenue_inr
FROM bookings
WHERE Booking_Status = 'Success' AND Pickup_Location <> Drop_Location
GROUP BY route
ORDER BY completed_rides DESC
LIMIT 10;

-- Q5.5 Pickup locations ranked by driver-cancellation rate
SELECT Pickup_Location,
       COUNT(*) AS bookings,
       ROUND(100.0 * SUM(Booking_Status = 'Canceled by Driver') / COUNT(*), 2) AS driver_cancel_pct
FROM bookings
GROUP BY Pickup_Location
ORDER BY driver_cancel_pct DESC
LIMIT 10;

-- 6. CANCELLATIONS & INCOMPLETE RIDES
-- Q6.1 Why customers cancel
SELECT Canceled_Rides_by_Customer AS reason,
       COUNT(*) AS cancellations,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customer_cancels
FROM bookings
WHERE Booking_Status = 'Canceled by Customer'
GROUP BY reason
ORDER BY cancellations DESC;

-- Q6.2 Why drivers cancel
SELECT Canceled_Rides_by_Driver AS reason,
       COUNT(*) AS cancellations,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_driver_cancels
FROM bookings
WHERE Booking_Status = 'Canceled by Driver'
GROUP BY reason
ORDER BY cancellations DESC;

-- Q6.3 Incomplete rides and their reasons (among successful bookings)
SELECT Incomplete_Rides_Reason AS reason,
       COUNT(*) AS incomplete_rides,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM bookings WHERE Booking_Status = 'Success'), 2) AS pct_of_successful
FROM bookings
WHERE Incomplete_Rides = 'Yes'
GROUP BY reason
ORDER BY incomplete_rides DESC;

-- Q6.4 Cancellation + not-found rate by vehicle type
SELECT Vehicle_Type,
       ROUND(100.0 * SUM(Booking_Status = 'Canceled by Customer') / COUNT(*), 2) AS customer_cancel_pct,
       ROUND(100.0 * SUM(Booking_Status = 'Canceled by Driver')   / COUNT(*), 2) AS driver_cancel_pct,
       ROUND(100.0 * SUM(Booking_Status = 'Driver Not Found')     / COUNT(*), 2) AS not_found_pct
FROM bookings
GROUP BY Vehicle_Type
ORDER BY driver_cancel_pct DESC;

-- Q6.5 Failure rate by hour: when does the platform fail most?
SELECT Hour,
       COUNT(*) AS bookings,
       ROUND(100.0 * SUM(Booking_Status <> 'Success') / COUNT(*), 2) AS failure_rate_pct
FROM bookings
GROUP BY Hour
ORDER BY failure_rate_pct DESC
LIMIT 5;

-- 7. PAYMENTS
-- Q7.1 Payment method mix on completed rides
SELECT Payment_Method,
       COUNT(*)           AS rides,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_rides,
       SUM(Booking_Value) AS revenue_inr,
       ROUND(AVG(Booking_Value), 1) AS avg_fare_inr
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Payment_Method
ORDER BY rides DESC;

-- Q7.2 Payment method by vehicle type
SELECT Vehicle_Type,
       ROUND(100.0 * SUM(Payment_Method = 'Cash') / COUNT(*), 1) AS cash_pct,
       ROUND(100.0 * SUM(Payment_Method = 'UPI')  / COUNT(*), 1) AS upi_pct,
       ROUND(100.0 * SUM(Payment_Method IN ('Credit Card','Debit Card')) / COUNT(*), 1) AS card_pct
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Vehicle_Type;

-- 8. CUSTOMERS & RATINGS
-- Q8.1 Booking frequency: how many customers booked 1, 2, 3+ times
SELECT bookings_per_customer, COUNT(*) AS customers
FROM (SELECT Customer_ID, COUNT(*) AS bookings_per_customer FROM bookings GROUP BY Customer_ID)
GROUP BY bookings_per_customer
ORDER BY bookings_per_customer;

-- Q8.2 Top 10 customers by completed-ride spend
SELECT Customer_ID,
       COUNT(*)           AS completed_rides,
       SUM(Booking_Value) AS total_spend_inr
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY Customer_ID
ORDER BY total_spend_inr DESC
LIMIT 10;

-- Q8.3 Rating distribution (driver vs customer)
SELECT Driver_Ratings AS rating,
       COUNT(*)       AS rides
FROM bookings
WHERE Driver_Ratings IS NOT NULL
GROUP BY Driver_Ratings
ORDER BY Driver_Ratings;

-- Q8.4 Does a longer wait hurt the rating? (V_TAT band vs avg customer rating)
SELECT CASE WHEN V_TAT < 100 THEN '1 Under 100'
            WHEN V_TAT < 170 THEN '2 100-169'
            WHEN V_TAT < 240 THEN '3 170-239'
            ELSE '4 240+' END AS v_tat_band,
       COUNT(*)                         AS rides,
       ROUND(AVG(Customer_Rating), 3)   AS avg_customer_rating,
       ROUND(AVG(Driver_Ratings), 3)    AS avg_driver_rating
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY v_tat_band
ORDER BY v_tat_band;

-- Q8.5 High-value rides: fare buckets
SELECT CASE WHEN Booking_Value < 250  THEN '1 Under 250'
            WHEN Booking_Value < 500  THEN '2 250-499'
            WHEN Booking_Value < 1000 THEN '3 500-999'
            WHEN Booking_Value < 2000 THEN '4 1000-1999'
            ELSE '5 2000+' END AS fare_band,
       COUNT(*)           AS rides,
       SUM(Booking_Value) AS revenue_inr,
       ROUND(100.0 * SUM(Booking_Value) / SUM(SUM(Booking_Value)) OVER (), 2) AS pct_of_revenue
FROM bookings
WHERE Booking_Status = 'Success'
GROUP BY fare_band
ORDER BY fare_band;

-- 9. SUMMARY VIEW FOR DASHBOARDS (used by the Streamlit app)
DROP VIEW IF EXISTS v_vehicle_summary;
CREATE VIEW v_vehicle_summary AS
SELECT Vehicle_Type,
       COUNT(*)                                                     AS bookings,
       SUM(Booking_Status = 'Success')                              AS successful,
       ROUND(100.0 * SUM(Booking_Status = 'Success') / COUNT(*), 2) AS success_rate_pct,
       SUM(CASE WHEN Booking_Status = 'Success' THEN Booking_Value END) AS revenue_inr
FROM bookings
GROUP BY Vehicle_Type;

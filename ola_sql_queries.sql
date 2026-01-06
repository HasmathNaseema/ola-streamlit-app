-- name:  All successful bookings
select * from ola_clean 
where Booking_Status = 'Success';

-- name:  The average ride distance for each vehicle type
select Vehicle_Type ,
round(avg(Ride_Distance),2) as Avg_Distance 
from ola_clean
group by Vehicle_Type
order by Avg_Distance desc;

-- name: The total number of cancelled rides by customers
 select 
 count(Canceled_Rides_by_Customer) as Cancelled_by_Customers
 from ola_clean
 order by Cancelled_by_Customers desc;
 
-- name: The top 5 customers who booked the highest number of rides
select 
Customer_ID ,
count(Booking_ID) as Total_Rides
from ola_clean 
group by Customer_ID 
order by Total_Rides desc
limit 5 ;

-- name: The number of rides cancelled by drivers due to personal and car-related issues
select 
count(Canceled_Rides_by_Driver) as Cancelled_by_Driver
from ola_clean 
where Canceled_Rides_by_Driver = 'Personal & Car related issue';

-- name: The maximum and minimum driver ratings for Prime Sedan bookings
select 
vehicle_type,
max(Driver_Ratings) as Max_Ratings ,
min(Driver_Ratings) as Min_Ratings 
from ola_clean
where Vehicle_type = 'Prime Sedan'
group by Vehicle_type;

-- name: All rides where payment was made using UPI
select * 
from ola_clean 
where Payment_Method = 'UPI';

-- name:  The average customer rating per vehicle type
select 
Vehicle_Type,
round(avg(Customer_Rating),2) Avg_Customer_Ratings
from ola_clean
group by Vehicle_Type
order by Avg_Customer_Ratings desc;

-- name: The total booking value of rides completed successfully
select 
sum(Booking_Value) Total_Booking_Value
from ola_clean
where Booking_Status = 'Success';

-- name:  All incomplete rides along with the reason
select 
Booking_Id,
Incomplete_Rides_Reason
from ola_clean 
where Incomplete_Rides = 'Yes';




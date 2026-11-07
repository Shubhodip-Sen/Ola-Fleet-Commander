"""Clean OLA_DataSet.xlsx (sheet 'July') and build data/ola_cleaned.csv + data/ola.db (SQLite).
Run:  python prep_data.py  (expects OLA_DataSet.xlsx next to this file or in ./data)"""
import os, sqlite3, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = next((p for p in [os.path.join(HERE, "OLA_DataSet.xlsx"), os.path.join(HERE, "data", "OLA_DataSet.xlsx")] if os.path.exists(p)), None)
if SRC is None:
    raise SystemExit("Place OLA_DataSet.xlsx in this folder or in ./data and re-run.")

df = pd.read_excel(SRC, sheet_name="July").rename(columns={"Vehicle Images": "Vehicle_Image"})
df["Date"] = pd.to_datetime(df["Date"])
df["Booking_Date"] = df["Date"].dt.strftime("%Y-%m-%d")
df["Booking_Time"] = df["Time"].astype(str)
df["Hour"] = df["Date"].dt.hour
df["Day_Of_Week"] = df["Date"].dt.day_name()
df["Day_Num"] = df["Date"].dt.dayofweek
df["Week"] = (df["Date"].dt.day - 1) // 7 + 1
for c in ["Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver", "Incomplete_Rides_Reason", "Payment_Method", "Incomplete_Rides"]:
    df[c] = df[c].fillna("Not Applicable")
cols = ["Booking_ID", "Booking_Date", "Booking_Time", "Hour", "Day_Of_Week", "Day_Num", "Week", "Booking_Status",
        "Customer_ID", "Vehicle_Type", "Pickup_Location", "Drop_Location", "V_TAT", "C_TAT",
        "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver", "Incomplete_Rides", "Incomplete_Rides_Reason",
        "Booking_Value", "Payment_Method", "Ride_Distance", "Driver_Ratings", "Customer_Rating", "Vehicle_Image"]
df = df[cols]
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
df.to_csv(os.path.join(HERE, "data", "ola_cleaned.csv"), index=False)
db = os.path.join(HERE, "data", "ola.db")
if os.path.exists(db): os.remove(db)
con = sqlite3.connect(db)
df.to_sql("bookings", con, index=False)
for ix in ["Booking_Status", "Vehicle_Type", "Booking_Date", "Pickup_Location", "Customer_ID"]:
    con.execute(f"CREATE INDEX idx_{ix} ON bookings({ix})")
df.groupby("Vehicle_Type", as_index=False).Vehicle_Image.first().to_sql("vehicle_images", con, index=False)
con.commit(); con.close()
print("rows:", len(df), "->", db)

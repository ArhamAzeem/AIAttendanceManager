from pymongo import MongoClient
from datetime import datetime
import pytz

class DatabaseManager:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="ai_attendance_system"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.students = self.db['students']
        self.attendance = self.db['attendance']
        self.tz = pytz.timezone('Asia/Karachi')

    def generate_student_id(self):
        last_student = self.students.find_one(
            {},
            sort=[("student_id", -1)]
        )

        if last_student:
            last_id = last_student["student_id"]
            last_number = int(last_id.split("-")[1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"STU-{new_number:03d}"

    def register_student(self, student_id, name):
        if self.students.find_one({"student_id": student_id}):
            return False, "Student ID already exists."

        now = datetime.now(self.tz)
        student_data = {
            "student_id": student_id,
            "name": name,
            "registered_at": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.students.insert_one(student_data)
        return True, "Student registered successfully."

    def get_all_students(self):
        return list(self.students.find({}, {"_id": 0}))

    def get_student_by_id(self, student_id):
        return self.students.find_one({"student_id": student_id})

    def mark_attendance(self, student_id):
        now = datetime.now(self.tz)
        today_date = now.strftime("%Y-%m-%d")
        current_time = now
        current_time_str = current_time.strftime("%H:%M:%S")

        record = self.attendance.find_one(
            {"student_id": student_id, "date": today_date},
            sort=[("_id", -1)]
        )

        if not record:
            self.attendance.insert_one({
                "student_id": student_id,
                "date": today_date,
                "in_time": current_time_str,
                "out_time": "-"
            })
            return f"Marked IN for {student_id} at {current_time_str}"
        else:
            if record['out_time'] == "-":
                last_time_str = record['in_time']
            else:
                last_time_str = record['out_time']

            last_time = datetime.strptime(f"{today_date} {last_time_str}", "%Y-%m-%d %H:%M:%S")
            last_time = self.tz.localize(last_time)
            
            time_diff = (current_time - last_time).total_seconds()
            
            if record['out_time'] == "-":
                if time_diff > 300:
                    self.attendance.update_one(
                        {"_id": record["_id"]},
                        {"$set": {"out_time": current_time_str}}
                    )
                    return f"Updated OUT for {student_id} at {current_time_str}"
                else:
                    return f"Already marked IN recently. Waiting for OUT."
            else:
                if time_diff > 300:
                    self.attendance.insert_one({
                        "student_id": student_id,
                        "date": today_date,
                        "in_time": current_time_str,
                        "out_time": "-"
                    })
                    return f"Marked NEW IN for {student_id} at {current_time_str}"
                else:
                    self.attendance.update_one(
                        {"_id": record["_id"]},
                        {"$set": {"out_time": current_time_str}}
                    )
                    return f"Updated OUT for {student_id} at {current_time_str}"

    def get_attendance_logs(self, date=None):
        query = {}
        if date:
            query["date"] = date
        return list(self.attendance.find(query, {"_id": 0}).sort("date", -1))

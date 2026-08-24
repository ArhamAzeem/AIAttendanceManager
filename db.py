from pymongo import MongoClient
from datetime import datetime

class DatabaseManager:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="attendance_db"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.students = self.db['students']
        self.attendance = self.db['attendance']

    def generate_student_id(self):
        count = self.students.count_documents({})
        return f"STU-{count + 1:03d}"

    def register_student(self, student_id, name):
        """Register a new student."""
        if self.students.find_one({"student_id": student_id}):
            return False, "Student ID already exists."

        self.students.insert_one({
            "student_id": student_id,
            "name": name,
            "registered_at": datetime.now()
        })
        return True, "Student registered successfully."

    def get_all_students(self):
        """Fetch all registered students."""
        return list(self.students.find({}, {"_id": 0}))

    def get_student_by_id(self, student_id):
        """Fetch a specific student by ID."""
        return self.students.find_one({"student_id": student_id}, {"_id": 0})

    def mark_attendance(self, student_id):
        """
        Mark attendance for a student.
        If first time today -> In-Time
        If already marked today -> update Out-Time or create new entry based on cooldown.
        """
        today_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now()
        current_time_str = current_time.strftime("%H:%M:%S")

        # Fetch the latest record for today
        record = self.attendance.find_one(
            {"student_id": student_id, "date": today_date},
            sort=[("_id", -1)]
        )

        if not record:
            self.attendance.insert_one({
                "student_id": student_id,
                "date": today_date,
                "in_time": current_time_str,
                "out_time": current_time_str
            })
            return f"Marked IN for {student_id} at {current_time_str}"
        else:
            last_out_time = datetime.strptime(f"{today_date} {record['out_time']}", "%Y-%m-%d %H:%M:%S")
            time_diff = (current_time - last_out_time).total_seconds()

            # If seen again within 5 minutes, just update out_time
            if time_diff < 300:
                self.attendance.update_one(
                    {"_id": record["_id"]},
                    {"$set": {"out_time": current_time_str}}
                )
                return f"Updated OUT for {student_id} at {current_time_str}"
            else:
                # If more than 5 minutes have passed, create a NEW entry
                self.attendance.insert_one({
                    "student_id": student_id,
                    "date": today_date,
                    "in_time": current_time_str,
                    "out_time": current_time_str
                })
                return f"Marked NEW IN for {student_id} at {current_time_str}"

    def get_attendance_logs(self, date=None):
        """Fetch attendance logs, optionally filtered by date."""
        query = {}
        if date:
            query["date"] = date
        return list(self.attendance.find(query, {"_id": 0}).sort("date", -1))

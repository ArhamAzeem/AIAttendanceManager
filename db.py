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

    def add_attendance_record(self, student_id, date, in_time, out_time="-"):
        self.attendance.insert_one({
            "student_id": student_id,
            "date": date,
            "in_time": in_time,
            "out_time": out_time
        })

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

    def get_activity_feed(self, limit=10):
        """Newest IN/OUT events for the live activity timeline."""
        records = list(self.attendance.find({}, {"_id": 0}))
        names = {s["student_id"]: s["name"] for s in self.get_all_students()}
        events = []
        for rec in records:
            sid = rec.get("student_id")
            name = names.get(sid, sid)
            date = rec.get("date", "")
            in_time = rec.get("in_time")
            out_time = rec.get("out_time")
            if in_time and in_time != "-":
                events.append({
                    "name": name,
                    "student_id": sid,
                    "action": "IN",
                    "time": in_time,
                    "date": date,
                    "sort_key": f"{date} {in_time}",
                })
            if out_time and out_time not in ("-", "", None):
                events.append({
                    "name": name,
                    "student_id": sid,
                    "action": "OUT",
                    "time": out_time,
                    "date": date,
                    "sort_key": f"{date} {out_time}",
                })
        events.sort(key=lambda e: e["sort_key"], reverse=True)
        return events[:limit]

    def get_all_attendance_records(self):
        """Get every attendance record ever logged, oldest first."""
        return list(self.attendance.find({}, {"_id": 0}).sort("date", 1))

    def get_distinct_attendance_dates(self):
        """
        All unique dates where at least one student was marked present.
        Used as the 'total possible days' baseline for % calculations,
        since you don't have a fixed class schedule/calendar defined.
        """
        return sorted(self.attendance.distinct("date"))

    def get_attendance_summary_per_student(self):
        """
        Builds a per-student report: how many days they were present,
        out of how many days attendance was taken at all, as a percentage.
        """
        all_dates = self.get_distinct_attendance_dates()
        total_days = len(all_dates)

        students = self.get_all_students()
        summary = []

        for student in students:
            student_id = student["student_id"]
            name = student["name"]

            present_dates = self.attendance.distinct("date", {"student_id": student_id})
            present_count = len(present_dates)

            if total_days > 0:
                percentage = round((present_count / total_days) * 100, 1)
            else:
                percentage = 0.0

            absent_count = total_days - present_count

            summary.append({
                "student_id": student_id,
                "name": name,
                "days_present": present_count,
                "days_absent": absent_count,
                "total_days": total_days,
                "attendance_percentage": percentage
            })

        return summary

    def get_daily_attendance_trend(self):
        """
        Returns count of present students per date, across all recorded dates.
        Used for the trend chart.
        """
        pipeline = [
            {"$group": {"_id": "$date", "count": {"$addToSet": "$student_id"}}},
            {"$project": {"date": "$_id", "present_count": {"$size": "$count"}, "_id": 0}},
            {"$sort": {"date": 1}}
        ]
        return list(self.attendance.aggregate(pipeline))

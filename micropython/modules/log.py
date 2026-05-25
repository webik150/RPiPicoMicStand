import utime
import os

class Log:
    def __init__(self):
        pass

    @staticmethod
    def log_data(data):
        with open("micstandlog.txt", "a") as file:
            file.write(f"[{utime.time()}] {str(data)}\n")
            print(data)

    @staticmethod
    def delete_log_on_startup():
        try:
            os.remove("micstandlog.txt")
            print("Log file deleted.")
        except OSError:
            print("No log file to delete.")

    # Function to read the log file
    @staticmethod
    def read_log():
        try:
            with open("micstandlog.txt", "r") as file:
                data = file.read()
            return data
        except OSError:
            return "Log file not found."


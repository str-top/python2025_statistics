from log import get_logger
from datetime import datetime, timedelta, timezone

class Conversion:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)

    def format_title(self):
        gmt_plus_5 = timezone(timedelta(hours=5))
        formatted_time = datetime.now(gmt_plus_5).strftime("%d.%m %H:%M:%S")
        title = f"# Результаты практических занятий за последние {self.app.conf.days_of_results} дней"
        title += f'\n\n<div align="right">обновлено: {formatted_time} GMT+5</div>\n\n'
        return title

    def format_overall_rating(self):
        # Calculate actual difference between scores
        overall_gaps = [0]  # No gap for the first student
        for i in range(1, len(self.app.students_overall)):
            prev_score = self.app.students_overall[i - 1][1]
            current_score = self.app.students_overall[i][1]
            gap = prev_score - current_score  # Actual difference
            overall_gaps.append(round(gap))  # Round the difference to the nearest integer

        # Format data
        overall_rating = "## Общий рейтинг студентов\nВ скобках указано отставание в процентах от предыдущего студента\n```\n"
        for i, (name, score) in enumerate(self.app.students_overall):
            gap_text = f" ({overall_gaps[i]}%)" if overall_gaps[i] > 0 else ""
            overall_rating += f"{i + 1}. {name:<10} {round(score)}%{gap_text}\n"
        overall_rating += "```\n"
        return overall_rating

    def format_completed_tests(self):
        total_tests = len(self.app.sorted_tests)
        tests_rating = f"## Рейтинг по количеству сданных работ (из {total_tests})\n```\n"
        for i, (name, test_count) in enumerate(self.app.students_tests):
            tests_rating += f"{i + 1}. {name:<10} {test_count}\n"
        tests_rating += "```\n"
        return tests_rating

    def format_average_score_rating(self):
        # Calculate the threshold for half of the tests
        half_tests_threshold = len(self.app.sorted_tests) / 2

        # Formatting average score rating
        score_rating = "## Рейтинг по проценту правильных ответов\n```\n"
        rank = 1  # Separate counter for ranking index
        for name, score in self.app.students_scores:
            # Check if the student has completed at least half of the tests
            if self.app.students_data[name]["quantity"] >= half_tests_threshold:
                score_rating += f"{rank}. {name:<10} {round(score)}%\n"
                rank += 1  # Increment the ranking index only for included students
        score_rating += "```\n"
        return score_rating

    def format_test_list(self):
        return "## Практические работы:\n```\n" + "\n".join([f"{test}" for i, test in enumerate(self.app.sorted_tests)]) + '\n```\n'

    def test_results_for_mentor(self, sorted_students):
        submitted_tests = ''
        for name, data in sorted_students:
            tests_info = []
            for result in data["results"]:
                test_number = result["test_number"]
                score = round(result["score"])
                date = result["endTime"].split("T")[0]
                short_date = ".".join(reversed(date.split("-")[1:]))  # Convert to dd.mm format
                
                # If role is mentor, include a clickable link
                url = result.get("url", "#")
                test_info = f"{score:>3}% {short_date}"
                test_info = f"{test_number} [{test_info}]({url})"
                
                tests_info.append(test_info)

            # Format the student's results into one line with their name
            submitted_tests += f"{name}: {', '.join(tests_info)}\n"
            submitted_tests += '\n'
        return submitted_tests

    def test_results_for_students(self, sorted_students):
        # If the role is not mentor, show results in columns
        submitted_tests = "```\n"
        # Разбиваем студентов на группы по 4
        column_count = 4
        student_groups = [sorted_students[i:i + column_count] for i in range(0, len(sorted_students), column_count)]

        for group in student_groups:
            # Заголовок с именами студентов
            names = [f"{name:<18}" for name, _ in group]
            submitted_tests += "  ".join(names) + "\n"

            # Определяем максимальное количество тестов в текущей группе
            max_tests = max(len(data["results"]) for _, data in group)

            # Формируем строки с результатами тестов
            for i in range(max_tests):
                row = []
                for name, data in group:
                    if i < len(data["results"]):
                        result = data["results"][i]
                        test_number = result["test_number"]
                        score = round(result["score"])
                        date = result["endTime"].split("T")[0]
                        short_date = ".".join(reversed(date.split("-")[1:]))  # Convert to dd.mm format
                        
                        test_info = f"{test_number} {score:>3}% {short_date}"
                        row.append(test_info.ljust(18))
                    else:
                        row.append("".ljust(18))  # Заполняем пустыми значениями

                submitted_tests += "  ".join(row) + "\n"

            submitted_tests += "\n"  # Отделяем группы пустой строкой

        submitted_tests += "```\n"
        return submitted_tests

    def format_submitted_tests(self, role):
        submitted_tests = "## Сданные работы\n"

        # Сортировка студентов по количеству сданных тестов (по убыванию)
        sorted_students = sorted(self.app.students_data.items(), key=lambda x: len(x[1]["results"]), reverse=True)
        
        if role == 'mentor':
            submitted_tests += self.test_results_for_mentor(sorted_students)
        else:
            submitted_tests += self.test_results_for_students(sorted_students)
        return submitted_tests

    def format_last_results(self):
        last_results = "## Последние результаты\n\n```\n"
        for end_time, test_number, student in self.app.last_15_results:
            formatted_time = end_time.strftime("%d.%m, %H:%M")  # Convert datetime to "HH:MM"
            last_results += f"{formatted_time} {test_number} {student}\n"
        last_results += "```"
        return last_results

    def convert(self, role):
        title = self.format_title()
        overall_rating = self.format_overall_rating()
        tests_rating = self.format_completed_tests()
        score_rating = self.format_average_score_rating()
        test_list = self.format_test_list()
        submitted_tests = self.format_submitted_tests(role)
        last_results = self.format_last_results()
        
        # Concatenating final output
        text = f"{title}\n{overall_rating}\n{tests_rating}\n{score_rating}\n{test_list}\n\n{submitted_tests}\n\n{last_results}"
        self.app.content = text

        line_count = text.count("\n") + 1
        self.logger.info(f'Converted prepared data to {line_count} lines for *.md file')
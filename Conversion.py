from log import get_logger
from datetime import datetime, timedelta, timezone

class Conversion:
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
        
    def calculate_gap(self, sorted_list):
        """Calculate percentage gap between students for overall ranking."""
        gaps = []
        for i in range(len(sorted_list) - 1):
            gap = round(((sorted_list[i][1] - sorted_list[i + 1][1]) / sorted_list[i + 1][1]) * 100)
            gaps.append(gap)
        gaps.append(0)  # No gap for the last student
        return gaps

    def convert(self, role):
        # Calculate percentage gaps
        overall_gaps = self.calculate_gap(self.app.students_overall)

        # Formatting overall ranking
        overall_ranking = "## Общий рейтинг студентов\nВ скобках указан процент отрыва от следующего студента\n```\n"
        for i, (name, score) in enumerate(self.app.students_overall):
            gap_text = f" ({overall_gaps[i]}%)" if overall_gaps[i] > 0 else ""
            overall_ranking += f"{i + 1}. {name:<10} {round(score)}%{gap_text}\n"
        overall_ranking += "```\n"

        # Formatting tests completed ranking
        total_tests = len(self.app.sorted_tests)
        tests_ranking = f"## Рейтинг по количеству сданных работ (из {total_tests})\n```\n"
        for i, (name, test_count) in enumerate(self.app.students_tests):
            tests_ranking += f"{i + 1}. {name:<10} {test_count}\n"
        tests_ranking += "```\n"

        # Formatting average score ranking
        score_ranking = "## Рейтинг по проценту правильных ответов\n```\n"
        for i, (name, score) in enumerate(self.app.students_scores):
            score_ranking += f"{i + 1}. {name:<10} {round(score)}%\n"
        score_ranking += "```\n"

        # Formatting practical tests
        practical_tests = "## Практические работы:\n```\n" + "\n".join([f"{test}" for i, test in enumerate(self.app.sorted_tests)]) + '\n```\n'

        # Formatting submitted tests
        submitted_tests = "## Сданные работы\n"

        # Сортировка студентов по количеству сданных тестов (по убыванию)
        sorted_students = sorted(self.app.students_data.items(), key=lambda x: len(x[1]["results"]), reverse=True)

        if role == 'mentor':
            # If the role is mentor, show results in separate rows
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
        else:
            # If the role is not mentor, show results in columns
            submitted_tests += "```\n"
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

        # last results
        last_results = "## Последние результаты\n\n```\n"
        for end_time, test_number, student in self.app.last_15_results:
            formatted_time = end_time.strftime("%d.%m, %H:%M")  # Convert datetime to "HH:MM"
            last_results += f"{formatted_time} {test_number} {student}\n"
        last_results += "```"

        # show edited time
        gmt_plus_5 = timezone(timedelta(hours=5))
        formatted_time = datetime.now(gmt_plus_5).strftime("%H:%M:%S")
        title = f"# Результаты практических занятий за последние {self.app.conf.days_of_results} дней"
        title += f'\n\n<div align="right">обновлено: {formatted_time} GMT+5</div>\n\n'
        
        # Concatenating final output
        self.app.content = f"{title}\n{overall_ranking}\n{tests_ranking}\n{score_ranking}\n{practical_tests}\n\n{submitted_tests}\n\n{last_results}"
"""Consistency grading - a pure scoring function, no state or Qt dependency."""


def calculate_consistency_grade(std_dev, valid_percentage):
    """Driver consistency score is calculated using a matrix of the following variables and weights;
      std of lap time - 60% weight
      valid lap per - 40% weight

      resulting matric score then assigned a grade and colour and will be displayed in overview screen

    Ive chosen the following weights impirically based off my own interpretation of sessions in iracing aswell as personal opinion
    """
    if std_dev < 0.1:
        time_score = 100
    elif std_dev < 0.2:
        time_score = 95
    elif std_dev < 0.3:
        time_score = 90
    elif std_dev < 0.5:
        time_score = 85
    elif std_dev < 0.8:
        time_score = 75
    elif std_dev < 1.2:
        time_score = 65
    else:
        time_score = 50

    if valid_percentage >= 100:
        valid_score = 100
    elif valid_percentage >= 90:
        valid_score = 95
    elif valid_percentage >= 80:
        valid_score = 85
    elif valid_percentage >= 70:
        valid_score = 75
    elif valid_percentage >= 60:
        valid_score = 65
    elif valid_percentage >= 50:
        valid_score = 55
    else:
        valid_score = 45

    final_score = (time_score * 0.6) + (valid_score * 0.4)

    if final_score >= 95:
        grade, color = "S+", "#ffd700"
    elif final_score >= 90:
        grade, color = "S", "#c0c0c0"
    elif final_score >= 85:
        grade, color = "A+", "#90EE90"
    elif final_score >= 80:
        grade, color = "A", "#98FB98"
    elif final_score >= 70:
        grade, color = "B", "#87CEEB"
    elif final_score >= 60:
        grade, color = "C", "#FFD580"
    else:
        grade, color = "D", "#FFB6C1"

    return grade, color

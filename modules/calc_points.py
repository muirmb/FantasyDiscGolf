def getPlayerPoints(tourPlayer):
    totalPoints = 0

    # Position after final round
    if tourPlayer[1] == 4:
        if tourPlayer[2] >= 1 & tourPlayer[2] <= 4:
            totalPoints += (100-(tourPlayer[2]-1)*20)
        elif tourPlayer[2] == 5:
            totalPoints += 30
        elif tourPlayer[2] <= 10:
            totalPoints += 20
        elif tourPlayer[2] <= 15:
            totalPoints += 15
        elif tourPlayer[2] <= 20:
            totalPoints += 10
        elif tourPlayer[2] <= 30:
            totalPoints += 5

    # Per-round statistics
    if tourPlayer[3] == 100.0:
        totalPoints += 10
    elif tourPlayer[3] >= 90.0:
        totalPoints += 5
    elif tourPlayer[3] >= 80.0:
        totalPoints += 2

    if tourPlayer[4] == 100.0:
        totalPoints += 20
    elif tourPlayer[4] >= 85.0:
        totalPoints += 15
    elif tourPlayer[4] >= 70.0:
        totalPoints += 10
    elif tourPlayer[4] >= 50.0:
        totalPoints += 5

    if tourPlayer[5] == 100.0:
        totalPoints += 1000
    elif tourPlayer[5] >= 80.0:
        totalPoints += 200
    elif tourPlayer[5] >= 50.0:
        totalPoints += 50
    elif tourPlayer[5] >= 30.0:
        totalPoints += 20
    elif tourPlayer[5] >= 20.0:
        totalPoints += 15
    elif tourPlayer[5] >= 10.0:
        totalPoints += 5

    if tourPlayer[6] == 100.0:
        totalPoints += 100
    elif tourPlayer[6] >= 80.0:
        totalPoints += 50
    elif tourPlayer[6] >= 60.0:
        totalPoints += 40
    elif tourPlayer[6] >= 50.0:
        totalPoints += 30
    elif tourPlayer[6] >= 40.0:
        totalPoints += 20
    elif tourPlayer[6] >= 30.0:
        totalPoints += 10

    if tourPlayer[7] == 100.0:
        totalPoints += 50
    elif tourPlayer[7] >= 80.0:
        totalPoints += 30
    elif tourPlayer[7] >= 60.0:
        totalPoints += 20
    elif tourPlayer[7] >= 50.0:
        totalPoints += 10
    elif tourPlayer[7] >= 40.0:
        totalPoints += 5
    elif tourPlayer[7] >= 30.0:
        totalPoints += 2

    if tourPlayer[8] == 100.0:
        totalPoints += 10
    elif tourPlayer[8] >= 90.0:
        totalPoints += 5
    elif tourPlayer[8] >= 80.0:
        totalPoints += 2

    return totalPoints